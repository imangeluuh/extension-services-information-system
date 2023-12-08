from flask import render_template
from app.email import sendEmail


def sendPasswordResetEmail(user):
    token = user.get_reset_password_token()
    sendEmail('[PUPQC-ESIS] Reset Your Password',
                recipients=[user.Email],
                text_body=render_template('email/reset_password.txt', user=user, token=token),
                html_body=render_template('email/reset_password.html', user=user, token=token))