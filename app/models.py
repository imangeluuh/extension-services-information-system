from flask import url_for
from app import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta
from time import time
from flask_jwt_extended import create_access_token, decode_token
import ast

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Role(db.Model):
    __tablename__ = 'Role'

    RoleId = db.Column(db.Integer, primary_key=True)
    RoleName = db.Column(db.String(14), nullable=False)
    User = db.relationship("User", back_populates='Role',  cascade='all, delete-orphan')

class User(db.Model, UserMixin):
    __tablename__ = 'User'

    UserId = db.Column(db.String(36), primary_key=True) # System Id
    UserNumber = db.Column(db.String(30), index=True, unique=True, nullable=False) # Student/Faculty/Beneficiary ID
    FirstName = db.Column(db.String(50), nullable=False)
    MiddleName = db.Column(db.String(50), default=None)
    LastName = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(50), nullable=False, index=True, unique=True)
    Password = db.Column(db.String(60), nullable=False)
    Gender = db.Column(db.String(20), nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    PlaceOfBirth = db.Column(db.String(50), nullable=False)
    ResidentialAddress = db.Column(db.String(50), nullable=False)
    MobileNumber = db.Column(db.String(11), nullable=False)
    RoleId = db.Column(db.Integer, db.ForeignKey('Role.RoleId', ondelete='CASCADE'), nullable=False)
    Role = db.relationship("Role", back_populates='User', passive_deletes=True)
    Registration = db.relationship('Registration', backref='User', cascade='all, delete-orphan', passive_deletes=True)
    Certificate = db.relationship("Certificate", back_populates="User")
    Attendance = db.relationship("Attendance", back_populates="User")
    Question = db.relationship('Question', back_populates='Creator', cascade='all, delete-orphan')
    Evaluation = db.relationship('Evaluation', back_populates='Creator', cascade='all, delete-orphan')

    @property
    def password_hash(self):
        return self.password_hash

    @password_hash.setter
    def password_hash(self, plain_text_password):
        self.Password = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.Password, attempted_password)
    
    def get_reset_password_token(self, expires_in=10):
        return create_access_token(identity={'reset_password': self.UserId},expires_delta=timedelta(minutes=expires_in))

    @staticmethod
    def verify_reset_password_token(token):
        try:
            decoded_token = decode_token(token)
            user_id= decoded_token['sub']['reset_password']
        except:
            return
        return User.query.get(user_id)
    
    def get_id(self):
        return self.UserId

    def get_role(self):
        return(self.Role.RoleName)


class Beneficiary(db.Model):
    __tablename__ = 'Beneficiary'

    BeneficiaryId = db.Column(db.String(36), db.ForeignKey('User.UserId', ondelete='CASCADE'), primary_key=True)
    User = db.relationship("User", backref='Beneficiary', lazy=True, passive_deletes=True)
    EvaluationResponse = db.relationship("Response", back_populates="Beneficiary")


class ExtensionProgram(db.Model):
    __tablename__ = 'ExtensionProgram'

    ExtensionProgramId = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), nullable=False)
    Rationale = db.Column(db.Text, nullable=False)
    ImageUrl = db.Column(db.Text)
    ImageFileId = db.Column(db.Text)
    AgendaId = db.Column(db.Integer, db.ForeignKey('Agenda.AgendaId', ondelete='CASCADE'), nullable=False)
    ProgramId = db.Column(db.Integer, db.ForeignKey('Program.ProgramId', ondelete='CASCADE'), nullable=False)
    Agenda = db.relationship("Agenda", back_populates='ExtensionPrograms', lazy=True, passive_deletes=True)
    Program = db.relationship("Program", back_populates='ExtensionPrograms', lazy=True, passive_deletes=True)
    Projects = db.relationship("Project", back_populates='ExtensionProgram', cascade='all, delete-orphan')


