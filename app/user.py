from flask import render_template, url_for, request, redirect, flash, current_app, Blueprint
from flask_login import current_user
from .models import Certificate, Registration, Project, Beneficiary
from datetime import datetime
from .decorators.decorators import login_required
from app import db

bp = Blueprint('user', __name__, template_folder="templates", static_folder="static", static_url_path='static')

@bp.route('/profile')
@login_required()
def profile():
    # Get all projects current user are registered
    if current_user.RoleId in [2, 3]:
        projects_id = [registration.ProjectId for registration in Registration.query.filter_by(UserId=current_user.UserId).all()]
        user_projects = [Project.query.filter_by(ProjectId=project_id).first() for project_id in projects_id]
    else: 
        user_projects = Project.query.filter_by(LeadProponentId=current_user.UserId).all()
    user_certificates = Certificate.query.filter_by(UserId=current_user.UserId).all()
    current_date = datetime.utcnow().date()
    
    # Create a list of project and certificate
    projects = []
    for project in user_projects:
        # Initialize project list
        projects.append([project, None])
        for certificate in user_certificates:
            if project.ProjectId == certificate.ProjectId:
                # Modify the last appended item
                projects[-1][1] = certificate
                break
    return render_template('user_profile.html', projects=projects, current_date=current_date)

@bp.route('/change-password', methods=["GET", "POST"])
@login_required(role=["Beneficiary"])
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
