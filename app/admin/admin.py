from app.admin import bp
from flask import render_template, url_for, request, redirect, flash, session, current_app
from flask_login import current_user, login_user, login_required, logout_user
from .forms import LoginForm, CollaboratorForm, SpeakerForm
from ..models import Project,  Registration, User, ExtensionProgram, Collaborator, Location, Activity, Speaker, Faculty, Beneficiary, Student
from ..Api.resources import AdminLoginApi
from ..decorators.decorators import login_required
from app import db, cache
from ..store import uploadImage
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from datetime import datetime
import folium
from folium.plugins import MarkerCluster
import os
from datetime import timedelta

def saveImage(image, imagepath):
    imagename = secure_filename(image.filename)
    image.save(imagepath)
    # Upload image to imagekit
    return uploadImage(imagepath, imagename)


# @cache.cached(timeout=600, key_prefix='getStatusCount')
# def getStatusCount():
#     current_date = datetime.utcnow().date()

#     upcoming_projects = Project.query.filter(Project.StartDate > current_date).count()
#     ongoing_projects = Project.query.filter(Project.StartDate <= current_date, Project.EndDate >= current_date).count()
#     completed_projects = Project.query.filter(Project.EndDate < current_date).count()

#     upcoming_activities = Activity.query.filter(Activity.Date > current_date).count()
#     ongoing_activities = Activity.query.filter(Activity.Date <= current_date, Activity.Date >= current_date).count()
#     completed_activities = Activity.query.filter(Activity.Date < current_date).count()

#     return [upcoming_projects, ongoing_projects, completed_projects, upcoming_activities, ongoing_activities, completed_activities]

@cache.cached(timeout=600, key_prefix='getParticipants')
def getParticipants():
    programs = ExtensionProgram.query.all()
    years = set()
    programs_participants = {}
    programs_projects = {}
    data_for_bar_graph = []
    for program in programs:
        program_data = {"name": program.Name, "data": []}
        program_projects_data = {"name": program.Name, "data": []}

        for project in program.Projects:
            registered = project.Registration
            end_date = project.EndDate

            # Extracting the year from the EndDate
            year = end_date.year
            years.add(year)

            # Update the participants count for the corresponding year
            year_exists_participants = any(entry["year"] == year for entry in program_data["data"])
            year_exists_projects = any(entry["year"] == year for entry in program_projects_data["data"])

            if not year_exists_participants:
                program_data["data"].append({"year": year, "participants": 0})
            if not year_exists_projects:
                program_projects_data["data"].append({"year": year, "projects": 0})

            for data in program_data["data"]:
                if data["year"] == year:
                    data["participants"] += len(registered)

            for data in program_projects_data["data"]:
                if data["year"] == year:
                    data["projects"] += 1

        programs_participants[program.Name] = program_data
        programs_projects[program.Name] = program_projects_data

    for program_name, program_data in programs_participants.items():
        for year in years:
            year_exists = any(entry["year"] == year for entry in program_data["data"])
            if not year_exists:
                program_data["data"].append({"year": year, "participants": 0})

    for program_name, program_data in programs_projects.items():
        for year in years:
            year_exists = any(entry["year"] == year for entry in program_data["data"])
            if not year_exists:
                program_data["data"].append({"year": year, "projects": 0})

    years = sorted(list(years))

    data_for_chart_participants = [{"Year": year} for year in years]
    data_for_chart_projects = [{"Year": year} for year in years]

    # Populate data for chart
    for program_name, program_data in programs_participants.items():
        for data in program_data["data"]:
            for chart_data in data_for_chart_participants:
                if chart_data["Year"] == data["year"]:
                    chart_data[program_name] = data["participants"]

    for program_name, program_data in programs_projects.items():
        for data in program_data["data"]:
            for chart_data in data_for_chart_projects:
                if chart_data["Year"] == data["year"]:
                    chart_data[program_name] = data["projects"]

    for extension_program in ExtensionProgram.query.all():
        print("extension_program:", extension_program)
        program_ratings = []
        for project in extension_program.Projects:
            for activity in project.Activity:
                if activity.Evaluation:
                    for evaluation in activity.Evaluation:
                        # Check if the evaluation type is for satisfaction
                        if evaluation.EvaluationType == "Satisfaction":
                            for response in evaluation.Response:
                                rating = response.Num
                                if rating is not None:
                                    program_ratings.append({"year": activity.Date.year, "rating": rating})
        
        if program_ratings:
            # Calculate the average rating for the extension program
            non_none_ratings = [entry["rating"] for entry in program_ratings if entry["rating"] is not None]
            average_rating = sum(non_none_ratings) / len(non_none_ratings) if non_none_ratings else None
            data_for_bar_graph.append({"name": extension_program.Name, "data": program_ratings, "average_rating": average_rating})

    return [data_for_chart_participants, data_for_chart_projects, data_for_bar_graph]