class Project(db.Model):
    __tablename__ = 'Project'

    ProjectId = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    Implementer = db.Column(db.String(255), nullable=False)
    LeadProponentId = db.Column(db.String(36), db.ForeignKey('User.UserId', ondelete='CASCADE'), nullable=False)
    CollaboratorId = db.Column(db.Integer, db.ForeignKey('Collaborator.CollaboratorId', ondelete='CASCADE'), nullable=False)
    ProjectTeam = db.Column(db.JSON, nullable=False)
    TargetGroup= db.Column(db.String(255), nullable=False)
    ProjectType = db.Column(db.String(100), nullable=False)
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)
    ImpactStatement = db.Column(db.Text, nullable=False)
    Objectives = db.Column(db.Text, nullable=False)
    Status = db.Column(db.String(20), nullable=False) 
    ImageUrl = db.Column(db.Text)
    ImageFileId = db.Column(db.Text)
    ProjectProposalUrl = db.Column(db.Text, nullable=False)
    ProjectProposalFileId = db.Column(db.Text, nullable=False)
    ExtensionProgramId = db.Column(db.Integer, db.ForeignKey('ExtensionProgram.ExtensionProgramId', ondelete='CASCADE'), nullable=False)
    LeadProponent = db.relationship('User', backref='Project', lazy=True, passive_deletes=True)
    Collaborator = db.relationship("Collaborator", back_populates='Projects', lazy=True)
    ExtensionProgram = db.relationship("ExtensionProgram", back_populates='Projects', lazy=True, passive_deletes=True)
    Registration = db.relationship('Registration', backref='Project', cascade='all, delete-orphan', passive_deletes=True)
    Certificate = db.relationship('Certificate', back_populates='Project')
    Activity = db.relationship("Activity", back_populates="Project", cascade='all, delete-orphan')
    Budget = db.relationship('Budget', back_populates='Project', cascade='all, delete-orphan')

    def totalBudget(self):
        # Calculates and returns the total budget for the project.
        return sum(budget.Amount for budget in self.Budget)

class Program(db.Model):
    __tablename__ = 'Program'

    ProgramId = db.Column(db.Integer, primary_key=True)
    ProgramName = db.Column(db.String(255), nullable=False)
    Abbreviation = db.Column(db.String(255), nullable=False)
    ExtensionPrograms = db.relationship("ExtensionProgram", back_populates='Program', lazy=True)


class Agenda(db.Model):
    __tablename__ = 'Agenda'

    AgendaId = db.Column(db.Integer, primary_key=True)
    AgendaName = db.Column(db.String(255), nullable=False)
    ExtensionPrograms = db.relationship("ExtensionProgram", back_populates='Agenda', lazy=True)


class Collaborator(db.Model):
    __tablename__ = 'Collaborator'

    CollaboratorId = db.Column(db.Integer, primary_key=True)
    Organization = db.Column(db.String(100), nullable=False)
    Location = db.Column(db.String(255), nullable=False)
    SignedMOAUrl = db.Column(db.Text, nullable=False)
    SignedMOAFileId = db.Column(db.Text, nullable=False)
    Projects = db.relationship("Project", back_populates='Collaborator', lazy=True)
    Budget = db.relationship('Budget', back_populates='Collaborator', cascade='all, delete-orphan')


class Activity(db.Model):
    __tablename__ = 'Activity'

    ActivityId = db.Column(db.Integer, primary_key=True)
    ActivityName = db.Column(db.String(255), nullable=False)
    Date = db.Column(db.Date, index=True, nullable=False)
    StartTime = db.Column(db.Time, nullable=False)
    EndTime = db.Column(db.Time, nullable=False)
    Description = db.Column(db.Text, nullable=False)
    ImageUrl = db.Column(db.Text)
    ImageFileId = db.Column(db.Text)
    Speaker = db.Column(db.JSON, nullable=False)
    LocationId = db.Column(db.Integer, db.ForeignKey('Location.LocationId'))
    ProjectId = db.Column(db.Integer, db.ForeignKey('Project.ProjectId', ondelete='CASCADE'), nullable=False)
    Project = db.relationship('Project', back_populates='Activity', passive_deletes='all')
    Location = db.relationship('Location', back_populates='Activity', passive_deletes='all')
    Evaluation = db.relationship("Evaluation", back_populates='Activity', cascade='all, delete-orphan', lazy=True)
    Attendance = db.relationship('Attendance', back_populates='Activity', cascade='all, delete-orphan')
    Item = db.relationship('Item', back_populates='Activity', cascade='all, delete-orphan')

