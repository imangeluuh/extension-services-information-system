from flask import url_for
from app import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, decode_token
from werkzeug.security import generate_password_hash, check_password_hash
import ast

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Role(db.Model):
    __tablename__ = 'ESISRole'

    RoleId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RoleName = db.Column(db.String(20), nullable=False)
    User = db.relationship("User", back_populates='Role')

class User(db.Model, UserMixin):
    __tablename__ = 'ESISUser'

    UserId = db.Column(db.String(36), primary_key=True) 
    RoleId = db.Column(db.Integer, db.ForeignKey('ESISRole.RoleId', ondelete='CASCADE'), nullable=False)
    StudentId =  db.Column(db.Integer, db.ForeignKey('SPSStudent.StudentId', ondelete='CASCADE'), unique=True)
    FacultyId = db.Column(db.Integer, db.ForeignKey('FISFaculty.FacultyId', ondelete='CASCADE'), unique=True)
    BeneficiaryId = db.Column(db.Integer, db.ForeignKey('ESISBeneficiary.BeneficiaryId', ondelete='CASCADE'), unique=True)
    Student =  db.relationship("Student", backref="User")
    Faculty =  db.relationship("Faculty", backref="User")
    Beneficiary =  db.relationship("Beneficiary", backref="User")
    Role = db.relationship("Role", back_populates='User')
    Registration = db.relationship('Registration', back_populates='User')
    Certificate = db.relationship("Certificate", back_populates="User")
    Attendance = db.relationship("Attendance", back_populates="User")
    Question = db.relationship('Question', back_populates='Creator')
    Evaluation = db.relationship('Evaluation', back_populates='Creator')
    
    def get_id(self):
        return self.UserId

    def get_role(self):
        return(self.Role.RoleName)
    

class Student(db.Model): 
    __tablename__ = 'SPSStudent' 

    StudentId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentNumber = db.Column(db.String(30), unique=True, nullable=False)  # UserID
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(256), nullable=False)  # Password
    Gender = db.Column(db.Integer, nullable=True)  # Gender
    DateOfBirth = db.Column(db.Date)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50))  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    IsOfficer = db.Column(db.Boolean, default=False)
    Token = db.Column(db.String(128))  # This is for handling reset password 
    TokenExpiration = db.Column(db.DateTime) # This is for handling reset password 
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    # IsBridging
    
    def to_dict(self):
        return {
            'StudentId': self.StudentId,
            'StudentNumber': self.StudentNumber,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'MiddleName': self.MiddleName,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsOfficer': self.IsOfficer
        }

    def get_id(self):
        return str(self.StudentId)  # Convert to string to ensure compatibility

    def get_user_id(self):
        return self.StudentId

# Faculty Users
class Faculty(db.Model):
    __tablename__ = 'FISFaculty' # Set the name of table in database
    FacultyId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FacultyType = db.Column(db.String(50), nullable=False)  # Faculty Type
    Rank = db.Column(db.String(50))  # Faculty Rank
    Units = db.Column(db.Numeric, nullable=False)  # Faculty Unit
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    MiddleInitial = db.Column(db.String(50))  # Middle Initial
    NameExtension = db.Column(db.String(50))  # Name Extension
    BirthDate = db.Column(db.Date, nullable=False)  # Birthdate
    DateHired = db.Column(db.Date, nullable=False)  # Date Hired
    Degree = db.Column(db.String)  # Degree
    Remarks = db.Column(db.String)  # Remarks
    FacultyCode = db.Column(db.Integer, nullable=False)  # Faculty Code
    Honorific = db.Column(db.String(50))  # Honorific
    Age = db.Column(db.Numeric, nullable=False)  # Age
    
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    ResidentialAddress = db.Column(db.String(50))  # ResidentialAddress
    MobileNumber = db.Column(db.String(11))  # MobileNumber
    Gender = db.Column(db.Integer) # Gender # 1 if Male 2 if Female
    
    Password = db.Column(db.String(256), nullable=False)  # Password
    ProfilePic= db.Column(db.String(50),default="14wkc8rPgd8NcrqFoRFO_CNyrJ7nhmU08")  # Profile Pic
    IsActive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    # FOREIGN TABLES
    

    def to_dict(self):
        return {
            'faculty_account_id': self.FacultyId,
            'faculty_type': self.FacultyType,
            'rank': self.Rank,
            'units': self.Units,
            'name': self.Name,
            'first_name': self.FirstName,
            'last_name': self.LastName,
            'middle_name': self.MiddleName,
            'middle_initial': self.MiddleInitial,
            'name_extension': self.NameExtension,
            'birth_date': self.BirthDate,
            'date_hired': self.DateHired,
            'degree': self.Degree,
            'remarks': self.Remarks,
            'faculty_code': self.FacultyCode,
            'honorific': self.Honorific,
            'age': self.Age,
            'email': self.Email,
            # 'password': self.password,
            'profile_pic': self.ProfilePic,
            'is_active': self.IsActive,
        }
        
    def get_id(self):
        return str(self.FacultyId)  # Convert to string to ensure compatibility


