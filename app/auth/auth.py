from app.auth import bp
from flask import render_template, url_for, request, redirect, flash, session
from .forms import BeneficiaryRegisterForm, StudentRegisterForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from ..models import Login, User
from app import db, api
from ..Api.resources import BeneficiaryLoginApi, StudentLoginApi, FacultyLoginApi, BeneficiaryRegisterApi, StudentRegisterApi
from flask_login import login_user, logout_user, current_user
from datetime import timedelta
import uuid
import requests, json
from .email import sendPasswordResetEmail

lockout_duration = timedelta(minutes=1)
headers = {"Content-Type": "application/json"}

@bp.route('/')
def login():
    current_url_path = request.path
    return render_template('auth/login.html', current_url_path=current_url_path)

@bp.route('/beneficiary', methods=['GET', 'POST'])
# @limiter.limit('5 per day')
# @limiter.limit("3 per day", key_func=lambda: request.method == "POST")
def beneficiaryLogin():
    # Prevents logged in users from accessing the page
    current_url_path = request.path
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            data={'Email': form.email.data,
                'Password': form.password.data}
            response = requests.post(api.url_for(BeneficiaryLoginApi, _external=True), json=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                session['access_token'] = response_data.get('access_token')
                user = Login.query.filter_by(Email=data['Email']).first()
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                try:
                    response_data = response.json()
                    flash(response_data.get('error'), category='danger')
                except json.JSONDecodeError:
                    print(response)
    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

@bp.route('/beneficiary/signup', methods=['GET', 'POST'])
def beneficiarySignup():
    current_url_path = request.path
    form = BeneficiaryRegisterForm()    
    current_url_path = request.path
    if request.method == "POST":
        if form.validate_on_submit():
            data={"Email": form.email.data,
                "Password": form.password1.data,
                "FirstName": form.first_name.data,
                "MiddleName": form.middle_name.data,
                "LastName": form.last_name.data,
                "ContactDetails": form.contact_details.data,
                "Birthdate": form.birthdate.data.strftime("%Y-%m-%d"),
                "Gender": form.gender.data,
                "Address": form.address.data,
                "SkillsInterest": ""}
            response = requests.post(api.url_for(BeneficiaryRegisterApi, _external=True), json=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                flash(response_data.get('success'))
                return redirect(url_for('auth.beneficiaryLogin'))
            else:
                try:
                    response_data = response.json()
                    flash(response_data.get('error'))
                except json.JSONDecodeError:
                    print(response)
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg)
    return render_template('auth/beneficiary_signup.html', form=form, current_url_path=current_url_path)

@bp.route('/student', methods=['GET', 'POST'])
def studentLogin():
    # Prevents logged in users from accessing the page
    current_url_path = request.path
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            data={'Email': form.email.data,
                'Password': form.password.data}
            response = requests.post(api.url_for(StudentLoginApi, _external=True), json=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                session['access_token'] = response_data.get('access_token')
                user = Login.query.filter_by(Email=data['Email']).first()
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                try:
                    response_data = response.json()
                    flash(response_data.get('error'))
                except json.JSONDecodeError:
                    print(response)
    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

@bp.route('/student/signup', methods=['GET', 'POST'])
def studentSignup():
    current_url_path = request.path
    form = StudentRegisterForm()    
    current_url_path = request.path
    if request.method == "POST":
        if form.validate_on_submit():
            data={"Email": form.email.data,
                "Password": form.password1.data,
                "FirstName": form.first_name.data,
                "MiddleName": form.middle_name.data,
                "LastName": form.last_name.data,
                "ContactDetails": form.contact_details.data,
                "Birthdate": form.birthdate.data.strftime("%Y-%m-%d"),
                "Gender": form.gender.data,
                "Address": form.address.data,
                "SkillsInterest": form.skills_interest.data}
            response = requests.post(api.url_for(StudentRegisterApi, _external=True), json=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                flash(response_data.get('success'))
                return redirect(url_for('auth.studentLogin'))
            else:
                try:
                    response_data = response.json()
                    flash(response_data.get('error'))
                except json.JSONDecodeError:
                    print(response)
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg)
    return render_template('auth/student_signup.html', form=form, current_url_path=current_url_path)

@bp.route('/faculty', methods=['GET', 'POST'])
def facultyLogin():
    # Prevents logged in users from accessing the page
    current_url_path = request.path
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            data={'Email': form.email.data,
                'Password': form.password.data}
            response = requests.post(api.url_for(FacultyLoginApi, _external=True), json=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                session['access_token'] = response_data.get('access_token')
                user = Login.query.filter_by(Email=data['Email']).first()
                login_user(user, remember=True)
                return redirect(url_for('admin.programs'))
            else:
                try:
                    response_data = response.json()
                    flash(response_data.get('error'))
                except json.JSONDecodeError:
                    print(response)
    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home')) # temp route

def createUser(form, role):
    str_login_uuid = uuid.uuid4()
    user_login = Login(LoginId=str_login_uuid,
                        Email=form.email.data,
                        password_hash=form.password1.data,
                        RoleId=role)
    str_user_id = uuid.uuid4()
    user_to_create = User(UserId=str_user_id,
                            FirstName=form.first_name.data,
                            MiddleName=form.middle_name.data,
                            LastName=form.last_name.data,
                            ContactDetails=form.contact_details.data,
                            Birthdate=form.birthdate.data,
                            Gender=form.gender.data,
                            Address=form.address.data,
                            LoginId=str_login_uuid)
    db.session.add(user_login)
    db.session.add(user_to_create)
    db.session.commit()
    return str_user_id

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def resetPasswordRequest():
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    form = ResetPasswordRequestForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = Login.query.filter_by(Email=form.email.data).first()
            if user:
                sendPasswordResetEmail(user)
                flash('Check your email for the instructions to reset your password', category='info')
                return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def resetPassword(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    user = Login.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('home'))
    form = ResetPasswordForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user.password_hash = form.password.data
            db.session.commit()
            flash('Your password has been reset.', category='success')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