class Location(db.Model):
    __tablename__ = 'Location'

    LocationId = db.Column(db.Integer, primary_key=True)
    LocationName = db.Column(db.String(55), nullable=False)
    Longitude = db.Column(db.String(55), nullable=False)
    Latitude = db.Column(db.String(55), nullable=False)
    Activity = db.relationship('Activity', back_populates='Location')

class Speaker(db.Model):
    __tablename__ = 'Speaker'

    SpeakerId = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(50), nullable=False)
    MiddleName = db.Column(db.String(50), default=None)
    LastName = db.Column(db.String(50), nullable=False)
    # Email = db.Column(db.String(100), nullable=False)
    ContactDetails = db.Column(db.String(13), nullable=False)

class Item(db.Model):
    __tablename__ = 'Item'

    ItemId = db.Column(db.Integer, primary_key=True)
    ItemName = db.Column(db.String(50), nullable=False)
    Amount = db.Column(db.Numeric(12, 2), nullable=False)
    IsPurchased = db.Column(db.Boolean, nullable=False, default=0)
    DatePurchased = db.Column(db.DateTime)
    ReceiptUrl = db.Column(db.Text)
    ReceiptId = db.Column(db.Text)
    ActivityId = db.Column(db.Integer, db.ForeignKey('Activity.ActivityId', ondelete='CASCADE'), nullable=False)
    Activity = db.relationship("Activity", back_populates="Item", passive_deletes=True)

class Budget(db.Model):
    __tablename__ = 'Budget'

    BudgetId = db.Column(db.Integer, primary_key=True)
    FundType = db.Column(db.String(20), nullable=False)
    Amount = db.Column(db.Numeric(12, 2), nullable=False)
    ProjectId = db.Column(db.Integer, db.ForeignKey('Project.ProjectId', ondelete='CASCADE'), nullable=False)
    CollaboratorId = db.Column(db.Integer, db.ForeignKey('Collaborator.CollaboratorId', ondelete='CASCADE'))
    Project = db.relationship("Project", back_populates="Budget", passive_deletes=True)
    Collaborator = db.relationship("Collaborator", back_populates="Budget", passive_deletes=True)

class Announcement(db.Model):
    __tablename__ = 'Announcement'

    AnnouncementId = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    Content= db.Column(db.Text)
    CreatorId = db.Column(db.String(36), db.ForeignKey('User.UserId', ondelete='CASCADE'), nullable=False)
    IsLive = db.Column(db.Boolean, index=True, nullable=False)
    Slug = db.Column(db.String(255), nullable=False)
    Created = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    Updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True, nullable=False)
    ImageUrl = db.Column(db.Text)
    ImageId = db.Column(db.Text)
    ProjectId = db.Column(db.Integer, db.ForeignKey('Project.ProjectId', ondelete='CASCADE'), nullable=False)
    Project = db.relationship('Project', backref='Announcement')
    Creator = db.relationship('User', backref='Announcement')


class Registration(db.Model):
    __tablename__ = 'Registration'

    RegistrationId = db.Column(db.Integer, primary_key=True)
    RegistrationDate = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    IsAssigned = db.Column(db.Boolean, default=False, nullable=False)
    ProjectId = db.Column(db.Integer, db.ForeignKey('Project.ProjectId', ondelete='CASCADE'), nullable=False)
    UserId = db.Column(db.String(36), db.ForeignKey('User.UserId', ondelete='CASCADE'), nullable=False)