class Beneficiary(db.Model):
    __tablename__ = 'ESISBeneficiary'

    BeneficiaryId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FirstName = db.Column(db.String(50), nullable=False)  # First Name
    LastName = db.Column(db.String(50), nullable=False)  # Last Name
    MiddleName = db.Column(db.String(50))  # Middle Name
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Email
    Password = db.Column(db.String(256), nullable=False)  # Password
    Gender = db.Column(db.Integer, nullable=False)  # Gender: 1 if Male 2 if Female 3 if Others
    DateOfBirth = db.Column(db.Date, nullable=False)  # DateOfBirth
    PlaceOfBirth = db.Column(db.String(50), nullable=False)  # PlaceOfBirth
    ResidentialAddress = db.Column(db.String(50), nullable=False)  # ResidentialAddress
    MobileNumber = db.Column(db.String(11), nullable=False)  # MobileNumber
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    EvaluationResponse = db.relationship("Response", back_populates="Beneficiary")

    @property
    def password_hash(self):
        return self.password_hash

    @password_hash.setter
    def password_hash(self, plain_text_password):
        self.Password = generate_password_hash(plain_text_password)

    def check_password_correction(self, attempted_password):
        return check_password_hash(self.Password, attempted_password)
    
    def get_reset_password_token(self, expires_in=10):
        return create_access_token(identity={'reset_password': self.BeneficiaryId},expires_delta=timedelta(minutes=expires_in))

    @staticmethod
    def verify_reset_password_token(token):
        try:
            decoded_token = decode_token(token)
            user_id= decoded_token['sub']['reset_password']
        except:
            return
        return Beneficiary.query.get(user_id)


class ExtensionProgram(db.Model):
    __tablename__ = 'ESISExtensionProgram'

    ExtensionProgramId = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), nullable=False)
    Rationale = db.Column(db.Text, nullable=False)
    ImageUrl = db.Column(db.Text)
    ImageFileId = db.Column(db.Text)
    AgendaId = db.Column(db.Integer, db.ForeignKey('ESISAgenda.AgendaId', ondelete='CASCADE'), nullable=False)
    ProgramId = db.Column(db.Integer, db.ForeignKey('SPSCourse.CourseId', ondelete='CASCADE'), nullable=False)
    Agenda = db.relationship("Agenda", back_populates='ExtensionPrograms', lazy=True, passive_deletes=True)
    Program = db.relationship("Course", backref='ExtensionProgram')
    Projects = db.relationship("Project", back_populates='ExtensionProgram', cascade='all, delete-orphan')


