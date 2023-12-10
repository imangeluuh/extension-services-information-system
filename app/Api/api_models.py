from flask_restx import fields
from app import api

role_model = api.model("Role", {
    "RoleId": fields.Integer,
    "RoleName": fields.String,
    # "Login": fields.Nested,
})

login_input_model = api.model("LoginInput", {
    "Email": fields.String,
    "Password": fields.String,
})

login_model = api.model("Login", {
    "LoginId": fields.String,
    "Email": fields.String,
    "Password": fields.String,
    "RoleId": fields.Integer
})

register_input_model = api.model("RegisterInput", {
    "Email": fields.String,
    "Password": fields.String,
    "FirstName": fields.String,
    "MiddleName": fields.String,
    "LastName": fields.String,
    "ContactDetails": fields.String,
    "Birthdate": fields.Date,
    "Gender": fields.String,
    "Address": fields.String,
    "SkillsInterest": fields.String,
})

admin_model = api.model("Admin", {
    "AdminId": fields.String,
    "FirstName": fields.String,
    "LastName": fields.String,
    # "AdminLogin": fields.Nested(login_model)
})

# registration_model = api.model("Registration", {
#     "RegistrationId": fields.Integer,
#     "RegistrationDate": fields.Date,
#     "ProjectId": fields.Integer,
#     "User": fields.Nested(user_model)
# })

user_model = api.model("User", {
    "UserId": fields.String,
    "FirstName": fields.String,
    "MiddleName": fields.String,
    "LastName": fields.String,
    "ContactDetails": fields.String,
    "Birthdate": fields.Date,
    "Gender": fields.String,
    "Address": fields.String,
    # "UserLogin": fields.Nested(login_model)
})

activity_model = api.model("Activity", {
    "ActivityId": fields.Integer,
    "ActivityName": fields.String,
    "Date": fields.Date,
    # "StartTime": fields.DateTime(dt_format='%H:%M:%S'),
    # "EndTime": fields.DateTime(dt_format='%H:%M:%S'),
    "Description": fields.String,
    "Location": fields.String,
    "ImageUrl": fields.String,
    "Speaker": fields.Raw,
})

agenda_model = api.model("Agenda", {
    "AgendaId": fields.Integer,
    "AgendaName": fields.String,
})

collaborator_model = api.model("Collaborator", {
    "CollaboratorId": fields.Integer,
    "Organization": fields.String,
    "KeyPersonnel": fields.String,
    "Location": fields.String
})

extension_project_model = api.model("ExtensionProject", {
    "ProjectId": fields.Integer,
    "Title": fields.String,
    "Implementer": fields.String,
    "ProjectTeam": fields.Raw,
    "TargetGroup": fields.String,
    "ProjectType": fields.String,
    "StartDate": fields.Date,
    "EndDate": fields.Date,
    "ProposedBudget": fields.Float,
    "ApprovedBudget": fields.Float,
    "FundType": fields.String,
    "ImpactStatement": fields.String,
    "Objectives": fields.String,
    "Status": fields.String,
    "ImageUrl": fields.String,
    "ProjectProposalUrl": fields.String,
    "LeadProponent": fields.Nested(user_model),
    "Collaborator": fields.Nested(collaborator_model),
    "Activity": fields.Nested(activity_model),
})

program_model = api.model("Program", {
    "ProgramId": fields.Integer,
    "ProgramName": fields.String,
    "Abbreviation": fields.String
})

extension_program_model = api.model("ExtensionProgram", {
    "ExtensionProgramId": fields.Integer,
    "Name": fields.String,
    "Rationale": fields.String,
    "ImageUrl": fields.String,
    "Agenda": fields.Nested(agenda_model),
    "Program": fields.Nested(program_model),
    "Projects": fields.List(fields.Nested(extension_project_model)),
})