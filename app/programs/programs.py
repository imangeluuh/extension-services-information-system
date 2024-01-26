from app.programs import bp
from flask import render_template, url_for, request, redirect, flash, current_app
from flask_login import current_user
from ..models import Project, ExtensionProgram, Registration, Agenda, ExtensionProgram, Activity, Response, User, Certificate, Budget, Item, Attendance, Course, Faculty, Speaker
from .forms import ProgramForm, ProjectForm, ActivityForm, CombinedForm, ItemForm
import calendar
from datetime import datetime
from app import db, cache
from ..store import uploadImage, purgeImage
from werkzeug.utils import secure_filename
import os, requests
from ..decorators.decorators import login_required, role_excluded
from ..Api.resources import ExtensionProgramListApi
from sqlalchemy import func
from fillpdf import fillpdfs
from dotenv import load_dotenv
from pathlib import Path
import os, folium
from folium.plugins import MarkerCluster
from ..email import certificate

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# ============== Admin/Faculty views ===========================


# Function to add project team input to dictionary
def getProjectTeamInput(selected_values, choices):
    project_team ={}
    for choice in choices:
        if choice[0] in selected_values:
            project_team[choice[0]] = choice[1]
    return project_team

# Function to save image/file to local and upload it to cloud
def saveImage(image, imagepath):
    imagename = secure_filename(image.filename)
    image.save(imagepath)
    # Upload image to imagekit
    return uploadImage(imagepath, imagename)


# def getResearchData():
#     headers = {
#         'Content-Type': 'application/json'  # Adjust content type as needed
#     }
#     token_response = requests.get(os.getenv('RIS_AUTH_API'), headers=headers)
#     data = token_response.json()

#     # Set up headers with the API key in the 'API Key' authorization header
#     headers = {
#         'Authorization': f"Bearer {data['result']['access_token']}",  
#         'Content-Type': 'application/json'  # Adjust content type as needed
#     }
#     url = os.getenv('RIS_FOR_API')

#     response = requests.get(url, headers=headers)
#     print(response.json())

# @cache.cached(timeout=1800, key_prefix='getPrograms')
def getPrograms():
    return ExtensionProgram.query.all()

@bp.route('/pupqc/extension-programs')
@login_required(role=["Admin", "Faculty"])
def programs():
    form = ProgramForm()
    project_form = ProjectForm()
    programs = getPrograms()    
    
    return render_template('programs/program_management.html', programs=programs, form=form, project_form=project_form)