class Project(db.Model):
    __tablename__ = 'ESISProject'

    ProjectId = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    Implementer = db.Column(db.String(255), nullable=False)
    LeadProponentId = db.Column(db.String(36), db.ForeignKey('ESISUser.UserId', ondelete='CASCADE'), nullable=False)
    CollaboratorId = db.Column(db.Integer, db.ForeignKey('ESISCollaborator.CollaboratorId', ondelete='CASCADE'), nullable=False)
    ProjectTeam = db.Column(db.JSON, nullable=False)
    TargetGroup= db.Column(db.String(255), nullable=False)
    ProjectType = db.Column(db.String(100), nullable=False)
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)
    ImpactStatement = db.Column(db.Text, nullable=False)
    Objectives = db.Column(db.Text, nullable=False)
    ImageUrl = db.Column(db.Text)
    ImageFileId = db.Column(db.Text)
    ProjectProposalUrl = db.Column(db.Text, nullable=False)
    ProjectProposalFileId = db.Column(db.Text, nullable=False)
    ExtensionProgramId = db.Column(db.Integer, db.ForeignKey('ESISExtensionProgram.ExtensionProgramId', ondelete='CASCADE'), nullable=False)
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

# Course List
class Course(db.Model):
    __tablename__ = 'SPSCourse'

    CourseId = db.Column(db.Integer, primary_key=True, autoincrement=True) # Unique Identifier
    CourseCode = db.Column(db.String(10), unique=True) # Course Code - (BSIT, BSHM, BSCS)
    Name = db.Column(db.String(200)) # (Name of Course (Bachelor of Science in Information Technology)
    Description = db.Column(db.String(200)) # Description of course
    IsValidPUPQCCourses = db.Column(db.Boolean, default=True) # APMS are handling different courses so there are specific courses available in QC Only
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'CourseCode': self.CourseCode,
            'Name': self.Name,
            'Description': self.Description,
            'IsValidPUPQCCourses': self.IsValidPUPQCCourses
        }


class Agenda(db.Model):
    __tablename__ = 'ESISAgenda'

    AgendaId = db.Column(db.Integer, primary_key=True)
    AgendaName = db.Column(db.String(255), nullable=False)
    ExtensionPrograms = db.relationship("ExtensionProgram", back_populates='Agenda', lazy=True)


class Collaborator(db.Model):
    __tablename__ = 'ESISCollaborator'

    CollaboratorId = db.Column(db.Integer, primary_key=True)
    Organization = db.Column(db.String(100), nullable=False)
    Location = db.Column(db.String(255), nullable=False)
    SignedMOAUrl = db.Column(db.Text, nullable=False)
    SignedMOAFileId = db.Column(db.Text, nullable=False)
    Projects = db.relationship("Project", back_populates='Collaborator', lazy=True)
    Budget = db.relationship('Budget', back_populates='Collaborator', cascade='all, delete-orphan')


class Activity(db.Model):
    __tablename__ = 'ESISActivity'

    ActivityId = db.Column(db.Integer, primary_key=True)
    ActivityName = db.Column(db.String(255), nullable=False)
    Date = db.Column(db.Date, index=True, nullable=False)
    StartTime = db.Column(db.Time, nullable=False)
    EndTime = db.Column(db.Time, nullable=False)
    Description = db.Column(db.Text, nullable=False)
    ImageUrl = db.Column(db.Text)
    ImageFileId = db.Column(db.Text)
    Speaker = db.Column(db.JSON, nullable=False)
    LocationId = db.Column(db.Integer, db.ForeignKey('ESISLocation.LocationId', ondelete='CASCADE'))
    ProjectId = db.Column(db.Integer, db.ForeignKey('ESISProject.ProjectId', ondelete='CASCADE'), nullable=False)
    Project = db.relationship('Project', back_populates='Activity', passive_deletes='all')
    Location = db.relationship('Location', back_populates='Activity', passive_deletes='all')
    Evaluation = db.relationship("Evaluation", back_populates='Activity', cascade='all, delete-orphan', lazy=True)
    Attendance = db.relationship('Attendance', back_populates='Activity', cascade='all, delete-orphan')
    Item = db.relationship('Item', back_populates='Activity', cascade='all, delete-orphan')

