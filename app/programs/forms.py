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
    url = 'https://pupqcfis-com.onrender.com/api/all/Faculty_Profile'

    api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJrZXkiOiIzM2Y0ZWI4NWNjNDQ0MTQzOWFkMzMwYWUzMzJiNmYwYyJ9.5pjwXdaIIZf6Jm9zb26YueCPQhj6Tc18bbZ0vnX4S9M'

    # Set up headers with the API key in the 'API Key' authorization header
    headers = {
        'Authorization': 'API Key',
        'token': api_key,  # 'token' key with the API key value
        'Content-Type': 'application/json'  # Adjust content type as needed
    }

    # Make a GET request to the API with the API key in the headers
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Process the API response data
        api_data = response.json()
        
        # RETURNING SPECIFIC DATA FROM ALL FACULTIES
        
        # Extracting faculty_account_ids into a list
        faculty_account_ids = list(api_data['Faculties'].keys())

        # Fetching Specific data for each faculty
        for faculty_id in faculty_account_ids:
            faculty_info = api_data['Faculties'][faculty_id]
            faculty_name = faculty_info['name']
            faculty_names.append((faculty_id, faculty_name))

except:
    # Sample only
    faculty_names = [
        ('1', 'Monika Shin'),
        ('2', 'John Doe'),
        ('3', 'Alice Johnson'),
        ('4', 'Michael Smith'),
        ('5', 'Emily Davis'),
        ('6', 'Daniel Brown'),
        ('7', 'Sophia Martinez'),
        ('8', 'William Taylor'),
        ('9', 'Olivia Miller'),
        ('10', 'Ethan Anderson'),
        ('11', 'Grace White'),
        ('12', 'Matthew Lee'),
        ('13', 'Ava Robinson'),
        ('14', 'Jacob Wright'),
        ('15', 'Lily Thomas'),
        ('16', 'Christopher Hall'),
        ('17', 'Emma Turner'),
        ('18', 'Alexander Carter'),
        ('19', 'Chloe Harris'),
        ('20', 'Benjamin Clark'),
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