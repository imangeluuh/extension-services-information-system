from flask import render_template, current_app, url_for
from ..models import Login, User
from app.email import sendEmail
from app import db
import random, string, requests, uuid
from threading import Thread
from datetime import datetime

def sendPasswordResetEmail(user):
    token = user.get_reset_password_token()
    sendEmail('[PUPQC-ESIS] Reset Your Password',
                recipients=[user.Email],
                text_body=render_template('email/reset_password.txt', user=user, token=token),
                html_body=render_template('email/reset_password.html', user=user, token=token))
    
def sendAccountEmail(app, email, login_url):
    with app.app_context():
        success = False
        faculty_info = None
        try:
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
                # Check if the input email is found in the faculty data
                for faculty_id in faculty_account_ids:
                    if email == api_data['Faculties'][faculty_id]['email']:
                        # Check if email is not connected to an existing account
                        if not Login.query.filter_by(Email=email).first():
                            success = True
                            faculty_info = api_data['Faculties'][faculty_id]
                        break
        except Exception as e:
            print(e)
        # Create account if email is found in faculty data and if account is not existing 
        if success:
            # Generates a random 8-character string containing uppercase, lowercase, and numbers.
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
            temp_password = ''.join(random.choice(chars) for _ in range(8))
            str_login_uuid = uuid.uuid4()
            faculty_login = Login(LoginId=str_login_uuid,
                        Email=faculty_info['email'],
                        password_hash=temp_password,
                        RoleId=4)
            # Parse the date string using strptime with the appropriate format code
            birthdate = datetime.strptime(faculty_info['birth_date'], '%a, %d %b %Y %H:%M:%S %Z')
            faculty_to_create = User(UserId=faculty_info['faculty_account_id'],
                                        FirstName=faculty_info['first_name'],
                                        MiddleName=faculty_info['middle_name'],
                                        LastName=faculty_info['last_name'],
                                        ContactDetails='0'+faculty_info['PDS_Contact_Details']['mobile_number'],
                                        Birthdate=birthdate.strftime('%Y-%m-%d'),
                                        Gender=faculty_info['PDS_Personal_Details']['sex'],
                                        Address=faculty_info['PDS_Contact_Details']['perm_address'],
                                        LoginId=str_login_uuid)
            db.session.add(faculty_login)
            db.session.add(faculty_to_create)
            db.session.commit()
            sendEmail('[PUPQC-ESIS] Account Creation Request',
                    recipients=[email],
                    text_body=render_template('email/successful_account.txt', temp_password=temp_password, login_url=login_url),
                    html_body=render_template('email/successful_account.html', temp_password=temp_password, login_url=login_url))
        else:
            sendEmail('[PUPQC-ESIS] Account Creation Request',
                    recipients=[email],
                    text_body=render_template('email/unsuccessful_account.txt'),
                    html_body=render_template('email/unsuccessful_account.html'))
        
def requestAccount(email):
    email_input = email
    login_url = url_for('auth.facultyLogin', _external=True)
    # Create a new Thread to send the email asynchronously
    Thread(target=sendAccountEmail, args=(current_app._get_current_object(), email_input, login_url)).start()