@bp.route('/extension-program/<int:id>', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def viewExtensionProgram(id):
    ext_program_form = ProgramForm()
    form = ProjectForm()
    ext_program = ExtensionProgram.query.filter_by(ExtensionProgramId=id).first()

    # fill the edit form with extension program details
    ext_program_form.program_name.data = ext_program.Name
    ext_program_form.rationale.data = ext_program.Rationale

    return render_template('programs/view_ext_program.html', ext_program=ext_program, ext_program_form=ext_program_form, form=form)

@bp.route('/extension-program/insert', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def insertExtensionProgram():
    form = CombinedForm()
    if request.method == 'POST':
        str_image_url = None
        str_image_file_id = None
        if form.extension_program.image.data is not None:
            # Get the input image path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.extension_program.image.data.filename)
                )
            # Save image
            status = saveImage(form.extension_program.image.data, imagepath)
            if status.error is not None:
                flash("Extension program image upload failed", category="error")
                return redirect(request.referrer)
            else:
                str_image_url = status.url
                str_image_file_id = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)
        program_to_add = ExtensionProgram(Name = form.extension_program.program_name.data,
                                        Rationale = form.extension_program.rationale.data,
                                        AgendaId = form.extension_program.agenda.data,
                                        ProgramId = form.extension_program.program.data,
                                        ImageUrl=str_image_url,
                                        ImageFileId=str_image_file_id)
        db.session.add(program_to_add)
        db.session.flush()
        int_program_id = program_to_add.ExtensionProgramId

        # Insert project
        str_image_url = None
        str_image_file_id = None
        if form.project.image.data is not None:
            # Get the input image path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.project.image.data.filename)
                )
            # Save image
            status = saveImage(form.project.image.data, imagepath)
            if status.error is not None:
                flash("Project image upload failed", category="error")
                return redirect(request.referrer)
            else:
                str_image_url = status.url
                str_image_file_id = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

        str_proposal_url = None
        str_proposal_file_id = None

        # Get the project proposal path
        imagepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"], secure_filename(form.project.project_proposal.data.filename)
            )
        
        # Save project proposal to local and upload to cloud 
        status = saveImage(form.project.project_proposal.data, imagepath)
        
        if status.error is not None:
            flash("Project proposal upload failed", category="error")
            return redirect(request.referrer)
        else:
            str_proposal_url = status.url
            str_proposal_file_id = status.file_id
        # Delete file from local storage
        if os.path.exists(imagepath):
            os.remove(imagepath)
     
        project_team = getProjectTeamInput(form.project.project_team.data, form.project.project_team.choices)
        project_to_add = Project(Title = form.project.title.data,
                                Implementer = form.project.implementer.data,
                                LeadProponentId = current_user.UserId,
                                CollaboratorId = form.project.collaborator.data,
                                ProjectTeam = project_team,
                                TargetGroup = form.project.target_group.data,
                                ProjectType = form.project.project_type.data,
                                StartDate = form.project.start_date.data,
                                EndDate = form.project.end_date.data,
                                ImpactStatement = form.project.impact_statement.data,
                                Objectives = form.project.objectives.data,
                                ResearchBased = form.project.research_based.data if form.project.research_based.data else False,
                                ResearchId = form.project.research_title.data if form.project.research_based.data and form.project.research_title.data else None,
                                ImageUrl=str_image_url,
                                ImageFileId=str_image_file_id,
                                ProjectProposalUrl = str_proposal_url,
                                ProjectProposalFileId = str_proposal_file_id,
                                ExtensionProgramId = int_program_id)
        db.session.add(project_to_add)
        
        # Get the id of the recently added project
        db.session.flush()
        int_project_id = project_to_add.ProjectId

        # Add budget of the project
        approved_budgets = request.form.getlist('approved_budget')
        fund_types = request.form.getlist('fund_type')
        budget_data = zip(approved_budgets, fund_types)
        for approved_budget, fund_type in budget_data:
            budget_to_add = Budget(FundType=fund_type,
                                    Amount=approved_budget,
                                    ProjectId=int_project_id,
                                    CollaboratorId=form.project.collaborator.data if fund_type=='External' else None)
            db.session.add(budget_to_add)

        # Insert Activity
        str_image_url = None
        str_image_file_id = None
        if form.activity.image.data is not None:
            # Get the input image path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.activity.image.data.filename)
                )
            # Save image
            status = saveImage(form.activity.image.data, imagepath)
            if status.error is not None:
                flash("Activity image upload failed", category="error")
                return redirect(request.referrer)
            else:
                str_image_url = status.url
                str_image_file_id = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)
                
        activity_to_create = Activity(ActivityName=form.activity.activity_name.data,
                                        Date=form.activity.date.data,
                                        StartTime=form.activity.start_time.data,
                                        EndTime=form.activity.end_time.data,
                                        Description=form.activity.activity_description.data,
                                        LocationId=form.activity.location.data,
                                        ProjectId= int_project_id,
                                        ImageUrl=str_image_url,
                                        ImageFileId=str_image_file_id)
        db.session.add(activity_to_create)
        db.session.flush()
        activity_id = activity_to_create.ActivityId

        selected_values = form.activity.speaker.data
        for choice in form.activity.speaker.choices:
            if choice[0] in selected_values:
                role = choice[1].split(" - ")[-1]
                if role == "Alumni":
                    speaker_to_add = Speaker(ActivityId=activity_id,
                                            AlumniId=choice[0])
                else:
                    speaker_to_add = Speaker(ActivityId=activity_id,
                                            FacultyId=choice[0])
                db.session.add(speaker_to_add)
        db.session.commit()
        flash('Extension program is successfully inserted.', category='success')
        return redirect(url_for('programs.programs'))
    if form.errors != {}: # If there are errors from the validations
        for err_msg in form.errors.values():
            flash(err_msg, category='error')

    return render_template('programs/add_ext_program.html', form=form)


@bp.route('/extension-program/update/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def updateExtensionProgram(id):
    form = ProgramForm()
    extension_program = ExtensionProgram.query.get_or_404(id)
    if form.validate_on_submit():
        if form.image.data is not None:
            # If extension program has previous image, remove it from imagekit
            if extension_program.ImageFileId is not None:
                status = purgeImage(extension_program.ImageFileId)
            # Get the input image path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.image.data.filename)
                )
            # Save image
            status = saveImage(form.image.data, imagepath)
            if status.error is not None:
                flash("File Upload Error", category='error')
                return redirect(request.referrer)
            else:
                extension_program.ImageUrl = status.url
                extension_program.ImageFileId = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

        extension_program.Name = form.program_name.data
        extension_program.Rationale = form.rationale.data
        extension_program.AgendaId = int(form.agenda.data)
        extension_program.ProgramId = int(form.program.data)
        try:
            db.session.commit()
            flash('Extension progam is successfully updated.', category='success')
        except:
            flash('There was an issue updating the extension program.', category='error')

        return redirect(request.referrer)
    
    if form.errors != {}: # If there are errors from the validations
        for err_msg in form.errors.values():
            flash(err_msg, category='error')

    return redirect(url_for('programs.programs'))