class Location(db.Model):
    __tablename__ = 'ESISLocation'

    LocationId = db.Column(db.Integer, primary_key=True)
    LocationName = db.Column(db.String(55), nullable=False)
    Longitude = db.Column(db.String(55), nullable=False)
    Latitude = db.Column(db.String(55), nullable=False)
    Activity = db.relationship('Activity', back_populates='Location')

class Speaker(db.Model):
    __tablename__ = 'ESISSpeaker'

    SpeakerId = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(50), nullable=False)
    MiddleName = db.Column(db.String(50), default=None)
    LastName = db.Column(db.String(50), nullable=False)
    # Email = db.Column(db.String(100), nullable=False)
    ContactDetails = db.Column(db.String(13), nullable=False)

class Item(db.Model):
    __tablename__ = 'ESISItem'

    ItemId = db.Column(db.Integer, primary_key=True)
    ItemName = db.Column(db.String(50), nullable=False)
    Amount = db.Column(db.Numeric(12, 2), nullable=False)
    IsPurchased = db.Column(db.Boolean, nullable=False, default=0)
    DatePurchased = db.Column(db.DateTime)
    ReceiptUrl = db.Column(db.Text)
    ReceiptId = db.Column(db.Text)
    ActivityId = db.Column(db.Integer, db.ForeignKey('ESISActivity.ActivityId', ondelete='CASCADE'), nullable=False)
    Activity = db.relationship("Activity", back_populates="Item", passive_deletes=True)

class Budget(db.Model):
    __tablename__ = 'ESISProjectBudget'

    BudgetId = db.Column(db.Integer, primary_key=True)
    FundType = db.Column(db.String(20), nullable=False)
    Amount = db.Column(db.Numeric(12, 2), nullable=False)
    ProjectId = db.Column(db.Integer, db.ForeignKey('ESISProject.ProjectId', ondelete='CASCADE'), nullable=False)
    CollaboratorId = db.Column(db.Integer, db.ForeignKey('ESISCollaborator.CollaboratorId', ondelete='CASCADE'))
    Project = db.relationship("Project", back_populates="Budget", passive_deletes=True)
    Collaborator = db.relationship("Collaborator", back_populates="Budget", passive_deletes=True)

class Announcement(db.Model):
    __tablename__ = 'ESISAnnouncement'

    AnnouncementId = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    Content= db.Column(db.Text)
    CreatorId = db.Column(db.String(36), db.ForeignKey('ESISUser.UserId', ondelete='CASCADE'), nullable=False)
    IsLive = db.Column(db.Boolean, index=True, nullable=False)
    Slug = db.Column(db.String(255), nullable=False)
    Created = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    Updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True, nullable=False)
    ImageUrl = db.Column(db.Text)
    ImageId = db.Column(db.Text)
    ProjectId = db.Column(db.Integer, db.ForeignKey('ESISProject.ProjectId', ondelete='CASCADE'), nullable=False)
    Project = db.relationship('Project', backref='Announcement')
    Creator = db.relationship('User', backref='Announcement')


class Registration(db.Model):
    __tablename__ = 'ESISRegistration'

    RegistrationId = db.Column(db.Integer, primary_key=True)
    RegistrationDate = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    IsAssigned = db.Column(db.Boolean, default=False, nullable=False)
    ProjectId = db.Column(db.Integer, db.ForeignKey('ESISProject.ProjectId', ondelete='CASCADE'), nullable=False)
    UserId = db.Column(db.String(36), db.ForeignKey('ESISUser.UserId', ondelete='CASCADE'), nullable=False)
    User = db.relationship('User', back_populates='Registration', passive_deletes=True)


