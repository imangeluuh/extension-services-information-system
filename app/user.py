from flask import render_template, url_for, request, redirect, flash, current_app, Blueprint
from flask_login import current_user
from .models import Certificate, Registration, Project


bp = Blueprint('user', __name__, template_folder="templates", static_folder="static", static_url_path='static')

@bp.route('/profile')
def profile():
    # Get all projects current user are registered
    projects_id = [registration.ProjectId for registration in Registration.query.filter_by(UserId=current_user.UserId).all()]
    user_projects = [Project.query.filter_by(ProjectId=project_id).first() for project_id in projects_id]
    user_certificates = Certificate.query.filter_by(UserId=current_user.UserId).all()
    
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
    return render_template('user_profile.html', projects=projects)
