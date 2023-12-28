from app.programs import bp
from flask import render_template, url_for, request, redirect, flash, current_app
from flask_login import current_user
from ..models import Project, ExtensionProgram, Program, Registration, Agenda, ExtensionProgram, Activity, Response, User, Certificate, Budget, Item, Attendance
from .forms import ProgramForm, ProjectForm, ActivityForm, CombinedForm, ItemForm
import calendar
from datetime import datetime
from app import db, api
from ..store import uploadImage, purgeImage
from werkzeug.utils import secure_filename
import os, requests
from ..decorators.decorators import login_required
from ..Api.resources import ExtensionProgramListApi
from sqlalchemy import func
from fillpdf import fillpdfs

url = 'https://pupqcfis-com.onrender.com/api/all/Faculty_Profile'

api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJrZXkiOiIzM2Y0ZWI4NWNjNDQ0MTQzOWFkMzMwYWUzMzJiNmYwYyJ9.5pjwXdaIIZf6Jm9zb26YueCPQhj6Tc18bbZ0vnX4S9M'

# Set up headers with the API key in the 'API Key' authorization header
headers = {
    'Authorization': 'API Key',
    'token': api_key,  # 'token' key with the API key value
    'Content-Type': 'application/json'  # Adjust content type as needed
}

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

@bp.route('/pupqc/extension-programs')
@login_required(role=["Admin", "Faculty"])
def programs():
    form = ProgramForm()
    project_form = ProjectForm()
    programs = ExtensionProgram.query.all()    
    
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
                return url_for('programs.addProgram')
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
                return redirect(url_for('programs.addProgram'))
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
            return redirect(url_for('programs.addProgram'))
        else:
            str_proposal_url = status.url
            str_proposal_file_id = status.file_id
        # Delete file from local storage
        if os.path.exists(imagepath):
            os.remove(imagepath)


        lead_proponent = current_user.User[0]
        project_team = getProjectTeamInput(form.project.project_team.data, form.project.project_team.choices)

        project_to_add = Project(Title = form.project.title.data,
                                Implementer = form.project.implementer.data,
                                LeadProponentId = lead_proponent.UserId,
                                CollaboratorId = form.project.collaborator.data,
                                ProjectTeam = project_team,
                                TargetGroup = form.project.target_group.data,
                                ProjectType = form.project.project_type.data,
                                StartDate = form.project.start_date.data,
                                EndDate = form.project.end_date.data,
                                ProposedBudget = form.project.proposed_budget.data,
                                ApprovedBudget = form.project.approved_budget.data,
                                FundType = form.project.fund_type.data,
                                ImpactStatement = form.project.impact_statement.data,
                                Objectives = form.project.objectives.data,
                                Status = form.project.status.data,
                                ImageUrl=str_image_url,
                                ImageFileId=str_image_file_id,
                                ProjectProposalUrl = str_proposal_url,
                                ProjectProposalFileId = str_proposal_file_id,
                                ExtensionProgramId = int_program_id)
        db.session.add(project_to_add)
        db.session.flush()
        int_project_id = project_to_add.ProjectId
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
                return redirect(url_for('programs.addProgram'))
            else:
                str_image_url = status.url
                str_image_file_id = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)
                
        speakers = getProjectTeamInput(form.activity.speaker.data, form.activity.speaker.choices)
                
        activity_to_create = Activity(ActivityName=form.activity.activity_name.data,
                                        Date=form.activity.date.data,
                                        StartTime=form.activity.start_time.data,
                                        EndTime=form.activity.end_time.data,
                                        Description=form.activity.activity_description.data,
                                        Location=form.activity.location.data,
                                        Speaker=speakers,
                                        ProjectId= int_project_id,
                                        ImageUrl=str_image_url,
                                        ImageFileId=str_image_file_id)
        db.session.add(activity_to_create)
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
                flash("File Upload Error")
                return redirect(url_for('programs.programs'))
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

        return redirect(url_for('programs.programs'))
    
    if form.errors != {}: # If there are errors from the validations
        for err_msg in form.errors.values():
            flash(err_msg)

    return redirect(url_for('programs.programs'))


