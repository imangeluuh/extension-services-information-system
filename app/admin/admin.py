from app.admin import bp
from flask import render_template, url_for, request, redirect, flash, session, current_app
from flask_login import current_user, login_user, login_required, logout_user
from .forms import LoginForm, CollaboratorForm, SpeakerForm, RoleForm
from ..models import Project,  Registration, User, ExtensionProgram, Collaborator, Location, Activity, Speaker, Faculty, Beneficiary, Student, Attendance, Role, Module, RoleAccess, Evaluation, Response
from ..Api.resources import AdminLoginApi
from ..decorators.decorators import requires_module_access
from app import db, cache
from ..store import uploadImage
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from datetime import datetime
import folium
from folium.plugins import MarkerCluster
import os, time
from datetime import timedelta
from collections import defaultdict
from sqlalchemy import func

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

@bp.route('/user-role/<string:id>', methods=['POST'])
@login_required
@requires_module_access('User Management')
# @login_required(role=["Admin"])
def changeUserRole(id):
    user = User.query.filter_by(UserId=id).first()
    form = RoleForm()
    user.RoleId = form.role.data
    print(form.role.data)
    db.session.commit()
    flash('User role is succesfully updated', category='success')
    return redirect(request.referrer)

@bp.route('/beneficiaries')
@login_required
@requires_module_access('User Management')
# @login_required(role=["Admin"])
def beneficiaries():
    users = User.query.filter_by(RoleId=2).all()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path)

@bp.route('/students')
@login_required
@requires_module_access('User Management')
# @login_required(role=["Admin"])
def students():
    users = User.query.filter_by(RoleId=3).all()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path)

@bp.route('/faculty')
@login_required
@requires_module_access('User Management')
# @login_required(role=["Admin"])
def faculty():
    users = User.query.filter(~User.RoleId.in_([2, 3])).all()
    form = RoleForm()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path, form=form)

# @bp.route('/user/<string:id>/role', methods=['POST'])
# @login_required(role=["Admin"])
# def editRole(id):
#     form = RoleForm()
#     user = User.query.filter_by(UserId=id).first()
#     user.RoleId == form.role.data
#     db.session.commit()
#     return redirect(request.referrer)

@bp.route('/beneficiaries/<int:id>')
@login_required
@requires_module_access('User Management')
# @login_required(role=["Admin"])
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
    attendance = [attendance.ActivityId for attendance in Attendance.query.filter_by(UserId=user.User[0].UserId).all()]
    return render_template('admin/view_user.html', user=user, user_projects=user_projects, current_date=current_date, attendance=attendance)

@bp.route('/students/<string:id>')
@login_required
@requires_module_access('User Management')
# @login_required(role=["Admin"])
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
    attendance = [attendance.ActivityId for attendance in Attendance.query.filter_by(UserId=user.User[0].UserId).all()]
    return render_template('admin/view_user.html', user=user, user_projects=user_projects, current_date=current_date, attendance=attendance)

@bp.route('/faculty/<int:id>')
# @login_required(role=["Admin"])
@login_required
@requires_module_access('User Management')
def viewFaculty(id):
    user = Faculty.query.filter_by(FacultyId=id).first()
    current_date = datetime.utcnow().date()
    user_projects = Project.query.filter_by(LeadProponentId=user.User[0].UserId)
    return render_template('admin/view_user.html', user=user, user_projects=user_projects, current_date=current_date)