@bp.route('/extension-program/delete/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def deleteExtensionProgram(id):
    extension_program = ExtensionProgram.query.filter_by(ExtensionProgramId=id).first()
    try:
        db.session.delete(extension_program)
        db.session.commit()
        flash('Extension program is successfully deleted.', category='success')
    except Exception as e:
        print(e)
        flash('There was an issue deleting the extension program.', category='error')

    return redirect(url_for('programs.programs'))

@bp.route('/extension-program/project/insert', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def insertProject():
    form = ProjectForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Insert project
            str_image_url = None
            str_image_file_id = None
            if form.image.data is not None:
                # Get the input image path
                imagepath = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], secure_filename(form.image.data.filename)
                    )
                # Save image
                status = saveImage(form.image.data, imagepath)
                if status.error is not None:
                    flash("Project image upload failed", category="error")
                    return redirect(request.referrer)
                else:
                    str_image_url = status.url
                    str_image_file_id = status.file_id
                # Delete file from local storage
                if os.path.exists(imagepath):
                    os.remove(imagepath)

            str_proposal_url = None
            str_proposal_file_id = None

            # Get the project proposal path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.project_proposal.data.filename)
                )
            # Save project proposal to local and upload to cloud 
            status = saveImage(form.project_proposal.data, imagepath)
            if status.error is not None:
                flash("Project proposal upload failed", category="error")
                return redirect(request.referrer)
            else:
                str_proposal_url = status.url
                str_proposal_file_id = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

            project_team = getProjectTeamInput(form.project_team.data, form.project_team.choices)

            project_to_add = Project(Title = form.title.data,
                                    Implementer = form.implementer.data,
                                    LeadProponentId = current_user.UserId,
                                    CollaboratorId = form.collaborator.data,
                                    ProjectTeam = project_team,
                                    TargetGroup = form.target_group.data,
                                    ProjectType = form.project_type.data,
                                    StartDate = form.start_date.data,
                                    EndDate = form.end_date.data,
                                    ImpactStatement = form.impact_statement.data,
                                    Objectives = form.objectives.data,
                                    ResearchBased = form.research_based.data if form.research_based.data else False,
                                    ResearchId = form.research_title.data if form.research_based.data and form.research_title.data else None,
                                    ImageUrl=str_image_url,
                                    ImageFileId=str_image_file_id,
                                    ProjectProposalUrl = str_proposal_url,
                                    ProjectProposalFileId = str_proposal_file_id,
                                    ExtensionProgramId = form.extension_program.data)
            db.session.add(project_to_add)
            
            # Get the id of the recently added project
            db.session.flush()
            int_project_id = project_to_add.ProjectId

            # Add budget of the project
            approved_budgets = request.form.getlist('approved_budget')
            fund_types = request.form.getlist('fund_type')
            budget_data = zip(approved_budgets, fund_types)
            for approved_budget, fund_type in budget_data:
                budget_to_add = Budget(FundType=fund_type,
                                        Amount=approved_budget,
                                        ProjectId=int_project_id,
                                        CollaboratorId=form.collaborator.data if fund_type=='External' else None)
                db.session.add(budget_to_add)

            db.session.commit()
            flash('Extension project is successfully inserted.', category='success')
            return redirect(request.referrer)
        if form.errors != {}: # If there are errors from the validations
            for field, error in form.errors.items():
                flash(f"Field '{field}' has an error: {error}", category='error')
    return redirect(url_for("programs.programs"))