@bp.route('/extension-program/delete/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
def deleteExtensionProgram(id):
    extension_program = ExtensionProgram.query.get_or_404(id)
    try:
        if extension_program.ImageFileId is not None:
            status = purgeImage(extension_program.ImageFileId)
        db.session.delete(extension_program)
        db.session.commit()
        flash('Extension program is successfully deleted.', category='success')
    except:
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
                    return redirect(url_for('programs.addProgram'))
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
                return redirect(url_for('programs.addProgram'))
            else:
                str_proposal_url = status.url
                str_proposal_file_id = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

            lead_proponent = current_user.User[0]            
            project_team = getProjectTeamInput(form.project_team.data, form.project_team.choices)

            project_to_add = Project(Title = form.title.data,
                                    Implementer = form.implementer.data,
                                    LeadProponentId = lead_proponent.UserId,
                                    CollaboratorId = form.collaborator.data,
                                    ProjectTeam = project_team,
                                    TargetGroup = form.target_group.data,
                                    ProjectType = form.project_type.data,
                                    StartDate = form.start_date.data,
                                    EndDate = form.end_date.data,
                                    ImpactStatement = form.impact_statement.data,
                                    Objectives = form.objectives.data,
                                    Status = form.status.data,
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
            return redirect(url_for('programs.programs'))
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors:
                flash(err_msg, category='error')
    return redirect(url_for('programs.programs'))


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
    form.collaborator.data = project.Collaborator.CollaboratorId
    form.project_team.data = project.ProjectTeam
    form.target_group.data = project.TargetGroup
    form.project_type.data = project.ProjectType
    form.start_date.data = project.StartDate
    form.end_date.data = project.EndDate
    form.impact_statement.data = project.ImpactStatement
    form.objectives.data = project.Objectives
    form.status.data = project.Status

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
                flash("File Upload Error")
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
                flash("File Upload Error")
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
        extension_project.Status = form.status.data

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
                flash("File Upload Error")
                return redirect(url_for('programs.viewProject', id=form.project.data))
            else:
                str_image_url = status.url
                str_image_file_id = status.file_id

            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

        selected_values = form.speaker.data
        speakers ={}
        for choice in form.speaker.choices:
            if choice[0] in selected_values:
                speakers[choice[0]] = choice[1]
                
        activity_to_create = Activity(ActivityName=form.activity_name.data,
                                        Date=form.date.data,
                                        StartTime=form.start_time.data,
                                        EndTime=form.end_time.data,
                                        Description=form.activity_description.data,
                                        Location=form.location.data,
                                        Speaker=speakers,
                                        ProjectId=id,
                                        ImageUrl=str_image_url,
                                        ImageFileId=str_image_file_id)
        db.session.add(activity_to_create)
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
                flash("File Upload Error")
                return redirect(url_for('programs.viewProject', id=activity.ProjectId))
            else:
                activity.ImageUrl = status.url
                activity.ImageFileId = status.file_id
            # Delete file from local storage
            if os.path.exists(imagepath):
                os.remove(imagepath)

        if form.speaker.data:
            selected_values = form.speaker.data
            speakers ={}
            for choice in form.speaker.choices:
                if choice[0] in selected_values:
                    speakers[choice[0]] = choice[1]

            activity.Speaker = speakers

        activity.ActivityName=form.activity_name.data
        activity.Date=form.date.data
        activity.StartTime=form.start_time.data
        activity.EndTime=form.end_time.data
        activity.Description=form.activity_description.data
        activity.Location=form.location.data

        db.session.commit()
        flash('Activity is successfully updated.', category='success')
        return redirect(url_for('programs.viewProject', id=activity.ProjectId))
    if form.errors != {}: # If there are errors from the validations
        for field, error in form.errors.items():
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


@bp.route('/calendar')
@login_required(role=["Admin", "Faculty"])
def calendar():
    projects = Project.query.all()
    selected_project_id = request.args.get('project_id', None)
    # Call a function to fetch activities based on the selected project
    activities = Activity.query.all()
    
    return render_template('programs/activity_calendar.html', projects=projects, events=activities, selected_project_id=selected_project_id)


@bp.route('/budget-allocation')
@login_required(role=["Admin", "Faculty"])
def budgetAllocation():
    projects = None 
    if current_user.Role.RoleName == "Faculty":
        projects = Project.query.filter_by(LeadProponentId= current_user.User[0].UserId).all()
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
    if project.Activity:
        for activity in project.Activity:
            if activity.Item:
                for item in activity.Item:
                    if item.IsPurchased==0:
                        to_be_purchased_items.append(item)
                    else:
                        purchased_items.append(item)

    if request.method == 'POST':
        if form.validate_on_submit():
            item_to_add = Item(ItemName=form.item.data,
                                Amount=form.amount.data,
                                ActivityId=form.activity.data)
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
    fillpdfs.get_form_fields(os.path.join(current_app.config["UPLOAD_FOLDER"], "e-cert (beneficiary) (FILLABLE).pdf"))
    # Get all the registered beneficiaries in the project
    beneficiaries_id = [registration.UserId for registration in Registration.query.filter_by(ProjectId=id).all()]
    registered_beneficiaries = [User.query.filter_by(UserId=beneficiary_id).first() for beneficiary_id in beneficiaries_id]
    
    # Get the project proponent's name for the certificate
    project = Project.query.filter_by(ProjectId=id).first()
    project_proponent = User.query.filter_by(UserId=project.LeadProponentId).first()
    proponent_name = project_proponent.FirstName + ' '
    if project_proponent.MiddleName:
        proponent_name += project_proponent.MiddleName[0] + '. '
    proponent_name += project_proponent.LastName

    # Get the extension program's name for the certificate
    extension_program = ExtensionProgram.query.filter_by(ExtensionProgramId=project.ExtensionProgramId).first()
    
    # Generate certificate for each beneficiary registered in the project
    for beneficiary in registered_beneficiaries:
        # Get the name of the beneficiary for the certificate
        beneficiary_name = beneficiary.FirstName + ' '
        if beneficiary.MiddleName:
            beneficiary_name += beneficiary.MiddleName[0] + '. '
        beneficiary_name += beneficiary.LastName
        data_dict = {'Text-n_L-ntAGRy': beneficiary_name,
                    'Text-Pnb29VfGWk': extension_program.Name,
                    'Date-jWSJ8ZAYJ_': datetime.utcnow(),
                    'Text-tf2etyjp87': proponent_name,
                    'Text-bcixq7yk8z': 'Jaime P. Gutierrez, Jr.'}
        
        # Get the initials of the beneficiary
        beneficiary_initials = ''.join([word[0] for word in beneficiary_name.split()])
        # Fill the pdf with the required information
        filepath = os.path.join(current_app.root_path, "media") + "\\" + extension_program.Name + "-" + beneficiary_initials + " CERTIFICATE.pdf"
        fillpdfs.write_fillable_pdf(os.path.join(current_app.config["UPLOAD_FOLDER"], "e-cert (beneficiary) (FILLABLE).pdf"), filepath, data_dict, flatten=True)

        # Upload cert pdf to cloud
        status = uploadImage(filepath, extension_program.Name + "-" + beneficiary_initials + " CERTIFICATE.pdf")

        # Get the url and file id of the uploaded certificate
        str_cert_url = None
        str_cert_file_id = None
        if status.error is not None:
            flash("Error in releasing certificates", category="error")
            return url_for('programs.viewProject', id=id)
        else:
            str_cert_url = status.url
            str_cert_file_id = status.file_id

        # Delete file from local storage after uploading to cloud
        if os.path.exists(filepath):
            os.remove(filepath)

        # Save certificate to database
        cert_to_add = Certificate(CertificateUrl=str_cert_url, 
                                CertificateFileId = str_cert_file_id, 
                                UserId=beneficiary.UserId, 
                                ProjectId=id)
        
        db.session.add(cert_to_add)
    
    db.session.commit()
    flash('Certificate is successfully released', category='success')

    return redirect(url_for('programs.programs'))


# =========================================================
# ||                      USER VIEWS                     ||
# =========================================================

@bp.route('/extension-programs')
def extensionPrograms():
    extension_programs = ExtensionProgram.query.all()
    programs = Program.query.all()
    agendas = Agenda.query.all()
    return render_template('programs/ext_programs_list.html', extension_programs=extension_programs, programs=programs, agendas=agendas)

@bp.route('/extension-program/view/<int:id>')
def extensionProgram(id):
    extension_program = ExtensionProgram.query.filter_by(ExtensionProgramId=id).first()
    projects = Project.query.filter_by(ExtensionProgramId=id).order_by(db.case(
            (Project.Status == "Ongoing", 1),
            (Project.Status == "To Be Started", 2),
            (Project.Status == "Finished", 3),
        ).asc()
    ).all()
    project_ids = [project.ProjectId for project in projects]
    events = Activity.query.filter(Activity.ProjectId.in_(project_ids),
                                    Activity.Date>datetime.utcnow().date()).order_by(Activity.Date.desc()).all()
    # Get all the faculty in each project in current extension program
    faculty_team = {}
    for project in projects:
        faculty_team.update(project.ProjectTeam)

    # Make a GET request to the API with the API key in the headers
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Process the API response data
        api_data = response.json()
        
        faculty_profile = {}
        # RETURNING SPECIFIC DATA FROM ALL FACULTIES
        for faculty in faculty_team.items():
            faculty_info = api_data['Faculties'][faculty[0]]
            faculty_profile[faculty[0]] = 'https://drive.google.com/uc?export=view&id='+faculty_info['profile_pic']
    
    return render_template('programs/extension_program.html', extension_program=extension_program, projects=projects, events=events, faculty_team=faculty_team, faculty_profile=faculty_profile)


@bp.route('/projects')
def projects():
    projects = Project.query.all()
    return render_template('programs/projects_list.html', projects=projects)

@bp.route('/projects/<int:id>')
def project(id):
    project = Project.query.filter_by(ProjectId=id).first()
    activities = Activity.query.filter_by(ProjectId=id).order_by(Activity.Date.desc()).all()
    events = [activity for activity in activities if activity.Date > datetime.utcnow().date()]
    # arrange upcoming activities in ascending order
    events.reverse()
    user_id = current_user.User[0].UserId if current_user.is_authenticated else None
    registration = Registration.query.filter_by(ProjectId=id, UserId=user_id).first()
    current_date = datetime.utcnow().date()

    # Make a GET request to the API with the API key in the headers
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Process the API response data
        api_data = response.json()
        
        faculty_profile = {project.LeadProponentId:'https://drive.google.com/uc?export=view&id='+api_data['Faculties'][project.LeadProponentId]['profile_pic']}
        # RETURNING SPECIFIC DATA FROM ALL FACULTIES
        for faculty in project.ProjectTeam.items():
            faculty_info = api_data['Faculties'][faculty[0]]
            faculty_profile[faculty[0]] = 'https://drive.google.com/uc?export=view&id='+faculty_info['profile_pic']
    return render_template('programs/project_reg.html', project=project, events=events,activities=activities, faculty_profile=faculty_profile, registration=registration, current_date=current_date)

@bp.route('/registration/<int:project_id>', methods=['POST'])
@login_required(role=["Beneficiary", "Student"])
def registration(project_id):
    user_id = current_user.User[0].UserId
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
    user_id = current_user.User[0].UserId if current_user.is_authenticated else None
    registration = Registration.query.filter_by(ProjectId=project_id, UserId=user_id).first()

    try:
        db.session.delete(registration)
        db.session.commit()
        flash('Registration is successfully canceled.', category='success')
    except:
        flash('There was an issue canceling the registration.', category='error')

    return redirect(url_for('programs.project', id=project_id))


@bp.route('/activities')
def activities():
    activities = Activity.query.order_by(Activity.Date.desc()).all()
    return render_template('programs/activities.html', activities=activities)

@bp.route('/activities/<int:id>')
def activity(id):
    activity = Activity.query.filter_by(ActivityId=id).first()
    suggestions = Activity.query.filter(Activity.Date > datetime.utcnow().date(),
                                        Activity.ProjectId==activity.ProjectId).order_by(func.random()).limit(3).all()
    current_date = datetime.utcnow().date()
    user_id = current_user.User[0].UserId if current_user.is_authenticated else None
    evaluation_id = activity.Evaluation[0].EvaluationId if activity.Evaluation else None
    bool_is_evaluation_taken = True if Response.query.filter_by(BeneficiaryId=user_id, EvaluationId=evaluation_id).first() else False
    return render_template('programs/activity.html', activity=activity, suggestions=suggestions, current_date=current_date, bool_is_evaluation_taken=bool_is_evaluation_taken)

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
        if user.User.Login.Role.RoleName == "Student":
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
