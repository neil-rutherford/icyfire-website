from flask import render_template, current_app
from app.email import send_email

def send_password_reset_email(user):
    token = user.get_reset_password()
    send_email('Reset your IcyFire password',
               sender='noreply@icy-fire.com',
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))

def send_verify_email_email(user):
    token = user.get_verify_email()
    send_email(
        'Verify your IcyFire email',
        sender='noreply@icy-fire.com',
        recipients=[user.email],
        text_body=render_template('email/verify_email.txt', user=user, token=token),
        html_body=render_template('email/verify_email.html', user=user, token=token))