@bp.route('/project/<int:id>', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def viewProject(id):
    form = ProjectForm()
    activity_form = ActivityForm()
    project = Project.query.get_or_404(id)
    project_budget = Budget.query.filter_by(ProjectId=id).all()
    registered = Registration.query.filter_by(ProjectId=project.ProjectId).all()
    # for calendar - temp
    events = Activity.query.filter_by(ProjectId=id).all()
    
    form.title.data = project.Title
    form.implementer.data = project.Implementer
    form.project_team.data = project.ProjectTeam
    form.target_group.data = project.TargetGroup
    form.project_type.data = project.ProjectType
    form.start_date.data = project.StartDate
    form.end_date.data = project.EndDate
    form.impact_statement.data = project.ImpactStatement
    form.objectives.data = project.Objectives

    return render_template('programs/view_project.html', project=project, form=form, activity_form=activity_form, registered=registered, events=events, project_budget=project_budget)


@bp.route('/project/update/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def updateProject(id):
    form = ProjectForm()
    extension_project = Project.query.get_or_404(id)
    project_budget = Budget.query.filter_by(ProjectId=id).all()
    if form.validate_on_submit():
        if form.image.data is not None:
            # If extension project has previous image, remove it from imagekit
            if extension_project.ImageFileId is not None:
                try:
                    status = purgeImage(extension_project.ImageFileId)
                except:
                    print("image not found")
            # Get the input image path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.image.data.filename)
                )
            # Save image
            status = saveImage(form.image.data, imagepath)
            if status.error is not None:
                flash("File Upload Error", category='error')
                return redirect(url_for('programs.programs'))
            else:
                extension_project.ImageUrl = status.url
                extension_project.ImageFileId = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

        # Delete previous project proposal from cloud
        if form.project_proposal.data is not None:
            try:
                status = purgeImage(extension_project.ImageFileId)
            except:
                print("image not found")

            # Get the input image path
            filepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.project_proposal.data.filename)
                )
            # Save image
            status = saveImage(form.project_proposal.data, filepath)
            if status.error is not None:
                flash("File Upload Error", category='error')
                return redirect(url_for('programs.programs'))
            else:
                extension_project.ProjectProposalUrl = status.url
                extension_project.ProjectProposalFileId = status.file_id
            # Delete file from local storage
            if os.path.exists(filepath):
                os.remove(filepath)

        project_team = getProjectTeamInput(form.project_team.data, form.project_team.choices)

        # Update project details
        extension_project.Title =form.title.data
        extension_project.Implementer = form.implementer.data
        extension_project.CollaboratorId = form.collaborator.data
        extension_project.ProjectTeam = project_team
        extension_project.TargetGroup = form.target_group.data
        extension_project.ProjectTyFpe = form.project_type.data
        extension_project.StartDate =  form.start_date.data
        extension_project.EndDate = form.end_date.data
        extension_project.ImpactStatement = form.impact_statement.data
        extension_project.Objectives = form.objectives.data
        extension_project.ResearchBased = form.research_based.data if form.research_based.data else False
        extension_project.ResearchId = form.research_title.data if form.research_based.data and form.research_title else None

        # Edit budget
        ids = request.form.getlist('id')
        approved_budgets = request.form.getlist('approved_budget')
        fund_types = request.form.getlist('fund_type')
        budget_data = zip(approved_budgets, fund_types)

        # Delete the removed budget from database
        if len(project_budget) != len(ids):
            for budget in project_budget:
                # If the id is not in request form, the budget has been removed
                if str(budget.BudgetId) not in ids:
                    db.session.delete(budget) # Delete the budget from the database
        
        count = 0 # Initial index 
        for approved_budget, fund_type in budget_data:
            # Update the data of first n budget/s in budget_data with id in database
            if count < len(ids):
                budget = Budget.query.filter_by(BudgetId=int(ids[count])).first()
                budget.Amount = approved_budget
                budget.FundType = fund_type
                budget.CollaboratorId = form.collaborator.data
            else: # Add to database the remaining/newly added budget
                budget_to_add = Budget(Amount=approved_budget,
                                        FundType=fund_type,
                                        ProjectId=id,
                                        CollaboratorId=form.collaborator.data)
                db.session.add(budget_to_add)
            count += 1 # Increment index

        try:
            db.session.commit()
            flash('Extension project is successfully updated.', category='success')
        except:
            flash('There was an issue updating the extension project.', category='error')

        return redirect(url_for('programs.viewProject', id=extension_project.ProjectId))
    
    if form.errors != {}: # If there are errors from the validations
        for err_msg in form.errors.values():
            flash(err_msg, category='error')

    return redirect(url_for('programs.viewProject', id=extension_project.ProjectId))


@bp.route('/delete/project/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def deleteProject(id):
    project = Project.query.get_or_404(id)
    ext_program_id = project.ExtensionProgram.ExtensionProgramId
    try:
        if project.ImageFileId is not None:
            status = purgeImage(project.ImageFileId)
        if project.ProjectProposalFileId is not None:
            status = purgeImage(project.ProjectProposalFileId)
        db.session.delete(project)
        db.session.commit()
        flash('Extension project is successfully deleted.', category='success')
    except Exception as e:
        flash(f'There was an issue deleting the extension project. {e}', category='error')

    return redirect(url_for('programs.viewExtensionProgram', id=ext_program_id))

@bp.route('<int:id>/activity/create', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def insertActivity(id):
    form = ActivityForm()

    if form.validate_on_submit():
        str_image_url = None
        str_image_file_id = None
        if form.image.data is not None:
            # Get the input image path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.image.data.filename)
                )
            # Save image
            status = saveImage(form.image.data, imagepath)
            if status.error is not None:
                flash("File Upload Error", category='error')
                return redirect(url_for('programs.viewProject', id=form.project.data))
            else:
                str_image_url = status.url
                str_image_file_id = status.file_id

            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)
                
        activity_to_create = Activity(ActivityName=form.activity_name.data,
                                        Date=form.date.data,
                                        StartTime=form.start_time.data,
                                        EndTime=form.end_time.data,
                                        Description=form.activity_description.data,
                                        LocationId=form.location.data,
                                        ProjectId=id,
                                        ImageUrl=str_image_url,
                                        ImageFileId=str_image_file_id)
        db.session.add(activity_to_create)
        db.session.flush()
        activity_id = activity_to_create.ActivityId

        selected_values = form.speaker.data
        for choice in form.speaker.choices:
            if choice[0] in selected_values:
                role = choice[1].split(" - ")[-1]
                if role == "Alumni":
                    speaker_to_add = Speaker(ActivityId=activity_id,
                                            AlumniId=choice[0])
                else:
                    speaker_to_add = Speaker(ActivityId=activity_id,
                                            FacultyId=choice[0])
                db.session.add(speaker_to_add)
        db.session.commit()
        flash('Activity is successfully inserted.', category='success')
        return redirect(url_for('programs.viewProject', id=id))
    if form.errors != {}: # If there are errors from the validations
        for err_msg in form.errors.values():
            flash(err_msg, category='error')

    return redirect(url_for('programs.viewProject', id=id))