# @cache.cached(timeout=600, key_prefix='getParticipants')
def getParticipants():
    programs = db.session.query(ExtensionProgram.ExtensionProgramId,
                                ExtensionProgram.Name).\
                filter(ExtensionProgram.IsArchived == False).all()
    
    # Create a list of year for the past 5 years
    years = list(range(datetime.utcnow().year-4, datetime.utcnow().year+1))
    data_for_chart_participants = []
    data_for_chart_projects = []

    # Tuple order: (Number of registration for each project, Registration date's year, Project Id, Extension Program Id, Project start date)
    records = db.session.query(func.count(Registration.RegistrationId),
                           func.extract('year', Registration.RegistrationDate),
                           Project.ExtensionProgramId).\
            join(Project, Registration.ProjectId == Project.ProjectId).\
            filter(func.extract('year', Registration.RegistrationDate) >= datetime.utcnow().year-4).\
            filter(Project.IsArchived == False).\
            group_by(func.extract('year', Registration.RegistrationDate), Project.ExtensionProgramId).\
            order_by(func.extract('year', Registration.RegistrationDate)).all()

    # Create a dictionary for the id and name of extension programs for reference later
    program_dict = {}
    for program in programs:
        program_dict[program[0]] = program[1]

    # Dictionary to hold the number of registration for each program in every year
    data = {}
    project_data = {}
    for year in years:
        data[year] = {}
        project_data[year] = {}
        for program in programs:
            data[year][program[1]] = 0
            project_data[year][program[1]] = 0

    # Update the count of registration based on record's program and registration date's year in data dictionary 
    for record in records:
        # Participants' growth data
        data[int(record[1])][program_dict[record[2]]] = record[0]

    # Update the data list for participants' growth chart
    for key in data:
        temp = {"Year": key}
        temp.update(data[key]) 
        data_for_chart_participants.append(temp)

    records = db.session.query(func.count(Project.ProjectId),
                           func.extract('year', Project.StartDate),
                           Project.ExtensionProgramId).\
            join(ExtensionProgram, Project.ExtensionProgramId == ExtensionProgram.ExtensionProgramId).\
            filter(func.extract('year', Project.StartDate) >= datetime.utcnow().year-4).\
            filter(Project.IsArchived == False).\
            filter(ExtensionProgram.IsArchived == False).\
            group_by(func.extract('year', Project.StartDate), Project.ExtensionProgramId).\
            order_by(func.extract('year', Project.StartDate)).all()
    # print(records)    

    # Update the count of registration based on record's program and registration date's year in data dictionary 
    for record in records:
        # Participants' growth data
        project_data[int(record[1])][program_dict[record[2]]] = record[0]

    # Update the data list for projects' growth chart
    for key in project_data:
        temp = {"Year": key}
        temp.update(project_data[key]) 
        data_for_chart_projects.append(temp)
    # print(data_for_chart_projects
    
