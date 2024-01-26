from flask import render_template, current_app
from flask_mail import Message
from app import mail, db
from threading import Thread
from .models import Project, User, Registration, Certificate
from fillpdf import fillpdfs
from datetime import datetime
from .store import uploadImage
import os

# Function to send an email asynchronously
def sendAsyncEmail(app, msg):
    with app.app_context():
        mail.send(msg)

# Function to send an email asynchronously with threading
def sendEmail(subject, recipients, text_body, html_body):
    msg=Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # Create a new Thread to send the email asynchronously
    Thread(target=sendAsyncEmail, args=(current_app._get_current_object(), msg)).start()

def generateCertificate(app, id):
    with app.app_context():
        beneficiaries = [registration.User for registration in Registration.query.filter_by(ProjectId=id).all() if registration.User.RoleId == 2]
        # Get the project proponent's name for the certificate
        project = Project.query.filter_by(ProjectId=id).first()
        project_proponent = User.query.filter_by(UserId=project.LeadProponentId).first()
        proponent_name = project_proponent.Faculty.FirstName + ' '
        if project_proponent.Faculty.MiddleName:
            proponent_name += project_proponent.Faculty.MiddleName[0] + '. '
        proponent_name += project_proponent.Faculty.LastName
        # Generate certificate for each beneficiary registered in the project
        for beneficiary in beneficiaries:
            # Get the name of the beneficiary for the certificate
            beneficiary_name = beneficiary.Beneficiary.FirstName + ' '
            if beneficiary.Beneficiary.MiddleName:
                beneficiary_name += beneficiary.Beneficiary.MiddleName[0] + '. '
            beneficiary_name += beneficiary.Beneficiary.LastName
            data_dict = {'Text-n_L-ntAGRy': beneficiary_name,
                        'Text-Pnb29VfGWk': project.Title,
                        'Date-jWSJ8ZAYJ_': datetime.utcnow(),
                        'Text-tf2etyjp87': proponent_name,
                        'Text-bcixq7yk8z': 'Jaime P. Gutierrez, Jr.'}
            
            # Get the initials of the beneficiary
            beneficiary_initials = ''.join([word[0] for word in beneficiary_name.split()])
            # Fill the pdf with the required information
            filepath = os.path.join(current_app.root_path, "media") + "\\" + project.Title + "-" + beneficiary_initials + " CERTIFICATE.pdf"
            fillpdfs.write_fillable_pdf(os.path.join(current_app.config["UPLOAD_FOLDER"], "e-cert (beneficiary) (FILLABLE).pdf"), filepath, data_dict, flatten=True)

            # Upload cert pdf to cloud
            status = uploadImage(filepath, project.Title + "-" + beneficiary_initials + " CERTIFICATE.pdf")

            # Get the url and file id of the uploaded certificate
            str_cert_url = None
            str_cert_file_id = None
            if status.error is not None:
                print("Error in releasing certificates", category="error")
                # return url_for('programs.viewProject', id=id)
            else:
                str_cert_url = status.url
                str_cert_file_id = status.file_id

            # Delete file from local storage after uploading to cloud
            if os.path.exists(filepath):
                os.remove(filepath)

            # Save certificate to database
            cert_to_add = Certificate(CertificateUrl=str_cert_url, 
                                    CertificateFileId = str_cert_file_id, 
                                    UserId=beneficiary.UserId, 
                                    ProjectId=project.ProjectId)
            
            db.session.add(cert_to_add)
        try:
            db.session.commit()
            print('Certificate is successfully released')
            # flash('Certificate is successfully released', category='success')
        except Exception as e:
            print(e)

def certificate(id):
    Thread(target=generateCertificate, args=(current_app._get_current_object(), id)).start()
