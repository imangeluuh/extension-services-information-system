from app.auth import bp
from flask import render_template, url_for, request, redirect, flash, session, current_app
from .forms import RegisterForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from ..models import User, Beneficiary, Faculty, Student
from app import db
from flask_login import login_user, logout_user, current_user
from datetime import timedelta
from werkzeug.security import check_password_hash
import uuid, datetime
from .email import sendPasswordResetEmail, requestAccount

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
        return redirect(url_for('home')) 
    form = LoginForm()

    if request.method == "POST":
        if form.validate_on_submit():
            attempted_user = Beneficiary.query.filter_by(Email=form.email.data).first()
            if attempted_user and attempted_user.User[0].RoleId == 2:
                if attempted_user.check_password_correction(attempted_password=form.password.data):
                    isRemember = True if request.form.get('remember') else False
                    login_user(attempted_user.User[0], remember=isRemember)
                    return redirect(url_for('home'))
                else:
                    flash('The password you\'ve entered is incorrect.', category='error')
            else:
                flash('The email you entered isn\'t connected to an account.', category='error')
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

@bp.route('/beneficiary/signup', methods=['GET', 'POST'])
def beneficiarySignup():
    current_url_path = request.path
    form = RegisterForm()    
    current_url_path = request.path
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                beneficiary_to_create = Beneficiary(FirstName=form.first_name.data,
                                                    MiddleName=form.middle_name.data,
                                                    LastName=form.last_name.data,
                                                    Email=form.email.data,
                                                    password_hash=form.password1.data,
                                                    Gender=form.gender.data,
                                                    DateOfBirth=form.birthdate.data,
                                                    PlaceOfBirth=form.birthplace.data,
                                                    ResidentialAddress=form.address.data,
                                                    MobileNumber=form.contact_details.data)
                db.session.add(beneficiary_to_create)
                # Get the beneficiary id
                db.session.flush()
                beneficiary_id = beneficiary_to_create.BeneficiaryId
                user_to_create = User(UserId=uuid.uuid4(),
                                    RoleId=2,
                                    BeneficiaryId=beneficiary_id)
                db.session.add(user_to_create)
                db.session.commit()
                flash('You have successfully created your account!', category='success')
            except Exception as e:
                print(e)
                flash('There was an issue creating your account. Please try again later.', category='error')
            return redirect(url_for('auth.beneficiaryLogin'))
    return render_template('auth/signup.html', form=form, current_url_path=current_url_path)

@bp.route('/student', methods=['GET', 'POST'])
def studentLogin():
    current_url_path = request.path
    # Prevents logged in users from accessing the page
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    
    form = LoginForm()

    if request.method == "POST":
        if form.validate_on_submit():
            attempted_user = Student.query.filter_by(Email=form.email.data).first()
            if attempted_user: # Account existing in SPS
                if not attempted_user.User:  # if SPS account not yet registered in ESISUser
                    # Create row for SPS account in EISUser
                    account_to_create = User(UserId=uuid.uuid4(),
                                            RoleId=4,
                                            FacultyId=attempted_user.FacultyId)
                    db.session.add(account_to_create)
                    db.session.commit()
                # Login to system
                if check_password_hash(attempted_user.Password, form.password.data):
                    isRemember = True if request.form.get('remember') else False
                    login_user(attempted_user.User[0], remember=isRemember)
                    return redirect(url_for('home'))
                else:
                    flash('The password you\'ve entered is incorrect.', category='error')
            else:
                flash('The email you entered isn\'t connected to an account.', category='error')
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

# @bp.route('/student/signup', methods=['GET', 'POST'])
# def studentSignup():
#     current_url_path = request.path
#     form = RegisterForm()    
#     current_url_path = request.path
#     if request.method == "POST":
#         if form.validate_on_submit():
#             try:
#                 # createUser(form, 3)
#                 # db.session.commit()   
#                 flash('You have successfully created your account!', category='success')
#             except Exception as e:
#                 print(e)
#                 flash('There was an issue creating your account. Please try again later.', category='error')
#             return redirect(url_for('auth.studentLogin'))
#     return render_template('auth/signup.html', form=form, current_url_path=current_url_path)

@bp.route('/faculty', methods=['GET', 'POST'])
def facultyLogin():
    # Prevents logged in users from accessing the page
    current_url_path = request.path
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Find if the attempted user is existing in FIS
            attempted_user = Faculty.query.filter_by(Email=form.email.data).first()
            if attempted_user: # Account existing in FIS
                if not attempted_user.User:  # if FIS account not yet registered in ESISUser
                    # Create row for FIS account in EISUser
                    account_to_create = User(UserId=uuid.uuid4(),
                                            RoleId=4,
                                            FacultyId=attempted_user.FacultyId)
                    db.session.add(account_to_create)
                    db.session.commit()
                # Login to system
                if check_password_hash(attempted_user.Password, form.password.data):
                    isRemember = True if request.form.get('remember') else False
                    login_user(attempted_user.User[0], remember=isRemember)
                    return redirect(url_for('programs.programs'))
                else:
                    flash('The password you\'ve entered is incorrect.', category='error')
            else:
                flash('The email you entered isn\'t connected to an account.', category='error')
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
    return render_template('auth/login.html', form=form, current_url_path=current_url_path)

# @bp.route('/faculty/signup', methods=['GET', 'POST'])
# def facultySignup():
#     if request.method == "POST":
#         email = request.form.get('email')
#         requestAccount(email)
#         flash('We have received your account request.  We\'re reviewing your account request and you\'ll hear back from us soon via email. Please check your inbox (including spam folder) for further instructions.', category='info')
#     return render_template('auth/faculty_signup.html')
        
@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home')) # temp route

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def resetPasswordRequest():
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    form = ResetPasswordRequestForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = Beneficiary.query.filter_by(Email=form.email.data).first()
            if user:
                sendPasswordResetEmail(user)
                flash('Check your email for the instructions to reset your password', category='info')
                return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def resetPassword(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Temp route
    user = User.verify_reset_password_token(token)
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

# def createUser(form, role):
#     # Generate student/faculty/beneficiary number
#     last_user = User.query.filter_by(RoleId=role).order_by(User.UserNumber.desc()).first()
#     middle_digits = '00001'
#     if last_user:
#         last_user_number = last_user.UserNumber # Get the last student/faculty/beneficiary number
#         middle_digits = int(last_user_number[5:10]) # Extract characters from index 5 to 9 (inclusive)
#         middle_digits = str(middle_digits + 1).zfill(5) # Increment and zero-pad to 5 digits
#     year = str(datetime.datetime.now().year ) # Get current year
#     last_chars = "-CM-1"
#     if role == 3:
#         last_chars = "-CM-0"
#     user_number = year+"-"+middle_digits+last_chars
#     user_to_create = User(UserId=uuid.uuid4(),
#                             UserNumber = user_number,
#                             FirstName=form.first_name.data,
#                             MiddleName=form.middle_name.data,
#                             LastName=form.last_name.data,
#                             Email=form.email.data,
#                             password_hash=form.password1.data,
#                             RoleId=role,
#                             MobileNumber=form.contact_details.data,
#                             DateOfBirth=form.birthdate.data,
#                             PlaceOfBirth=form.birthplace.data,
#                             Gender=form.gender.data,
#                             ResidentialAddress=form.address.data)
#     db.session.add(user_to_create)
#     db.session.commit()