@cache.cached(timeout=600, key_prefix='getEngagement')
def getEngagement():
    current_date = datetime.utcnow().date()
    last_5_months = [
        {
            "date": (current_date - timedelta(days=30 * i)).strftime('%Y-%m'),
            "month_name": (current_date - timedelta(days=30 * i)).strftime('%B')
        } for i in range(4, -1, -1)
    ]

    last_5_months_projects_engagement = []
    last_5_months_programs_engagement = []

    for project in Project.query.all():
        engagement_data = {
            "name": project.Title,
            "data": []
        }

        for month in last_5_months:
            participants_count = project.get_participants_count_for_month(month)
            engagement_data["data"].append({"month": month["date"], "month_name": month["month_name"], "participants": participants_count})

        last_5_months_projects_engagement.append(engagement_data)

    for program in ExtensionProgram.query.all():
        engagement_data = {
            "name": program.Name,
            "data": []
        }

        for month in last_5_months:
            participants_count = program.get_participants_count_for_month(month)
            engagement_data["data"].append({"month": month["date"], "month_name": month["month_name"], "participants": participants_count})

        last_5_months_programs_engagement.append(engagement_data)

    # Sort projects based on the participants count for the last month
    last_5_months_projects_engagement.sort(key=lambda x: x['data'][-1]['participants'], reverse=True)

    # Select the top 5 projects
    last_5_months_projects_engagement = last_5_months_projects_engagement[:5]
    return [last_5_months_projects_engagement, last_5_months_programs_engagement]


@bp.route('/', methods=['GET', 'POST'])
def adminLogin():
    form = LoginForm()
    
    # Prevents logged in users from accessing the page
    if current_user.is_authenticated:
        return redirect(url_for('programs.programs')) 
    if request.method == "POST":
        if form.validate_on_submit():
            attempted_user = Faculty.query.filter_by(Email=form.email.data).first()
            if attempted_user and attempted_user.User[0].RoleId == 1: 
                if check_password_hash(attempted_user.Password, form.password.data):
                    login_user(attempted_user.User[0], remember=True)
                    return redirect(url_for('programs.programs')) 
                else:
                    flash('The password you\'ve entered is incorrect.', category='error')
            else:
                flash('The email you entered isn\'t connected to an account.', category='error')
    return render_template('auth/admin_login.html', form=form)

@bp.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('admin.adminLogin'))

@bp.route('/beneficiaries')
@login_required(role=["Admin"])
def beneficiaries():
    users = Beneficiary.query.all()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path)

@bp.route('/students')
@login_required(role=["Admin"])
def students():
    users = User.query.filter_by(RoleId=3).all()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path)

@bp.route('/faculty')
@login_required(role=["Admin"])
def faculty():
    users = User.query.filter_by(RoleId=4).all()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path)

@bp.route('/beneficiaries/<int:id>')
@login_required(role=["Admin"])
def viewBeneficiary(id):
    user = Beneficiary.query.filter_by(BeneficiaryId=id).first()
    user_projects = (
    Project.query
    .join(Registration, Registration.ProjectId == Project.ProjectId)
    .join(User, User.UserId == Registration.UserId)
    .filter(User.UserId == user.User[0].UserId)
    .all()
    )
    current_date = datetime.utcnow().date()
    return render_template('admin/view_user.html', user=user, user_projects=user_projects, current_date=current_date)

@bp.route('/students/<string:id>')
@login_required(role=["Admin"])
def viewStudent(id):
    user = Student.query.filter_by(StudentNumber=id).first()
    user_projects = (
    Project.query
    .join(Registration, Registration.ProjectId == Project.ProjectId)
    .join(User, User.UserId == Registration.UserId)
    .filter(User.UserId == user.User[0].UserId)
    .all()
    )
    current_date = datetime.utcnow().date()
    return render_template('admin/view_user.html', user=user, user_projects=user_projects, current_date=current_date)

@bp.route('/faculty/<int:id>')
@login_required(role=["Admin"])
def viewFaculty(id):
    user = Faculty.query.filter_by(FacultyId=id).first()
    current_date = datetime.utcnow().date()
    user_projects = Project.query.filter_by(LeadProponentId=user.User[0].UserId)
    return render_template('admin/view_user.html', user=user, user_projects=user_projects, current_date=current_date)

