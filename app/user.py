from flask import render_template, url_for, request, redirect, flash, current_app, Blueprint
from flask_login import current_user, login_required
from .models import Certificate, Registration, Project, Beneficiary, ExtensionProgram, Certificate, ProjectTeam, User, Faculty
from datetime import datetime
from sqlalchemy import func
# from .decorators.decorators import login_required
from app import db

bp = Blueprint('user', __name__, template_folder="templates", static_folder="static", static_url_path='static')

@bp.route('/profile')
@login_required
def profile():
    return render_template('user_profile.html')

@bp.route('/my-projects')
@login_required
def myProjects():
    projects = None
    team_projects = None
    current_date = datetime.now().date()
    # Get all projects current user are registered
    if current_user.RoleId in [2, 3]:
        projects = db.session.query(
                Registration.RegistrationId
                , Project.ProjectId
                , Project.Title
                , Project.StartDate
                , Project.EndDate
                , ExtensionProgram.Name
                , Certificate.CertificateUrl
            ).join(Project, Registration.ProjectId == Project.ProjectId
            ).join(ExtensionProgram, Project.ExtensionProgramId == ExtensionProgram.ExtensionProgramId
            ).outerjoin(Certificate, Certificate.ProjectId == Project.ProjectId
            ).filter(
                Registration.UserId == current_user.UserId,
                Project.IsArchived == False,
                ExtensionProgram.IsArchived == False,
            ).all()
    else: 
        projects = db.session.query(
                Project.ProjectId
                , Project.Title
                , Project.StartDate
                , Project.EndDate
                , ExtensionProgram.Name
            ).join(ExtensionProgram, Project.ExtensionProgramId == ExtensionProgram.ExtensionProgramId
            ).filter(
                Project.LeadProponentId == current_user.UserId,
                Project.IsArchived == False,
                ExtensionProgram.IsArchived == False,
            ).all()
        
        team_projects = db.session.query(
                ProjectTeam.ProjectId
                , Project.Title
                , Project.StartDate
                , Project.EndDate
                , ExtensionProgram.Name
                , func.concat(Faculty.FirstName, ' ', Faculty.LastName).label('LeadProponent')
            ).join(Project, ProjectTeam.ProjectId == Project.ProjectId
            ).join(ExtensionProgram, Project.ExtensionProgramId == ExtensionProgram.ExtensionProgramId
            ).join(User, Project.LeadProponentId == User.UserId
            ).join(Faculty, User.FacultyId == Faculty.FacultyId
            ).filter(
                ProjectTeam.FacultyId == current_user.FacultyId,
                Project.LeadProponentId != current_user.UserId,
                Project.IsArchived == False,
                ExtensionProgram.IsArchived == False,
            ).all()

    return render_template('user_projects.html', projects=projects, team_projects=team_projects, current_date=current_date)

@bp.route('/change-password', methods=["GET", "POST"])
@login_required
# @login_required(role=["Beneficiary"])
def changePassword():
    if request.method == "POST":
        password = request.form.get('password')
        new_password = request.form.get('new-password')
        confirm_password = request.form.get('confirm-password')

        beneficiary = Beneficiary.query.filter_by(BeneficiaryId=current_user.BeneficiaryId).first()
        if beneficiary:
            # Check if the input current password matched the password of the beneficiary
            if beneficiary.check_password_correction(attempted_password=password):
                if new_password == confirm_password:
                    if password == new_password:
                        flash("New password must be different from current password.", category='error')
                    else:
                        beneficiary.password_hash = new_password
                        db.session.commit()
                        flash("Your password has been changed successfully!", category='success')
                else:
                    flash("New password does not match.", category='error')    
            else:
                flash("Incorrect password", category='error')
    return render_template('change_password.html')