# @cache.cached(timeout=600, key_prefix='getEngagement')

    today = datetime.utcnow().date()

    months = []
    for _ in range(5):
        months.append({today.strftime('%Y-%m'):today.strftime('%B')})
        today = today - timedelta(days=today.day)
    months.reverse()
    
    top_projects = db.session.query(Project.Title) \
        .join(Activity, Project.ProjectId == Activity.ProjectId) \
        .join(Attendance, Activity.ActivityId == Attendance.ActivityId) \
        .join(User, Attendance.UserId == User.UserId) \
        .filter(User.RoleId == 2) \
        .filter(Project.IsArchived == False) \
        .filter(Activity.Date >= f'{next(iter(months[0]))}-01') \
        .group_by(Project.Title) \
        .order_by(db.desc(db.func.count(Attendance.AttendanceId))) \
        .limit(5) \
        .all()
    top_projects = [project[0] for project in top_projects]

    # Initialize data dictionary
    data = {}
    for project in top_projects:
        data[project] = {}  # Initialize data dictionary for each project
        for month in months:
            data[project][next(iter(month))] = {
                'month': next(iter(month)),
                'month_name': list(month.values())[0],
                'participants': 0
            }

    records = db.session.query(
            Project.Title,
            func.TO_CHAR(Activity.Date, 'YYYY-MM'),
            func.count(Attendance.AttendanceId)
        ).join(
            Activity, Project.ProjectId == Activity.ProjectId
        ).join(
            Attendance, Activity.ActivityId == Attendance.ActivityId
        ).join(
            User, Attendance.UserId == User.UserId
        ).filter(
            User.RoleId == 2,
            Activity.Date >= f'{next(iter(months[0]))}-01',
            Project.Title.in_(top_projects)
        ).group_by(
            Project.Title,
            func.TO_CHAR(Activity.Date, 'YYYY-MM')
        ).order_by(
            Project.Title
        ).all()

    for record in records:
        project_title, month, participants_count = record
        data[project_title][month]['participants'] = participants_count
    
    top_5_projects = []

    for project, months_data in data.items():
        top_5_projects.append({'name': project, 'data': list(months_data.values())})

    program_data = {}
    for program in programs:
        program_data[program[1]] = {}  # Initialize data dictionary for each project
        for month in months:
            program_data[program[1]][next(iter(month))] = {
                'month': next(iter(month)),
                'month_name': list(month.values())[0],
                'participants': 0
            }

    records = db.session.query(
            ExtensionProgram.Name,
            func.TO_CHAR(Activity.Date, 'YYYY-MM'),
            func.count(Attendance.AttendanceId)
        ).join(
            Project, ExtensionProgram.ExtensionProgramId == Project.ExtensionProgramId
        ).join(
            Activity, Project.ProjectId == Activity.ProjectId
        ).join(
            Attendance, Activity.ActivityId == Attendance.ActivityId
        ).join(
            User, Attendance.UserId == User.UserId
        ).filter(
            User.RoleId == 2,
            Activity.Date >=  f'{next(iter(months[0]))}-01',
            Project.IsArchived == False,
            ExtensionProgram.IsArchived == False
        ).group_by(
            ExtensionProgram.Name,
            func.TO_CHAR(Activity.Date, 'YYYY-MM')
        ).order_by(
            ExtensionProgram.Name
        ).all()

    for record in records:
        program, month, participants_count = record
        program_data[program][month]['participants'] = participants_count
    
    program_engagement = []

    for program, months_data in program_data.items():
        program_engagement.append({'name': program, 'data': list(months_data.values())})


    satisfaction_data = {}
    for program in programs:
        satisfaction_data[program[1]] = {}  # Initialize data dictionary for each program
        for year in years:
            satisfaction_data[program[1]][year] = {
                'year': year,
                'average_rating': 0
            }
    print(satisfaction_data)
    records = db.session.query(
                ExtensionProgram.Name,
                func.extract('year', Activity.Date),
                func.avg(Response.Num)
            ).join(Project, ExtensionProgram.ExtensionProgramId == Project.ExtensionProgramId
            ).join(Activity, Project.ProjectId == Activity.ProjectId
            ).join(Evaluation, Activity.ActivityId == Evaluation.ActivityId
            ).join(Response, Evaluation.EvaluationId == Response.EvaluationId
            ).filter(
                func.extract('year', Activity.Date) >= datetime.utcnow().year-4,
                Project.IsArchived == False,
                ExtensionProgram.IsArchived == False,
                Evaluation.EvaluationType == 'Satisfaction',
                Response.Num != None
            ).group_by(
                ExtensionProgram.Name,
                func.extract('year', Activity.Date)
            ).order_by(
                ExtensionProgram.Name
            ).all()
    
    for record in records:
        program, year, average_rating = record
        satisfaction_data[program][year]['average_rating'] = float(round(average_rating, 2))

    data_for_bar_graph = []

    for program, years_data in satisfaction_data.items():
        data_for_bar_graph.append({'name': program, 'data': list(years_data.values())})

    # for extension_program in ExtensionProgram.query.all():
    #     print("extension_program:", extension_program)
    #     program_ratings = []
    #     for project in extension_program.Projects:
    #         for activity in project.Activity:
    #             if activity.Evaluation:
    #                 for evaluation in activity.Evaluation:
    #                     # Check if the evaluation type is for satisfaction
    #                     if evaluation.EvaluationType == "Satisfaction":
    #                         for response in evaluation.Response:
    #                             rating = response.Num
    #                             if rating is not None:
    #                                 program_ratings.append({"year": activity.Date.year, "rating": rating})
        
    #     if program_ratings:
    #         # Calculate the average rating for the extension program
    #         non_none_ratings = [entry["rating"] for entry in program_ratings if entry["rating"] is not None]
    #         average_rating = sum(non_none_ratings) / len(non_none_ratings) if non_none_ratings else None
    #         data_for_bar_graph.append({"name": extension_program.Name, "data": program_ratings, "average_rating": average_rating})

    print('data_for_bar', data_for_bar_graph)

    return [data_for_chart_participants, data_for_chart_projects, data_for_bar_graph, top_5_projects, program_engagement]

