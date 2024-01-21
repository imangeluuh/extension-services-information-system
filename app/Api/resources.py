from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, current_user
from ..models import *
from app import db
from .api_models import *
import uuid

authorizations = {
    "jsonWebToken": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

ns = Namespace("api", authorizations=authorizations)

@ns.route('/roles')
class RoleApi(Resource):

    @ns.marshal_list_with(role_model)
    def get(self):
        return Role.query.all()  

@ns.route('/login/admin')
class AdminLoginApi(Resource):
    
    @ns.expect(login_input_model)
    @ns.header('Content-Type', 'application/json')
    def post(self):
        attempted_user = Faculty.query.filter_by(Email=ns.payload['Email']).first()
        if attempted_user and attempted_user.Status == 'Active': 
            if attempted_user.check_password_correction(attempted_password=ns.payload['Password']):
                return {'access_token': create_access_token(attempted_user.LoginId),
                        'admin': attempted_user.to_dict()}
            else:
                return {'error': 'The password you\'ve entered is incorrect.'}, 404
        else:
            return {'error': 'The email you entered isn\'t connected to an account.'}, 404
        
@ns.route('/login/beneficiary')
class BeneficiaryLoginApi(Resource):
    
    @ns.expect(login_input_model)
    def post(self):
        attempted_user = Beneficiary.query.filter_by(Email=ns.payload['Email']).first()
        if attempted_user and attempted_user.Status == 'Active': 
            if attempted_user.check_password_correction(attempted_password=ns.payload['Password']):
                return {'access_token': create_access_token(attempted_user.LoginId),
                        'admin': attempted_user.to_dict()}
            else:
                return {'error': 'The password you\'ve entered is incorrect.'}, 404
        else:
            return {'error': 'The email you entered isn\'t connected to an account.'}, 404
        
@ns.route('/login/student')
class StudentLoginApi(Resource):
    
    @ns.expect(login_input_model)
    def post(self):
        attempted_user = Student.query.filter_by(Email=ns.payload['Email'], RoleId=3).first()
        if attempted_user and attempted_user.Status == 'Active': 
            if attempted_user.check_password_correction(attempted_password=ns.payload['Password']):
                return {'access_token': create_access_token(attempted_user.LoginId),
                        'admin': attempted_user.to_dict()}
            else:
                return {'error': 'The password you\'ve entered is incorrect.'}, 404
        else:
            return {'error': 'The email you entered isn\'t connected to an account.'}, 404
        
@ns.route('/login/faculty')
class FacultyLoginApi(Resource):
    
    @ns.expect(login_input_model)
    def post(self):
        attempted_user = Faculty.query.filter_by(Email=ns.payload['Email']).first()
        print(ns.payload)
        print(attempted_user)
        if attempted_user and attempted_user.Status == 'Active': 
            if attempted_user.check_password_correction(attempted_password=ns.payload['Password']):
                return {'access_token': create_access_token(attempted_user.LoginId),
                        'admin': attempted_user.to_dict()}
            else:
                return {'error': 'The password you\'ve entered is incorrect.'}, 404
        else:
            return {'error': 'The email you entered isn\'t connected to an account.'}, 404

@ns.route('/register/beneficiary')
class BeneficiaryRegisterApi(Resource):
    @ns.expect(register_input_model)
    def post(self):
        createUser(2)
        return {"success": "Account is successfully created"}, 200
    
@ns.route('/register/student')
class StudentRegisterApi(Resource):
    @ns.expect(register_input_model)
    def post(self):
        createUser(3)
        return {"success": "Account is successfully created"}, 200

@ns.route('/admins')
class AdminListApi(Resource):
    @ns.marshal_list_with(admin_model)
    def get(self):
        return Admin.query.all()
    
@ns.route('/users')
class UsersListApi(Resource):
    @ns.marshal_list_with(user_model)
    def get(self):
        return User.query.all()
    
@ns.route('/extension-programs')
class ExtensionProgramListApi(Resource):
    @ns.marshal_list_with(extension_program_model)
    def get(self):
        return ExtensionProgram.query.all()
    
@ns.route('/extension-projects')
class ExtensionProjectListApi(Resource):
    @ns.marshal_list_with(extension_project_model)
    def get(self):
        return Project.query.all()
    

def createUser(role):
    str_login_uuid = uuid.uuid4()
    user_login = Login(LoginId=str_login_uuid,
                        Email=ns.payload['Email'],
                        password_hash=ns.payload['Password'],
                        RoleId=role)
    str_user_id = uuid.uuid4()
    user_to_create = User(UserId=str_user_id,
                            FirstName=ns.payload['FirstName'],
                            MiddleName=ns.payload['MiddleName'],
                            LastName=ns.payload['LastName'],
                            ContactDetails=ns.payload['ContactDetails'],
                            Birthdate=ns.payload['Birthdate'],
                            Gender=ns.payload['Gender'],
                            Address=ns.payload['Address'],
                            LoginId=str_login_uuid)
    db.session.add(user_login)
    db.session.add(user_to_create)
    if role == 2:
        beneficiary_to_create = Beneficiary(BeneficiaryId = str_user_id)
        db.session.add(beneficiary_to_create)
    elif role == 3:
        student_to_create = Student(StudentId = str_user_id,
                                    SkillsInterest = ns.payload['SkillsInterest'])
        db.session.add(student_to_create)
    db.session.commit()