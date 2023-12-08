from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, Regexp, Optional
from ..models import Login
from datetime import datetime, timedelta

class BeneficiaryRegisterForm(FlaskForm):
    first_name = StringField(label="First Name", validators=[DataRequired()])
    middle_name = StringField(label="Middle Name")
    last_name = StringField(label="Last Name", validators=[DataRequired()])
    contact_details = StringField(label="Contact Details", validators=[DataRequired(), Regexp(r'^09\d{9}$', message="Please match the contact number format. 09123456789- 11 numbers only")])
    birthdate = DateField(label="Date of Birth",  validators=[DataRequired()])
    gender = SelectField(label="Gender", choices=[('Female', 'Female'),
        ('Male', 'Male'),
        ('Nonbinary', 'Nonbinary')], validators=[DataRequired()])
    address = StringField(label="Home Address",  validators=[DataRequired()])
    email = StringField(label="Email", validators=[Email(), DataRequired()])
    password1 = PasswordField(label="Password", validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label="Confirm Password", validators=[EqualTo('password1'),  DataRequired()])
    signup = SubmitField(label='Sign up')

    def validate_email(self, email):
        existing_participant_email = Login.query.filter_by(Email=email.data).first()

        if existing_participant_email:
            raise ValidationError("Email already exists. Please choose a different one.")
        
    def validate_birthdate(self, birthdate):
        today = datetime.today().date()
        ten_years_ago = today - timedelta(days=365 * 10)

        if birthdate.data > ten_years_ago:
            raise ValidationError("Invalid date of birth")
        
class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[Email(), DataRequired()])
    password = PasswordField(label='Password', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='Sign in')

class StudentRegisterForm(FlaskForm):
    first_name = StringField(label="First Name", validators=[DataRequired()])
    middle_name = StringField(label="Middle Name")
    last_name = StringField(label="Last Name", validators=[DataRequired()])
    contact_details = StringField(label="Contact Details", validators=[DataRequired(), Regexp(r'^09\d{9}$', message="Please match the contact number format. 09123456789- 11 numbers only")])
    birthdate = DateField(label="Date of Birth",  validators=[DataRequired()])
    gender = SelectField(label="Gender", choices=[('Female', 'Female'),
        ('Male', 'Male'),
        ('Nonbinary', 'Nonbinary')], validators=[DataRequired()])
    skills_interest = TextAreaField(label="Skills/Interest", validators=[Optional()])
    address = StringField(label="Home Address",  validators=[DataRequired()])
    email = StringField(label="Email", validators=[Email(), DataRequired()])
    password1 = PasswordField(label="Password", validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label="Confirm Password", validators=[EqualTo('password1'),  DataRequired()])
    signup = SubmitField(label='Sign up')

    def validate_email(self, email):
        existing_participant_email = Login.query.filter_by(Email=email.data).first()

        if existing_participant_email:
            raise ValidationError("Email already exists. Please choose a different one.")
        
    def validate_birthdate(self, birthdate):
        today = datetime.today().date()
        ten_years_ago = today - timedelta(days=365 * 10)

        if birthdate.data > ten_years_ago:
            raise ValidationError("Invalid date of birth")
        
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')