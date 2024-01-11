from app.admin import bp
from flask import render_template, url_for, request, redirect, flash, session, current_app
from flask_login import current_user, login_user, login_required, logout_user
from .forms import LoginForm, CollaboratorForm, SpeakerForm
from ..models import Project,  Registration, User, ExtensionProgram, Collaborator, Location, Activity, Speaker
from ..Api.resources import AdminLoginApi
from ..decorators.decorators import login_required
from app import db, api
from ..store import uploadImage
from werkzeug.utils import secure_filename
import folium
from folium.plugins import MarkerCluster
import os



def saveImage(image, imagepath):
    imagename = secure_filename(image.filename)
    image.save(imagepath)
    # Upload image to imagekit
    return uploadImage(imagepath, imagename)

@bp.route('/', methods=['GET', 'POST'])
def adminLogin():
    form = LoginForm()
    
    # Prevents logged in users from accessing the page
    if current_user.is_authenticated:
        return redirect(url_for('programs.programs')) 
    if request.method == "POST":
        if form.validate_on_submit():
            attempted_user = User.query.filter_by(Email=form.email.data).first()
            if attempted_user and attempted_user.RoleId == 1: 
                if attempted_user.check_password_correction(attempted_password=form.password.data):
                    login_user(attempted_user, remember=True)
                    return redirect(url_for('admin.dashboard')) 
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
    users = User.query.filter_by(RoleId=2).all()
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

@bp.route('/beneficiaries/<string:id>')
@login_required(role=["Admin"])
def viewUser(id):
    user = User.query.filter_by(UserNumber=id).first()
    if user.Role.RoleName in ["Beneficiary", "Student"]:
        user_projects = (
        Project.query
        .join(Registration, Registration.ProjectId == Project.ProjectId)
        .join(User, User.UserId == Registration.UserId)
        .filter(User.UserId == user.UserId)
        .all()
        )
    else:
        user_projects = Project.query.filter_by(LeadProponentId=user.UserId)
    return render_template('admin/view_user.html', user=user, user_projects=user_projects)
    
@bp.route('/dashboard')
@login_required(role=["Admin"])
def dashboard():
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
            year_exists = any(entry["year"] == year for entry in program_data["data"])

            if not year_exists:
                program_data["data"].append({"year": year, "participants": 0})
                program_projects_data["data"].append({"year": year, "projects": 0})

            for data in program_data["data"]:
                if data["year"] == year:
                    data["participants"] += len(registered)

            for data in program_projects_data["data"]:
                if data["year"] == year:
                    data["projects"] += 1

        programs_participants[program.Name] = program_data
        programs_projects[program.Name] = program_projects_data

    years = sorted(list(years))
    data_for_chart_participants = [{"Year": year} for year in years]
    data_for_chart_projects = [{"Year": year} for year in years]

    for program_name, program_data in programs_participants.items():
        for data in program_data["data"]:
            for chart_data in data_for_chart_participants:
                if chart_data["Year"] == data["year"]:
                    chart_data[program_name] = data["participants"]
                else:
                    chart_data[program_name] = 0

    for program_name, program_data in programs_projects.items():
        for data in program_data["data"]:
            for chart_data in data_for_chart_projects:
                if chart_data["Year"] == data["year"]:
                    chart_data[program_name] = data["projects"]
                else:
                    chart_data[program_name] = 0

    for extension_program in ExtensionProgram.query.all():
        print("extension_program:", extension_program)
        program_ratings = []
        for project in extension_program.Projects:
            for activity in project.Activity:
                if activity.Evaluation:
                    for evaluation in activity.Evaluation:
                        for response in evaluation.Response:
                            rating = response.Num
                            if rating is not None:
                                program_ratings.append({"year": activity.Date.year, "rating": rating})
        
        if program_ratings:
            # Calculate the average rating for the extension program
            non_none_ratings = [entry["rating"] for entry in program_ratings if entry["rating"] is not None]
            average_rating = sum(non_none_ratings) / len(non_none_ratings) if non_none_ratings else None
            data_for_bar_graph.append({"name": extension_program.Name, "data": program_ratings, "average_rating": average_rating})

    # Sort years in chronological order
    sorted_years = sorted(set(entry["year"] for program_data in data_for_bar_graph for entry in program_data["data"]))

    # Debug information
    print("programs_participants:", programs_participants)
    print("data_for_chart_participants:", data_for_chart_participants)
    print("programs_projects:", programs_projects)
    print("data_for_chart_projects:", data_for_chart_projects)
    print("data_for_bar_graph:", data_for_bar_graph)

    with current_app.app_context():
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
        folium.TileLayer('openstreetmap').add_to(mapObj)
        folium.TileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                        name='CartoDB.DarkMatter', attr="CartoDB.DarkMatter").add_to(mapObj)

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

    return render_template('admin/dashboard.html',
                            data_for_chart_participants=data_for_chart_participants,
                            data_for_chart_projects=data_for_chart_projects,
                            data_for_bar_graph=data_for_bar_graph,
                            sorted_years=sorted_years)

    
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
            flash(f"Field '{field}' has an error: {error}")
    return redirect(url_for('admin.collaborators'))

@bp.route('/collaborators/<int:id>')
@login_required(role=["Admin"])
def viewCollaborator(id):
    collaborator = Collaborator.query.filter_by(CollaboratorId=id).first()
    return render_template('admin/view_collaborator.html', collaborator=collaborator)

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
            flash('Collaborator is successfully update', category='success')
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

