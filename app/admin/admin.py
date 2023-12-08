from app.admin import bp
from flask import render_template, url_for, request, redirect, flash, session
from flask_login import current_user, login_user, login_required, logout_user
from .forms import LoginForm
from ..models import Login, Beneficiary, Project, Student, Registration, User, Faculty
from ..Api.resources import AdminLoginApi
from ..decorators.decorators import login_required
from app import db, api
from ..store import uploadImage
from ..email import sendEmail
from werkzeug.utils import secure_filename
import requests
from ..programs.programs import fetch_activities


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
        return redirect(url_for('programs.programs'))  # Temp route
    
    if request.method == "POST":
        if form.validate_on_submit():
            data={'Email': form.email.data,
                'Password': form.password.data}
            response = requests.post(api.url_for(AdminLoginApi, _external=True), json=data)
            if response.status_code == 200:
                response_data = response.json()
                session['access_token'] = response_data.get('access_token')
                instance_user = Login()
                instance_user.set_user_data(login_data=response_data['admin'])
                login_user(instance_user, remember=True)
                return redirect(url_for('programs.programs')) # Temp route
            else:
                response_data = response.json()
                flash(response_data.get('error'), category='error')
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