@bp.route('/activity/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def updateActivity(id):
    form = ActivityForm()
    activity = Activity.query.filter_by(ActivityId=id).first()
    if form.validate_on_submit():
        if form.image.data is not None:
            # If extension project has previous image, remove it from imagekit
            if activity.ImageFileId is not None:
                status = purgeImage(activity.ImageFileId)
            # Get the input image path
            imagepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(form.image.data.filename)
                )
            # Save image
            status = saveImage(form.image.data, imagepath)
            if status.error is not None:
                flash("File Upload Error", category='error')
                return redirect(url_for('programs.viewProject', id=activity.ProjectId))
            else:
                activity.ImageUrl = status.url
                activity.ImageFileId = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

        activity.ActivityName=form.activity_name.data
        activity.Date=form.date.data
        activity.StartTime=form.start_time.data
        activity.EndTime=form.end_time.data
        activity.Description=form.activity_description.data
        activity.LocationId=form.location.data

        selected_values = form.speaker.data
        for speaker in activity.Speaker:
            bool_is_removed = True
            if speaker.FacultyId:
                if str(speaker.FacultyId) in selected_values:
                    selected_values.remove(str(speaker.FacultyId))
                    bool_is_removed = False
            else:
                if str(speaker.AlumniId) in selected_values:
                    selected_values.remove(str(speaker.AlumniId))
                    bool_is_removed = False
            if bool_is_removed:
                db.session.delete(speaker)

        if selected_values:
            for choice in form.speaker.choices:
                if choice[0] in selected_values:
                    role = choice[1].split(" - ")[-1]
                    if role == "Alumni":
                        speaker_to_add = Speaker(ActivityId=activity.ActivityId,
                                                AlumniId=choice[0])
                    else:
                        speaker_to_add = Speaker(ActivityId=activity.ActivityId,
                                                FacultyId=choice[0])
                    db.session.add(speaker_to_add)
        db.session.commit()
        flash('Activity is successfully updated.', category='success')
        return redirect(request.referrer)
    if form.errors != {}: # If there are errors from the validations
        for field, error in form.errors.items():
            print(f"Field '{field}' has an error: {error}")
            flash(f"Field '{field}' has an error: {error}")
    return redirect(url_for('programs.viewProject', id=activity.ProjectId))