class Question(db.Model):
    __tablename__ = 'ESISQuestion'

    QuestionId = db.Column(db.Integer, primary_key=True)
    Text = db.Column(db.Text, nullable=False)
    State = db.Column(db.Integer, nullable=False)
    Type = db.Column(db.Integer, nullable=False)
    Required = db.Column(db.Integer, nullable=False)
    CreatorId = db.Column(db.String(36), db.ForeignKey('ESISUser.UserId', ondelete='CASCADE'), nullable=False)
    Responses = db.Column(db.Text, nullable=False)
    Creator = db.relationship("User", back_populates="Question", passive_deletes=True)
    Response = db.relationship("Response", back_populates="Question",  cascade='all, delete-orphan')

    def responsesList(self):
        return ast.literal_eval(self.Responses)


class Evaluation(db.Model):
    __tablename__ = 'ESISEvaluation'

    EvaluationId = db.Column(db.Integer, primary_key=True)
    EvaluationName = db.Column(db.Text, nullable=False)
    ActivityId = db.Column(db.Integer, db.ForeignKey('ESISActivity.ActivityId', ondelete='CASCADE'), nullable=False)
    State = db.Column(db.Integer, nullable=False)
    Questions = db.Column(db.Text, nullable=False)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    CreatorId = db.Column(db.String(36), db.ForeignKey('ESISUser.UserId', ondelete='CASCADE'), nullable=False)
    Activity = db.relationship("Activity", back_populates="Evaluation", passive_deletes=True)
    Response = db.relationship("Response", back_populates="Evaluation", cascade='all, delete-orphan')
    Creator = db.relationship("User", back_populates="Evaluation", passive_deletes=True)

    def questionsList(self):
        return ast.literal_eval(self.Questions)


class Response(db.Model):
    __tablename__ = 'ESISResponse'

    ResponseId = db.Column(db.Integer, primary_key=True)
    BeneficiaryId = db.Column(db.Integer, db.ForeignKey('ESISBeneficiary.BeneficiaryId'))
    EvaluationId = db.Column(db.Integer, db.ForeignKey('ESISEvaluation.EvaluationId', ondelete='CASCADE'), nullable=False)
    QuestionId = db.Column(db.Integer, db.ForeignKey('ESISQuestion.QuestionId'), nullable=False)
    Text = db.Column(db.Text)
    Num = db.Column(db.Integer)
    Beneficiary = db.relationship("Beneficiary", back_populates="EvaluationResponse")
    Evaluation = db.relationship("Evaluation", back_populates="Response", passive_deletes=True)
    Question = db.relationship("Question", back_populates="Response", passive_deletes=True)

    def responsesList(self):
        return ast.literal_eval(self.Responses)
    
class Attendance(db.Model):
    __tablename__ = 'ESISAttendance'

    AttendanceId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.String(36), db.ForeignKey('ESISUser.UserId'), nullable=False)
    ActivityId = db.Column(db.Integer, db.ForeignKey('ESISActivity.ActivityId', ondelete='CASCADE'), nullable=False)
    Activity = db.relationship("Activity", back_populates="Attendance", passive_deletes=True)
    User = db.relationship("User", back_populates="Attendance")

    # Create the unique constraint
    __table_args__ = (db.UniqueConstraint("UserId", "ActivityId", name="unique_user_activity"),)

class Certificate(db.Model):
    __tablename__ = 'ESISCertificate'

    CertificateId = db.Column(db.Integer, primary_key=True)
    CertificateUrl = db.Column(db.Text)
    CertificateFileId = db.Column(db.Text)
    UserId = db.Column(db.String(36), db.ForeignKey('ESISUser.UserId'), nullable=False)
    ProjectId = db.Column(db.Integer, db.ForeignKey('ESISProject.ProjectId', ondelete='CASCADE'), nullable=False)
    User = db.relationship("User", back_populates="Certificate", passive_deletes=True)
    Project = db.relationship("Project", back_populates="Certificate")

