from flask import current_app
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, DateField, SelectField, SubmitField, TextAreaField, HiddenField, TimeField, FormField, SelectMultipleField, DecimalField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed
from ..models import Agenda, Collaborator, Location, User, Faculty, Course, Alumni
from app import cache
import requests

@cache.cached(timeout=1800, key_prefix='getFacultyNames')
def getFacultyNames():
    faculty_names = []
    url = current_app.config['API_URL']
    api_key = current_app.config['API_KEY']
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
        
        # Extracting faculty_account_ids into a list
        faculty_account_ids = list(api_data['Faculties'].keys())

        # Fetching name for each faculty
        for faculty_id in faculty_account_ids:
            faculty_info = api_data['Faculties'][faculty_id]
            faculty_name = faculty_info['name']
            faculty_names.append((faculty_id, faculty_name))
    return faculty_names

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
            self.program.choices = [(program.CourseId, program.Name) for program in Course.query.all()]
            
class ProjectForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    implementer = StringField("Implementer", default="Polytechnic Unversity of the Philippines, Quezon City  Branch", validators=[DataRequired()])
    collaborator = SelectField('Collaborator', validators=[DataRequired()])
    project_team = SelectMultipleField('Project Team', validators=[DataRequired()])
    target_group = StringField("Target Group", validators=[DataRequired()])
    project_type = SelectField("Project Type", choices=[('Need-Based', 'Need-Based'),
                                                            ('Quick Response', 'Quick Response'),
                                                            ('Other Related Activities/Collaboration', 'Other Related Activities/Collaboration')],
                                                            validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    impact_statement = CKEditorField("Impact Statement", validators=[DataRequired()])
    objectives = CKEditorField("Objective of the Project", validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    project_proposal = FileField('Project Proposal', validators=[FileAllowed(['docx', 'pdf', 'docs'])])
    extension_program = HiddenField()
    submit = SubmitField("Save Project")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        with current_app.app_context():
            self.collaborator.choices = [(collaborator.CollaboratorId, collaborator.Organization) for collaborator in Collaborator.query.all()]
            self.project_team.choices = [(str(faculty.FacultyId), faculty.FirstName + ' ' + faculty.LastName) for faculty in Faculty.query.all()]

class ActivityForm(FlaskForm):
    activity_name = StringField("Activity Name", validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()])
    start_time = TimeField("Start Time", format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])
    location = SelectField('Location', validators=[DataRequired()])
    activity_description =  CKEditorField("Description", validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    speaker = SelectMultipleField('Speaker', validators=[DataRequired()])
    save = SubmitField("Save Activity") 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        with current_app.app_context():
            self.location.choices = [(location.LocationId, location.LocationName) for location in Location.query.all()]
            speakers = [(str(faculty.FacultyId), faculty.FirstName + ' ' + faculty.LastName + ' - Faculty') for faculty in Faculty.query.all()]
            speakers += [(str(alumni.id), alumni.first_name + ' ' + alumni.last_name + ' - Alumni') for alumni in Alumni.query.filter_by(role="alumni").all()]
            self.speaker.choices = speakers
            
class CombinedForm(FlaskForm):
    extension_program = FormField(ProgramForm)
    project = FormField(ProjectForm)
    activity = FormField(ActivityForm)
    submit = SubmitField("Submit") 

class ItemForm(FlaskForm):
    item = StringField("Item", validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired()])
    date = DateField("Date Purchased")
    project = HiddenField("Project", validators=[DataRequired()])
    receipt = FileField("Receipt", validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    
