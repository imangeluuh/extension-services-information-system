from app.admin import bp
from flask import render_template, url_for, request, redirect, flash, session
from flask_login import current_user, login_user, login_required, logout_user
from .forms import LoginForm
from ..models import Login, Beneficiary, Project, Student, Registration, User, Faculty, ExtensionProgram
from ..Api.resources import AdminLoginApi
from ..decorators.decorators import login_required
from app import db, api
from ..store import uploadImage
from ..email import sendEmail
from werkzeug.utils import secure_filename
import requests


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
            attempted_user = Login.query.filter_by(Email=form.email.data).first()
            if attempted_user and attempted_user.RoleId == 1: 
                if attempted_user.check_password_correction(attempted_password=form.password.data):
                    login_user(attempted_user, remember=True)
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
    users = Student.query.all()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path)

@bp.route('/faculty')
@login_required(role=["Admin"])
def faculty():
    users = Faculty.query.all()
    current_url_path = request.path
    return render_template('admin/users.html', users=users,current_url_path=current_url_path)

@bp.route('/beneficiaries/<string:id>')
@login_required(role=["Admin"])
def viewUser(id):
    user = User.query.filter_by(UserId=id).first()
    if user.Login.Role.RoleName in ["Beneficiary", "Student"]:
        user_projects = (
        Project.query
        .join(Registration, Registration.ProjectId == Project.ProjectId)
        .join(User, User.UserId == Registration.UserId)
        .filter(User.UserId == id)
        .all()
        )
    else:
        user_projects = Project.query.filter_by(LeadProponentId=user.UserId)
    return render_template('admin/view_user.html', user=user, user_projects=user_projects)
    
@bp.route('/dashboard')
@login_required(role=["Admin"])
def dashboard():
    programs = ExtensionProgram.query.all()
    programs_participants = []
    for program in programs:
        participants = [program.Name, 0]
        for project in program.Projects:
            registered = project.Registration
            participants[1] += len(registered)
        programs_participants.append(participants)

    return render_template('admin/dashboard.html', programs_participants=programs_participants)
    