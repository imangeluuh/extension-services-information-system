from flask import current_app
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField, TextAreaField, IntegerField, HiddenField, SelectMultipleField, widgets
from wtforms.validators import Length, Email, DataRequired, Optional
from flask_wtf.file import FileField, FileAllowed
from ..models import Project

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign in')

class ProjectForm(FlaskForm):
    project_name = StringField("Project Name", validators=[DataRequired()])
    lead_proponent = StringField("Lead Proponent", validators=[DataRequired()])
    status = StringField('Status', validators=[DataRequired()])
    project_type = SelectField("Project Type", choices=[('Need-Based', 'Need-Based'),
                                                            ('Quick Response', 'Quick Response'),
                                                            ('Other Related Activities/Collaboration', 'Other Related Activities/Collaboration')],
                                                            validators=[DataRequired()])
    rationale = TextAreaField("Rationale / Description of the Project", validators=[DataRequired()])
    objectives = TextAreaField("Objective of the Project", validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    start_date = DateField("Start Date", validators=[Optional()])
    num_of_beneficiaries = IntegerField("Specific Numbers of Target Beneficiaries", validators=[Optional()])
    beneficiaries_classifications = StringField("Target Beneficiaries Classifications", validators=[Optional()])
    project_scope = TextAreaField("Scope of Project", validators=[DataRequired()])
    extension_program = HiddenField()
    submit = SubmitField("Save Project") 

class CollaboratorForm(FlaskForm):
    organization = StringField("Organization", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    signed_moa = FileField("Signed MOU/MOA", validators=[FileAllowed(['jpg', 'png', 'jpeg', 'pdf', 'docs', 'docx'])])

class SpeakerForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    middle_name = StringField("Middle Name")
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    contact_details = StringField("Contact Details", validators=[DataRequired()])