class Question(db.Model):
    __tablename__ = 'Question'

    QuestionId = db.Column(db.Integer, primary_key=True)
    Text = db.Column(db.Text, nullable=False)
    State = db.Column(db.Integer, nullable=False)
    Type = db.Column(db.Integer, nullable=False)
    Required = db.Column(db.Integer, nullable=False)
    CreatorId = db.Column(db.String(36), db.ForeignKey('User.UserId', ondelete='CASCADE'), nullable=False)
    Responses = db.Column(db.Text, nullable=False)
    Creator = db.relationship("User", back_populates="Question", passive_deletes=True)
    Response = db.relationship("Response", back_populates="Question",  cascade='all, delete-orphan')

    def responsesList(self):
        return ast.literal_eval(self.Responses)


class Evaluation(db.Model):
    __tablename__ = 'Evaluation'

    EvaluationId = db.Column(db.Integer, primary_key=True)
    EvaluationName = db.Column(db.Text, nullable=False)
    ActivityId = db.Column(db.Integer, db.ForeignKey('Activity.ActivityId', ondelete='CASCADE'), nullable=False)
    State = db.Column(db.Integer, nullable=False)
    Questions = db.Column(db.Text, nullable=False)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    CreatorId = db.Column(db.String(36), db.ForeignKey('User.UserId', ondelete='CASCADE'), nullable=False)
    Activity = db.relationship("Activity", back_populates="Evaluation", passive_deletes=True)
    Response = db.relationship("Response", back_populates="Evaluation", cascade='all, delete-orphan')
    Creator = db.relationship("User", back_populates="Evaluation", passive_deletes=True)

    def questionsList(self):
        return ast.literal_eval(self.Questions)


class Response(db.Model):
    __tablename__ = 'Response'

    ResponseId = db.Column(db.Integer, primary_key=True)
    BeneficiaryId = db.Column(db.String(36), db.ForeignKey('Beneficiary.BeneficiaryId'))
    EvaluationId = db.Column(db.Integer, db.ForeignKey('Evaluation.EvaluationId', ondelete='CASCADE'), nullable=False)
    QuestionId = db.Column(db.Integer, db.ForeignKey('Question.QuestionId'), nullable=False)
    Text = db.Column(db.Text)
    Num = db.Column(db.Integer)
    Beneficiary = db.relationship("Beneficiary", back_populates="EvaluationResponse")
    Evaluation = db.relationship("Evaluation", back_populates="Response", passive_deletes=True)
    Question = db.relationship("Question", back_populates="Response", passive_deletes=True)

    def responsesList(self):
        return ast.literal_eval(self.Responses)
    
class Attendance(db.Model):
    __tablename__ = 'Attendance'

    AttendanceId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.String(36), db.ForeignKey('User.UserId'), nullable=False)
    ActivityId = db.Column(db.Integer, db.ForeignKey('Activity.ActivityId', ondelete='CASCADE'), nullable=False)
    Activity = db.relationship("Activity", back_populates="Attendance", passive_deletes=True)
    User = db.relationship("User", back_populates="Attendance")

    # Create the unique constraint
    __table_args__ = (db.UniqueConstraint("UserId", "ActivityId", name="unique_user_activity"),)

class Certificate(db.Model):
    __tablename__ = 'Certificate'

    CertificateId = db.Column(db.Integer, primary_key=True)
    CertificateUrl = db.Column(db.Text)
    CertificateFileId = db.Column(db.Text)
    UserId = db.Column(db.String(36), db.ForeignKey('User.UserId'), nullable=False)
    ProjectId = db.Column(db.Integer, db.ForeignKey('Project.ProjectId', ondelete='CASCADE'), nullable=False)
    User = db.relationship("User", back_populates="Certificate", passive_deletes=True)
    Project = db.relationship("Project", back_populates="Certificate")

