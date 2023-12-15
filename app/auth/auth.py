from app.auth import bp
from flask import render_template, url_for, request, redirect, flash, session
from .forms import BeneficiaryRegisterForm, StudentRegisterForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from ..models import Login, User, Beneficiary, Student
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
            attempted_user = Login.query.filter_by(Email=form.email.data).first()
            if attempted_user and attempted_user.RoleId == 2:
                if attempted_user.check_password_correction(attempted_password=form.password.data):
                    login_user(attempted_user, remember=True)
                    return redirect(url_for('home')) # temp route
                else:
                    flash('The password you\'ve entered is incorrect.', category='error')
            else:
                flash('The email you entered isn\'t connected to an account.', category='error')
    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

@bp.route('/beneficiary/signup', methods=['GET', 'POST'])
def beneficiarySignup():
    current_url_path = request.path
    form = BeneficiaryRegisterForm()    
    current_url_path = request.path
    if request.method == "POST":
        if form.validate_on_submit():
            str_user_id = createUser(form, 2)
            beneficiary_to_create = Beneficiary(BeneficiaryId = str_user_id)
            db.session.add(beneficiary_to_create)
            db.session.commit()
            return redirect(url_for('auth.beneficiaryLogin'))
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
    return render_template('auth/beneficiary_signup.html', form=form, current_url_path=current_url_path)

@bp.route('/student', methods=['GET', 'POST'])
def studentLogin():
    current_url_path = request.path
    # Prevents logged in users from accessing the page
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    
    form = LoginForm()

    if request.method == "POST":
        if form.validate_on_submit():
            attempted_user = Login.query.filter_by(Email=form.email.data).first()
            if attempted_user and attempted_user.RoleId == 3:
                if attempted_user.check_password_correction(attempted_password=form.password.data):
                    login_user(attempted_user, remember=True)
                    return redirect(url_for('home')) # temp route
                else:
                    flash('The password you\'ve entered is incorrect.', category='error')
            else:
                flash('The email you entered isn\'t connected to an account.', category='error')

    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

@bp.route('/student/signup', methods=['GET', 'POST'])
def studentSignup():
    current_url_path = request.path
    form = StudentRegisterForm()    
    current_url_path = request.path
    if request.method == "POST":
        if form.validate_on_submit():
            str_user_id = createUser(form, 3)
            student_to_create = Student(StudentId = str_user_id,
                                        SkillsInterest = form.skills_interest.data)
            db.session.add(student_to_create)
            db.session.commit()
            return redirect(url_for('auth.studentLogin'))
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
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
            attempted_user = Login.query.filter_by(Email=form.email.data).first()
            if attempted_user and attempted_user.RoleId == 4:
                if attempted_user.check_password_correction(attempted_password=form.password.data):
                    login_user(attempted_user, remember=True)
                    return redirect(url_for('programs.programs'))
                else:
                    flash('The password you\'ve entered is incorrect.', category='error')
            else:
                flash('The email you entered isn\'t connected to an account.', category='error')
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