@bp.route('/dashboard')
@login_required(role=["Admin", "Faculty"])
def dashboard():
    # statusCount = getStatusCount()
    # upcoming_projects = statusCount[0]
    # ongoing_projects = statusCount[1]
    # completed_projects = statusCount[2]

    # upcoming_activities = statusCount[3]
    # ongoing_activities = statusCount[4]
    # completed_activities = statusCount[5]

    participants = getParticipants()

    data_for_chart_participants = participants[0]
    data_for_chart_projects = participants[1]
    data_for_bar_graph = participants[2]

    # Sort years in chronological order
    sorted_years = sorted(set(entry["year"] for program_data in data_for_bar_graph for entry in program_data["data"]))

    engagement = getEngagement()
    last_5_months_projects_engagement = engagement[0]
    last_5_months_programs_engagement = engagement[1]

    return render_template('admin/dashboard.html',
                            data_for_chart_participants=data_for_chart_participants,
                            data_for_chart_projects=data_for_chart_projects,
                            data_for_bar_graph=data_for_bar_graph,
                            sorted_years=sorted_years,
                            # upcoming_projects=upcoming_projects,
                            # ongoing_projects=ongoing_projects,
                            # completed_projects=completed_projects,
                            # upcoming_activities=upcoming_activities,
                            # ongoing_activities=ongoing_activities,
                            # completed_activities=completed_activities,
                            last_5_months_projects_engagement=last_5_months_projects_engagement,
                            last_5_months_programs_engagement=last_5_months_programs_engagement)

@bp.route('/qcmap')
def qcmap():
    programs = ExtensionProgram.query.all()
    # Query the Activity table to get the location count
    location_counts = db.session.query(Location.LocationName, db.func.count(Activity.LocationId)). \
        join(Activity, Location.LocationId == Activity.LocationId). \
        group_by(Location.LocationName).all()

    # Fetch longitude and latitude from the Location table
    locations = db.session.query(Location).all()

    # Update the bubble_data list
    bubble_data = []
    for location in locations:
        location_name = location.LocationName
        longitude = location.Longitude
        latitude = location.Latitude

        # Find the corresponding location count
        count = next((count for name, count in location_counts if name == location_name), 0)

        # Display bubble marker only if activities are done in this location
        if count > 0:
            bubble_data.append((float(latitude), float(longitude), count))

    # Initialize a map with center and zoom
    mapObj = folium.Map(location=[14.7011253, 121.0721637], zoom_start=15, tiles=None)

    # Add tile layers
    folium.TileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                    name='CartoDB.DarkMatter', attr="CartoDB.DarkMatter").add_to(mapObj)
    folium.TileLayer('openstreetmap').add_to(mapObj)

    marker_cluster = MarkerCluster().add_to(mapObj)

    # Add dynamic bubble markers
    for bubble in bubble_data:
        latitude, longitude, program_count = bubble
        location_name = next((name for name, in db.session.query(Location.LocationName).filter_by(Latitude=str(latitude), Longitude=str(longitude)).all()), '')

        size_multiplier = 5
        bubble_size = program_count * size_multiplier

        folium.CircleMarker(
            location=[latitude, longitude],
            radius=bubble_size,
            popup=folium.Popup(f'Location: {location_name}<br>Projects: {program_count}', max_width=300),
            fill=True,
            fill_opacity=0.7
        ).add_to(marker_cluster)

    # Add layers control over the map
    folium.LayerControl().add_to(mapObj)

    # Save the map as an HTML file
    mapObj.save('app/templates/admin/qcmap.html')

    return render_template('admin/qcmap.html')

    
@bp.route('/collaborators')
@login_required(role=["Admin"])
def collaborators():
    form = CollaboratorForm()
    collaborators = Collaborator.query.all()
    return render_template('admin/collaborators.html', collaborators=collaborators, form=form)

@bp.route('/collaborators/create', methods=['POST'])
@login_required(role=["Admin"])
def createCollaborator():
    form = CollaboratorForm()
    if form.validate_on_submit():
        try:
            str_moa_url = None
            str_moa_file_id = None
            # Get the project proposal path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.signed_moa.data.filename)
                )
            # Save project proposal to local and upload to cloud 
            status = saveImage(form.signed_moa.data, imagepath)
            if status.error is not None:
                flash("Signed MOU/MOA upload failed", category="error")
                return redirect(url_for(request.referrer))
            else:
                str_moa_url = status.url
                str_moa_file_id = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)
            collaborator_to_add = Collaborator(Organization=form.organization.data
                                                , Location=form.location.data
                                                , SignedMOAUrl=str_moa_url
                                                , SignedMOAFileId=str_moa_file_id)
            db.session.add(collaborator_to_add)
            db.session.commit()
            flash('Collaborator is successfully inserted', category='success')
        except:
            flash('There was an error creating new collaborator', category='error')
    if form.errors != {}: # If there are errors from the validations
        for field, error in form.errors.items():
            flash(f"Field '{field}' has an error: {error}", category='error')
    return redirect(url_for('admin.collaborators'))

