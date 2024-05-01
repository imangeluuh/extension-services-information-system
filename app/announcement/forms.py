from flask import current_app
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, widgets, BooleanField
from flask_wtf.file import FileField, FileAllowed
from ..models import Project

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class AnnouncementForm(FlaskForm):
    title = StringField("Announcement Title")
    content = CKEditorField("Announcement Content")
    project = SelectField('Extension Project')
    publish = SubmitField("Publish") 
    draft = SubmitField("Save as Draft") 
    medium = BooleanField("Email")
    recipient = MultiCheckboxField("Recipient", choices=[('2', 'Beneficiaries'), ('3', 'Students'), ('5', 'Alumni')])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        with current_app.app_context():
            self.project.choices = [(project.ProjectId, project.Title) for project in Project.query.filter_by(IsArchived=False).all()]