@bp.route('/delete/activity/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def deleteActivity(id):
    activity = Activity.query.get_or_404(id)
    project_id = activity.ProjectId
    try:
        if activity.ImageFileId is not None:
            status = purgeImage(activity.ImageFileId)
        db.session.delete(activity)
        db.session.commit()
        flash('Activity is successfully deleted.', category='success')
    except Exception as e:
        flash('There was an issue deleting the activity', category='error')

    return redirect(url_for('programs.viewProject', id=project_id))

@bp.route('/view/activity/<int:id>')
@login_required(role=["Admin", "Faculty"])
def viewActivity(id):
    activity_form = ActivityForm()
    activity = Activity.query.get_or_404(id)
    attendance = Attendance.query.filter_by(ActivityId=id).all()
    current_date = datetime.utcnow().date()
    return render_template('programs/view_activity.html', activity=activity, attendance=attendance, activity_form=activity_form, current_date=current_date)


@bp.route('/calendar')
@login_required(role=["Admin", "Faculty"])
def calendar():
    projects = Project.query.all()
    selected_project_id = request.args.get('project_id', None)
    # Call a function to fetch activities based on the selected project
    activities = Activity.query.all()
    if selected_project_id:
        activities = Activity.query.filter_by(ProjectId=selected_project_id).order_by(Activity.Date.asc()).all()
    
    return render_template('programs/activity_calendar.html', projects=projects, events=activities, selected_project_id=selected_project_id)


@bp.route('/budget-allocation')
@login_required(role=["Admin", "Faculty"])
def budgetAllocation():
    projects = None 
    if current_user.Role.RoleName == "Faculty":
        projects = Project.query.filter_by(LeadProponentId= current_user.UserId).all()
    else:
        projects = Project.query.all()
    return render_template('programs/budget_allocation.html', projects=projects)

@bp.route('/budget-allocation/<int:id>', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def projectBudget(id):
    form = ItemForm()
    project = Project.query.filter_by(ProjectId=id).first()
    to_be_purchased_items = []
    purchased_items = []
    if project.Item:
        for item in project.Item:
            if item.IsPurchased==0:
                to_be_purchased_items.append(item)
            else:
                purchased_items.append(item)

    if request.method == 'POST':
        if form.validate_on_submit():
            item_to_add = Item(ItemName=form.item.data,
                                Amount=form.amount.data,
                                ProjectId=form.project.data)
            try:
                db.session.add(item_to_add)
                db.session.commit()
                flash('Item is successfully inserted', category='success')
            except:
                flash('There was an issue inserting the item', category='error')

        if form.errors != {}: # If there are errors from the validations
            for field, error in form.errors.items():
                flash(f"Field '{field}' has an error: {error}", category='error')
        
        return redirect(url_for('programs.projectBudget', id=id))
    
    external_budget = Budget.query.filter_by(ProjectId=id, FundType='External').first()
    internal_budget = Budget.query.filter_by(ProjectId=id, FundType='Internal').first()
    external_budget = external_budget.Amount if external_budget else 0
    internal_budget = internal_budget.Amount if internal_budget else 0
    return render_template('programs/project_budget.html', project=project, form=form, external_budget=external_budget, internal_budget=internal_budget, to_be_purchased_items=to_be_purchased_items, purchased_items=purchased_items)

@bp.route("/purchase-item/<int:status>", methods=["POST"])
@login_required(role=["Admin", "Faculty"])
def purchaseItem(status):
    item_id = request.json["itemId"]
    item = Item.query.filter_by(ItemId=item_id).first()
    if item:
        item.IsPurchased = status
        if status == 1:
            item.DatePurchased = datetime.utcnow()
        else:
            item.DatePurchased = None
        db.session.commit()
        return { "message": "Item status updated successfully!",
                "amount": item.Amount}
    else:
        return { "error": "Item not found" }, 404

@bp.route("/update-item/<int:id>", methods=["POST"])
@login_required(role=["Admin", "Faculty"])
def updateItem(id):
    form = ItemForm()
    item = Item.query.filter_by(ItemId=id).first()
    item.ItemName = form.item.data
    item.ProjectId = form.project.data
    item.Amount = form.amount.data
    try:
        db.session.commit()
        flash('Item is successfully updated', category='success')
    except:
        flash('There was an issue updating the item', category='error')
    return redirect(request.referrer)

@bp.route("/delete-item/<int:id>", methods=["POST"])
@login_required(role=["Admin", "Faculty"])
def deleteItem(id):
    item = Item.query.filter_by(ItemId=id).first()
    try:
        if item.ReceiptId is not None:
            status = purgeImage(item.ReceiptId)
        db.session.delete(item)
        db.session.commit()
        flash('Item is successfully deleted.', category='success')
    except Exception as e:
        flash('There was an issue deleting the item', category='error')
    
    return redirect(request.referrer)

@bp.route("/upload-receipt/<int:id>", methods=["POST"])
@login_required(role=["Admin", "Faculty"])
def uploadReceipt(id):
    form = ItemForm()
    item = Item.query.filter_by(ItemId=id).first()
    # If item has previous reciept, remove it from imagekit
    if item.ReceiptId is not None:
        status = purgeImage(item.ReceiptId)
    # Get the input image path
    imagepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"], secure_filename(form.receipt.data.filename)
        )
    # Save receipt
    status = saveImage(form.receipt.data, imagepath)
    if status.error is not None:
        flash("File Upload Error", category='error')
        return redirect(request.referrer)
    else:
        item.ReceiptUrl = status.url
        item.ReceiptId = status.file_id
    # Delete file from local storage
    if os.path.exists(imagepath):
        os.remove(imagepath)

    try:
        db.session.commit()
        flash('Receipt is successfully uploaded', category='success')
    except:
        flash('There was an issue uploading the receipt', category='error')

    return redirect(request.referrer)

@bp.route('/assign-student', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def assignStudent():
    student_registration = Registration.query.filter_by(RegistrationId=int(request.form.get('id'))).first()
    student_registration.IsAssigned = bool(request.form.get('is_assigned'))
    try:
        db.session.commit()
        flash('Student is successfully assigned to manage attendance and evaluations', category='success')
    except:
        flash('There was an issue assigning the student', category='error')

    return redirect(url_for('programs.viewProject', id=int(request.form.get('project_id'))))


@bp.route('/cert/<int:id>', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def cert(id):
    certificate(id)
    # fillpdfs.get_form_fields(os.path.join(current_app.config["UPLOAD_FOLDER"], "e-cert (beneficiary) (FILLABLE).pdf"))
    # Get all the registered beneficiaries in the project
    # beneficiaries_id = [registration.UserId for registration in Registration.query.filter_by(ProjectId=id).all()]
    # registered_beneficiaries = [User.query.filter_by(UserId=beneficiary_id).first() for beneficiary_id in beneficiaries_id]
    # beneficiaries = [registration.User for registration in Registration.query.filter_by(ProjectId=id).all() if registration.User.RoleId == 2]
    # print(beneficiaries)
    # for user in beneficiaries:
    #     print(user.Beneficiary.FirstName)
    # # Get the project proponent's name for the certificate
    # project = Project.query.filter_by(ProjectId=id).first()
    # project_proponent = User.query.filter_by(UserId=project.LeadProponentId).first()
    # proponent_name = project_proponent.Faculty.FirstName + ' '
    # if project_proponent.Faculty.MiddleName:
    #     proponent_name += project_proponent.Faculty.MiddleName[0] + '. '
    # proponent_name += project_proponent.Faculty.LastName

    # # Get the extension program's name for the certificate
    # extension_program = ExtensionProgram.query.filter_by(ExtensionProgramId=project.ExtensionProgramId).first()
    
    # # Generate certificate for each beneficiary registered in the project
    # for beneficiary in registered_beneficiaries:
    #     # Get the name of the beneficiary for the certificate
    #     beneficiary_name = beneficiary.Beneficiary.FirstName + ' '
    #     if beneficiary.Beneficiary.MiddleName:
    #         beneficiary_name += beneficiary.Beneficiary.MiddleName[0] + '. '
    #     beneficiary_name += beneficiary.Beneficiary.LastName
    #     data_dict = {'Text-n_L-ntAGRy': beneficiary_name,
    #                 'Text-Pnb29VfGWk': extension_program.Name,
    #                 'Date-jWSJ8ZAYJ_': datetime.utcnow(),
    #                 'Text-tf2etyjp87': proponent_name,
    #                 'Text-bcixq7yk8z': 'Jaime P. Gutierrez, Jr.'}
        
    #     # Get the initials of the beneficiary
    #     beneficiary_initials = ''.join([word[0] for word in beneficiary_name.split()])
    #     # Fill the pdf with the required information
    #     filepath = os.path.join(current_app.root_path, "media") + "\\" + extension_program.Name + "-" + beneficiary_initials + " CERTIFICATE.pdf"
    #     fillpdfs.write_fillable_pdf(os.path.join(current_app.config["UPLOAD_FOLDER"], "e-cert (beneficiary) (FILLABLE).pdf"), filepath, data_dict, flatten=True)

    #     # Upload cert pdf to cloud
    #     status = uploadImage(filepath, extension_program.Name + "-" + beneficiary_initials + " CERTIFICATE.pdf")

    #     # Get the url and file id of the uploaded certificate
    #     str_cert_url = None
    #     str_cert_file_id = None
    #     if status.error is not None:
    #         flash("Error in releasing certificates", category="error")
    #         return url_for('programs.viewProject', id=id)
    #     else:
    #         str_cert_url = status.url
    #         str_cert_file_id = status.file_id

    #     # Delete file from local storage after uploading to cloud
    #     if os.path.exists(filepath):
    #         os.remove(filepath)

    #     # Save certificate to database
    #     cert_to_add = Certificate(CertificateUrl=str_cert_url, 
    #                             CertificateFileId = str_cert_file_id, 
    #                             UserId=beneficiary.UserId, 
    #                             ProjectId=id)
        
    #     db.session.add(cert_to_add)
    # try:
    #     db.session.commit()
    #     flash('Certificate is successfully released', category='success')
    # except Exception as e:
    #     print(e)

    flash('Releasing of certificates is in progress', category='info')
    return redirect(url_for('programs.viewProject', id=id))


# =========================================================
# ||                      USER VIEWS                     ||
# =========================================================

@bp.route('/extension-programs')
@role_excluded(role=["Admin", "Faculty"])
def extensionPrograms():
    extension_programs = ExtensionProgram.query.all()
    programs = Course.query.all()
    agendas = Agenda.query.all()
    return render_template('programs/ext_programs_list.html', extension_programs=extension_programs, programs=programs, agendas=agendas)

@bp.route('/extension-program/view/<int:id>')
@role_excluded(role=["Admin", "Faculty"])
def extensionProgram(id):
    extension_program = ExtensionProgram.query.filter_by(ExtensionProgramId=id).first()
    projects = Project.query.filter_by(ExtensionProgramId=id).order_by(Project.EndDate.desc()).all()
    project_ids = [project.ProjectId for project in projects]
    events = Activity.query.filter(Activity.ProjectId.in_(project_ids),
                                    Activity.Date>datetime.utcnow().date()).order_by(Activity.Date.desc()).limit(5).all()
    current_date = datetime.utcnow().date()
    # Get all the faculty in each project in current extension program
    project_team = getProjectTeam(projects)
    
    return render_template('programs/extension_program.html', extension_program=extension_program, projects=projects, events=events, project_team=project_team, current_date=current_date)


@bp.route('/projects')
@role_excluded(role=["Admin", "Faculty"])
def projects():
    projects = Project.query.all()
    return render_template('programs/projects_list.html', projects=projects)

@bp.route('/projects/<int:id>')
@role_excluded(role=["Admin", "Faculty"])
def project(id):
    project = Project.query.filter_by(ProjectId=id).first()
    activities = Activity.query.filter_by(ProjectId=id).order_by(Activity.Date.desc()).all()
    events = [activity for activity in activities if activity.Date > datetime.utcnow().date()]
    # arrange upcoming activities in ascending order
    events.reverse()
    events = events[:5] # limit events to 5 data
    user_id = current_user.UserId if current_user.is_authenticated else None
    registration = Registration.query.filter_by(ProjectId=id, UserId=user_id).first()
    current_date = datetime.utcnow().date()

    # Get all the faculty in each project in current extension program
    project_team = getProjectTeam([project])

    return render_template('programs/project_reg.html', project=project, events=events,activities=activities, project_team=project_team, registration=registration, current_date=current_date)

@bp.route('/registration/<int:project_id>', methods=['POST'])
@login_required(role=["Beneficiary", "Student"])
def registration(project_id):
    user_id = current_user.UserId
    registration_to_create = Registration(ProjectId = project_id,
                                        UserId=user_id)
    try:
        db.session.add(registration_to_create)
        db.session.commit()
        flash('Registration Successful!', category='success')
    except:
        flash('There was an issue during registration.', category='error')

    return redirect(url_for('programs.project', id=project_id))

@bp.route('/registration/cancel/<int:project_id>', methods=['POST'])
@login_required(role=["Beneficiary", "Student"])
def cancelRegistration(project_id):
    user_id = current_user.UserId if current_user.is_authenticated else None
    registration = Registration.query.filter_by(ProjectId=project_id, UserId=user_id).first()

    try:
        db.session.delete(registration)
        db.session.commit()
        flash('Registration is successfully canceled.', category='success')
    except:
        flash('There was an issue canceling the registration.', category='error')

    return redirect(url_for('programs.project', id=project_id))


@bp.route('/activities')
@role_excluded(role=["Admin", "Faculty"])
def activities():
    activities = Activity.query.order_by(Activity.Date.desc()).all()
    return render_template('programs/activities.html', activities=activities)

@bp.route('/activities/<int:id>')
@role_excluded(role=["Admin", "Faculty"])
def activity(id):
    activity = Activity.query.filter_by(ActivityId=id).first()
    current_date = datetime.utcnow().date()
    suggestions = Activity.query.filter(Activity.Date > current_date,
                                        Activity.ProjectId==activity.ProjectId,
                                        Activity.ActivityId!=activity.ActivityId ).order_by(func.random()).limit(3).all()
    evaluation_id = None
    bool_is_evaluation_taken = False
    if current_user.is_authenticated and current_user.Role.RoleId==2:
        beneficiary_id = current_user.Beneficiary.BeneficiaryId
        evaluation_id = activity.Evaluation[0].EvaluationId if activity.Evaluation else None
        bool_is_evaluation_taken = True if Response.query.filter_by(BeneficiaryId=beneficiary_id, EvaluationId=evaluation_id).first() else False
    return render_template('programs/activity.html', activity=activity, suggestions=suggestions, current_date=current_date, bool_is_evaluation_taken=bool_is_evaluation_taken)


@bp.route('/activities/<int:id>/map')
def activity_map(id):
    activity = Activity.query.filter_by(ActivityId=id).first()

    # Create a map with a marker for the activity location
    mapObj = folium.Map(location=[float(activity.Location.Latitude), float(activity.Location.Longitude)], zoom_start=15, tiles=None)

    # Add tile layers
    folium.TileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                    name='CartoDB.DarkMatter', attr="CartoDB.DarkMatter").add_to(mapObj)
    folium.TileLayer('openstreetmap').add_to(mapObj)
    
    folium.LayerControl().add_to(mapObj)

    folium.Marker(
        location=[float(activity.Location.Latitude), float(activity.Location.Longitude)],
        popup=folium.Popup(f'Activity Location: {activity.Location.LocationName}', max_width=300),
        icon=folium.Icon(color='red')
    ).add_to(mapObj)

    mapObj.save('app/templates/programs/activity_map.html')

    return render_template('programs/activity_map.html', activity=activity)

@bp.route('/project/management/<int:id>')
@login_required(role=["Student"])
def studentProjectManage(id):
    project = Project.query.filter_by(ProjectId=id).first()
    return render_template('programs/student_manager.html', project=project)

@bp.route('project/<int:project_id>/activity/<int:activity_id>/attendance')
@login_required(role=["Student"])
def manageAttendance(project_id, activity_id):
    project = Project.query.filter_by(ProjectId=project_id).first()
    activity = Activity.query.filter_by(ActivityId=activity_id).first()
    attendance = [attendance.UserId for attendance in Attendance.query.filter_by(ActivityId=activity_id).all()]
    registered_users = Registration.query.filter_by(ProjectId=project_id).all()
    beneficiaries = []
    students = []

    for user in registered_users:
        if user.User.Role.RoleName == "Student":
            if user.User.UserId in attendance:
                students.append([user, 1])
            else:
                students.append([user, 0])
        else:
            if user.User.UserId in attendance:
                beneficiaries.append([user, 1])
            else:
                beneficiaries.append([user, 0])
    
    return render_template('programs/record_attendance.html', project=project, activity=activity, beneficiaries=beneficiaries, students=students)

@bp.route('/activity/record-attendance', methods=["POST"])
@login_required(role=["Student"])
def recordAttendance():
    attendance_to_add = Attendance(UserId=request.form.get('user_id'),
                                ActivityId=request.form.get('activity_id'))
    try:
        db.session.add(attendance_to_add)
        db.session.commit()
        flash('Attendance is successfully recorded.', category='success')
    except:
        flash('There was an issue recording the attendance.', category='error')
    
    return redirect(url_for('programs.manageAttendance', project_id=request.form.get('project_id'), activity_id=request.form.get('activity_id')))


def getProjectTeam(projects):
    faculty_team = {}
    for project in projects:
        faculty_team.update(project.ProjectTeam)
        
    project_team = []
    for faculty in faculty_team.items():
        faculty_info = Faculty.query.filter_by(FacultyId=int(faculty[0])).first()
        project_team.append(faculty_info)
    
    return project_team