@bp.route('/collaborators/<int:id>')
@login_required(role=["Admin"])
def viewCollaborator(id):
    collaborator = Collaborator.query.filter_by(CollaboratorId=id).first()
    current_date = datetime.utcnow().date()
    return render_template('admin/view_collaborator.html', collaborator=collaborator, current_date=current_date)

@bp.route('/collaborators/update/<int:id>', methods=['POST'])
@login_required(role=["Admin"])
def updateCollaborator(id):
    form = CollaboratorForm()
    if form.validate_on_submit():
        collaborator = Collaborator.query.filter_by(CollaboratorId=id).first()
        try:
            collaborator.Organization = form.organization.data
            collaborator.Location = form.location.data
            if form.signed_moa.data:
                str_moa_url = None
                str_moa_file_id = None
                # Get the project proposal path
                imagepath = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], secure_filename(form.signed_moa.data.filename)
                    )
                # Save project proposal to local and upload to cloud 
                status = saveImage(form.signed_moa.data, imagepath)
                if status.error is not None:
                    flash("Signed MOU/MOA upload failed", category="error")
                    return redirect(url_for(request.referrer))
                else:
                    str_moa_url = status.url
                    str_moa_file_id = status.file_id
                # Delete file from local storage
                if os.path.exists(imagepath):
                    os.remove(imagepath)

                collaborator.SignedMOAUrl = str_moa_url
                collaborator.SignedMOAFileId = str_moa_file_id
            db.session.commit()
            flash('Collaborator is successfully updated', category='success')
        except Exception as e:
            print(e)
            flash('There was an issue updating collaborator', category='error')
    
    return redirect(request.referrer)

@bp.route('/collaborators/delete/<int:id>', methods=['POST'])
@login_required(role=["Admin"])
def deleteCollaborator(id):
    collaborator = Collaborator.query.filter_by(CollaboratorId=id).first()
    try:
        db.session.delete(collaborator)
        db.session.commit()
        flash('Collaborator is successfully deleted.', category='success')
    except Exception as e:
        print(e)
        flash('There was an issue deleting the extension program.', category='error')

    return redirect(request.referrer)

@bp.route('/speakers')
@login_required(role=["Admin"])
def speakers():
    form = SpeakerForm()
    speakers = Speaker.query.all()
    return render_template('admin/speakers.html', speakers=speakers, form=form)

@bp.route('/speakers/create', methods=['POST'])
@login_required(role=["Admin"])
def createSpeaker():
    form = SpeakerForm()
    if form.validate_on_submit():
        try:
            speaker_to_add = Speaker(FirstName = form.first_name.data,
                                        MiddleName = form.middle_name.data if form.middle_name.data else None,
                                        LastName = form.last_name.data,
                                        Email = form.email.data,
                                        ContactDetails = form.contact_details.data)
            db.session.add(speaker_to_add)
            db.session.commit()
            flash('Speaker is successfully inserted', category='success')
        except:
            flash('There was an error creating a new speaker', category='error')
    if form.errors != {}: # If there are errors from the validations
        for field, error in form.errors.items():
            print(f"Field '{field}' has an error: {error}")
            flash(f"Field '{field}' has an error: {error}", category='error')
    return redirect(url_for('admin.speakers'))

@bp.route('/spakers/update/<int:id>', methods=['POST'])
@login_required(role=["Admin"])
def updateSpeaker(id):
    form = SpeakerForm()
    if form.validate_on_submit():
        speaker = Speaker.query.filter_by(SpeakerId=id).first()
        try:
            speaker.FirstName = form.first_name.data,
            speaker.MiddleName = form.middle_name.data if form.middle_name.data else None,
            speaker.LastName = form.last_name.data,
            speaker.Email = form.email.data,
            speaker.ContactDetails = form.contact_details.data
            db.session.commit()
            flash('Speaker is successfully updated', category='success')
        except Exception as e:
            print(e)
            flash('There was an issue updating speaker', category='error')
    
    return redirect(request.referrer)

@bp.route('/speakers/delete/<int:id>', methods=['POST'])
@login_required(role=["Admin"])
def deleteSpeaker(id):
    speaker = Speaker.query.filter_by(SpeakerId=id).first()
    try:
        db.session.delete(speaker)
        db.session.commit()
        flash('Speaker is successfully deleted.', category='success')
    except Exception as e:
        print(e)
        flash('There was an issue deleting the extension program.', category='error')

    return redirect(request.referrer)