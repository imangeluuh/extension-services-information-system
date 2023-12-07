from flask import current_app
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, DateField, SelectField, SubmitField, TextAreaField, HiddenField, TimeField, FormField, SelectMultipleField
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileField, FileAllowed
from ..models import Agenda, Program, Collaborator, Speaker, Login
import requests

faculty_names = []
try:
    api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJrZXkiOiJjNmYzMDFjZTg3OWE0M2YwOWMyZWYyZjUzODk1YjY1OSJ9.L0Xs2-s2hAhnOuUEyciVLPHOHDtH3OAeC_UgoMP3X64'

    access = requests.get(f"https://pupqcfis-com.onrender.com/api/all/faculty_data?token={api_key}")

    data = access.json()
    for faculty in data['FIS_data'][0]['faculty']:
        faculty_names.append((list(faculty.keys())[1], faculty['name']))
except:
    # Sample only
    faculty_names = [
        ('1', 'Monika Shin'),
        ('2', 'John Doe'),
        ('Alice Johnson', 'Alice Johnson'),
        ('Michael Smith', 'Michael Smith'),
        ('Emily Davis', 'Emily Davis'),
        ('Daniel Brown', 'Daniel Brown'),
        ('Sophia Martinez', 'Sophia Martinez'),
        ('William Taylor', 'William Taylor'),
        ('Olivia Miller', 'Olivia Miller'),
        ('Ethan Anderson', 'Ethan Anderson'),
        ('Grace White', 'Grace White'),
        ('Matthew Lee', 'Matthew Lee'),
        ('Ava Robinson', 'Ava Robinson'),
        ('Jacob Wright', 'Jacob Wright'),
        ('Lily Thomas', 'Lily Thomas'),
        ('Christopher Hall', 'Christopher Hall'),
        ('Emma Turner', 'Emma Turner'),
        ('Alexander Carter', 'Alexander Carter'),
        ('Chloe Harris', 'Chloe Harris'),
        ('Benjamin Clark', 'Benjamin Clark'),
    ]

class ProgramForm(FlaskForm):
    program_name = StringField('Extension Program Name', validators=[DataRequired()])
    rationale = TextAreaField('Rationale', validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    agenda = SelectField('Agenda', validators=[DataRequired()])
    program = SelectField('Program', validators=[DataRequired()])
    submit= SubmitField('Save Program')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        with current_app.app_context():
            self.agenda.choices = [(agenda.AgendaId, agenda.AgendaName) for agenda in Agenda.query.all()]
            self.program.choices = [(program.ProgramId, program.ProgramName) for program in Program.query.all()]
            
class ProjectForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    implementer = StringField("Implementer", default="Polytechnic Unversity of the Philippines, Quezon City  Branch", validators=[DataRequired()])
    collaborator = SelectField('Collaborator', validators=[DataRequired()])
    project_team = SelectMultipleField('Project Team', choices=faculty_names, validators=[DataRequired()])
    target_group = StringField("Target Group", validators=[DataRequired()])
    project_type = SelectField("Project Type", choices=[('Need-Based', 'Need-Based'),
                                                            ('Quick Response', 'Quick Response'),
                                                            ('Other Related Activities/Collaboration', 'Other Related Activities/Collaboration')],
                                                            validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    proposed_budget = StringField('Proposed Budget', validators=[DataRequired()])
    approved_budget = StringField('Approved Budget', validators=[DataRequired()])
    fund_type = SelectField('Fund Type', choices=[('Internal', 'Internal'),
                                                ('External', 'External')],
                                                validators=[DataRequired()])
    impact_statement = CKEditorField("Impact Statement", validators=[DataRequired()])
    objectives = CKEditorField("Objective of the Project", validators=[DataRequired()])
    status = SelectField('Status', choices=[('To be started', 'To be started'),
                                        ('Ongoing', 'Ongoing'),
                                        ('Finished', 'Finished')],
                                        validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    project_proposal = FileField('Project Proposal', validators=[FileAllowed(['docx', 'pdf', 'docs'])])
    extension_program = HiddenField()
    submit = SubmitField("Save Project")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        with current_app.app_context():
            self.collaborator.choices = [(collaborator.CollaboratorId, collaborator.Organization) for collaborator in Collaborator.query.all()]


class ActivityForm(FlaskForm):
    activity_name = StringField("Activity Name", validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()])
    start_time = TimeField("Start Time", format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    activity_description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    speaker = SelectMultipleField('Speaker', choices=faculty_names, validators=[DataRequired()])
    save = SubmitField("Save Activity") 

class CombinedForm(FlaskForm):
    extension_program = FormField(ProgramForm)
    project = FormField(ProjectForm)
    activity = FormField(ActivityForm)
    submit = SubmitField("Submit") 