@bp.route('/dashboard')
@login_required
@requires_module_access('Dashboard')
# @login_required(role=["Admin", "Faculty"])
def dashboard():
    start_time = time.time()
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

    # # Sort years in chronological order
    sorted_years = sorted(set(entry["year"] for program_data in data_for_bar_graph for entry in program_data["data"]))

    last_5_months_projects_engagement = participants[3]
    last_5_months_programs_engagement = participants[4]
    end_time = time.time()
    processing_time = end_time - start_time
    print('processing time', processing_time)
    return render_template('admin/dashboard.html',
                            data_for_chart_participants=data_for_chart_participants,
                            data_for_chart_projects=data_for_chart_projects,
                            data_for_bar_graph=data_for_bar_graph,
                            sorted_years=sorted_years,
                            # # upcoming_projects=upcoming_projects,
                            # # ongoing_projects=ongoing_projects,
                            # # completed_projects=completed_projects,
                            # # upcoming_activities=upcoming_activities,
                            # # ongoing_activities=ongoing_activities,
                            # # completed_activities=completed_activities,
                            last_5_months_projects_engagement=last_5_months_projects_engagement,
                            last_5_months_programs_engagement=last_5_months_programs_engagement
                            )

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
@login_required
@requires_module_access('Agency Partner Management')
# @login_required(role=["Admin"])
def collaborators():
    form = CollaboratorForm()
    collaborators = Collaborator.query.all()
    return render_template('admin/collaborators.html', collaborators=collaborators, form=form)

@bp.route('/collaborators/create', methods=['POST'])
@login_required
@requires_module_access('Agency Partner Management')
# @login_required(role=["Admin"])
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
@login_required
@requires_module_access('Agency Partner Management')
# @login_required(role=["Admin"])
def viewCollaborator(id):
    collaborator = Collaborator.query.filter_by(CollaboratorId=id).first()
    current_date = datetime.utcnow().date()
    return render_template('admin/view_collaborator.html', collaborator=collaborator, current_date=current_date)

@bp.route('/collaborators/update/<int:id>', methods=['POST'])
@login_required
@requires_module_access('Agency Partner Management')
# @login_required(role=["Admin"])
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
@login_required
@requires_module_access('Agency Partner Management')
# @login_required(role=["Admin"])
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


@bp.route('/access-management')
@login_required
@requires_module_access('Access Management')
def accessManagement():
    roles = Role.query.all()
    modules = Module.query.all()
    return render_template('admin/access_management.html', roles=roles, modules=modules)

@bp.route('/add-role', methods=['POST'])
@login_required
@requires_module_access('Access Management')
def addRole():
    role_to_add = Role(RoleName=request.form.get('role'))
    db.session.add(role_to_add)
    db.session.flush()

    role_id = role_to_add.RoleId

    for module_id in request.form.getlist('module'):
        access_to_add = RoleAccess(RoleId=role_id,
                                ModuleId=int(module_id))
        db.session.add(access_to_add)

    db.session.commit()
    return redirect(request.referrer)

@bp.route('/edit-role/<int:id>', methods=['POST'])
@login_required
@requires_module_access('Access Management')
def editRole(id):
    role = Role.query.filter_by(RoleId=id).first()
    
    role.RoleName = request.form.get('role')

    selected_values = request.form.getlist('module')

    for access in role.RoleAccess:
        bool_is_removed = True
        if str(access.ModuleId) in selected_values:
            selected_values.remove(str(access.ModuleId))
            bool_is_removed = False
        if bool_is_removed:
            db.session.delete(access)
    if len(selected_values) != 0:
        for module_id in selected_values:
            access_to_add = RoleAccess(RoleId=role.RoleId,
                                    ModuleId=int(module_id))
            db.session.add(access_to_add)

    db.session.commit()
    flash('Role access is successfully updated', category='success')
    return redirect(request.referrer)

@bp.route('/delete-role/<int:id>', methods=['POST'])
@login_required
@requires_module_access('Access Management')
def deleteRole(id):
    role = Role.query.filter_by(RoleId=id).first()
    db.session.delete(role)
    db.session.commit()
    flash('Role is successfully deleted', category='success')
    return redirect(request.referrer)

# ==================================================
@bp.route('/speakers')
@login_required
# @login_required(role=["Admin"])
def speakers():
    form = SpeakerForm()
    speakers = Speaker.query.all()
    return render_template('admin/speakers.html', speakers=speakers, form=form)

@bp.route('/speakers/create', methods=['POST'])
@login_required
# @login_required(role=["Admin"])
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
@login_required
# @login_required(role=["Admin"])
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
# @login_required(role=["Admin"])
@login_required
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