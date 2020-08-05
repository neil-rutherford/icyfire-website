from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User, Domain
from flask_login import current_user
from flask import url_for
import twitter
import pytumblr
import facebook
import praw
from flask import request

def password_check(form, field):
    '''
    Custom validator that checks to see if two passwords are equal.
    '''
    if form.password.data != form.verify_password.data:
        raise ValidationError('Passwords must match.')

def icyfire_email_check(form, field):
    '''
    Custom validator that raises a ValidationError if an email address does not belong to the "@icy-fire.com" domain.
    '''
    domain = str(field.data).split('@')[-1:]
    for domain in domain:
        if domain != 'icy-fire.com':
            raise ValidationError('Please use an IcyFire email address.')

def phone_check(form, field):
    '''
    Custom validator that raises a ValidationError if there are non-numeric characters.
    '''
    numbers = ['0','1','2','3','4','5','6','7','8','9']
    for character in str(field.data):
        if character == '-':
            raise ValidationError("We're expecting something like 1112223333, not 111-222-3333.")
        elif character not in numbers:
            raise ValidationError('Numbers only, please.')

# LOGIN FORM
class LoginForm(FlaskForm):
    '''
    Login form that takes email and password.
    '''
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')

# DOMAIN REGISTRATION FORM
class DomainRegistrationForm(FlaskForm):
    '''
    New admins set up their new domain here. 
    Activation codes are generated and provided to companies when they pay for the service.
    '''
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password (8 characters minimum)', validators=[DataRequired(), Length(min=8)])
    verify_password = PasswordField('Verify password', validators=[DataRequired(), password_check])
    domain_name = StringField('Choose a name for your domain', validators=[DataRequired(), Length(max=120)])
    activation_code = StringField('Activation code', validators=[DataRequired()])
    email_opt_in = BooleanField("Want to receive email updates about new products we're developing? (No spam, we promise.)")
    submit = SubmitField('Register')

    def validate_email(self, email):
        '''
        If an account already exists with that email address, this check raises a ValidationError.
        '''
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_activation_code(self, activation_code):
        '''
        If the activation code they entered is not valid, this check raises a ValidationError.
        '''
        domain = Domain.query.filter_by(activation_code=activation_code.data).first()
        if domain is None:
            raise ValidationError('Activation code incorrect. Please try again or contact your agent for assistance.')
    
    def validate_domain_name(self, domain_name):
        '''
        If the domain name they chose is not unique, this check raises a ValidationError.
        '''
        domain = Domain.query.filter_by(domain_name=domain_name.data).first()
        if domain is not None:
            raise ValidationError('Please choose a different domain name.')

# USER REGISTRATION FORM
class UserRegistrationForm(FlaskForm):
    '''
    Normal users link to an existing domain here.
    '''
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password (8 characters minimum)', validators=[DataRequired(), Length(min=8)])
    verify_password = PasswordField('Verify password', validators=[DataRequired(), password_check])
    domain_name = StringField('Domain name')
    email_opt_in = BooleanField("Want to receive email updates about new products we're developing? (No spam, we promise.)")
    submit = SubmitField('Register')

    def validate_email(self, email):
        '''
        If an account already exists with that email address, this check raises a ValidationError.
        '''
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_domain_name(self, domain_name):
        '''
        If the domain name they entered doesn't exist, this check raises a ValidationError.
        '''
        domain = Domain.query.filter_by(domain_name=domain_name.data).first()
        if domain is None:
            raise ValidationError("That domain doesn't exist. Please try again or contact your administrator for assistance.")

# CONTRACTOR REGISTRATION FORM
class ContractorRegistrationForm(FlaskForm):
    '''
    New contractors, regardless of rank, register here.
    '''
    icyfire_region = SelectField('What state are you in?', choices=[
        ('00', 'Not applicable. I am the Nation Lead.'),
        ('SOUTH', 'Alabama'),
        ('PACIFIC', 'Alaska'),
        ('PACIFIC', 'Arizona'),
        ('SOUTH', 'Arkansas'),
        ('PACIFIC', 'California'),
        ('FRONTIER', 'Colorado'),
        ('NORTHEAST', 'Connecticut'),
        ('NORTHEAST', 'Delaware'),
        ('NORTHEAST', 'District of Columbia'),
        ('SOUTH', 'Florida'),
        ('SOUTH', 'Georgia'),
        ('PACIFIC', 'Hawaii'),
        ('FRONTIER', 'Idaho'),
        ('MIDWEST', 'Illinois'),
        ('MIDWEST', 'Indiana'),
        ('MIDWEST', 'Iowa'),
        ('FRONTIER', 'Kansas'),
        ('SOUTH', 'Kentucky'),
        ('SOUTH', 'Louisiana'),
        ('NORTHEAST', 'Maine'),
        ('NORTHEAST', 'Maryland'),
        ('NORTHEAST', 'Massachusetts'),
        ('MIDWEST', 'Michigan'),
        ('MIDWEST', 'Minnesota'),
        ('SOUTH', 'Mississippi'),
        ('MIDWEST', 'Missouri'),
        ('FRONTIER', 'Montana'),
        ('FRONTIER', 'Nebraska'),
        ('PACIFIC', 'Nevada'),
        ('NORTHEAST', 'New Hampshire'),
        ('NORTHEAST', 'New Jersey'),
        ('FRONTIER', 'New Mexico'),
        ('NORTHEAST', 'New York'),
        ('SOUTH', 'North Carolina'),
        ('MIDWEST', 'North Dakota'),
        ('MIDWEST', 'Ohio'),
        ('FRONTIER', 'Oklahoma'),
        ('PACIFIC', 'Oregon'),
        ('NORTHEAST', 'Pennsylvania'),
        ('NORTHEAST', 'Rhode Island'),
        ('SOUTH', 'South Carolina'),
        ('MIDWEST', 'South Dakota'),
        ('SOUTH', 'Tennessee'),
        ('FRONTIER', 'Texas'),
        ('FRONTIER', 'Utah'),
        ('NORTHEAST', 'Vermont'),
        ('SOUTH', 'Virginia'),
        ('PACIFIC', 'Washington'),
        ('SOUTH', 'West Virginia'),
        ('MIDWEST', 'Wisconsin'),
        ('FRONTIER', 'Wyoming')], validators=[DataRequired()])

    icyfire_team = SelectField('What is the name of your team?', choices=[
        ('00', 'Not applicable. I am a Region Lead.'),
        ('ALPHA', 'Team Alpha'),
        ('BRAVO', 'Team Bravo'),
        ('CHARLIE', 'Team Charlie'),
        ('DELTA', 'Team Delta'),
        ('ECHO', 'Team Echo'),
        ('FOXTROT', 'Team Foxtrot'),
        ('GOLF', 'Team Golf'),
        ('HOTEL', 'Team Hotel'),
        ('INDIGO', 'Team Indigo'),
        ('JULIET', 'Team Juliet')], validators=[DataRequired()])

    icyfire_agent = SelectField("What is your agent number?", choices=[
        ('00', 'Not applicable. I am a Team Lead.'),
        ('01', '1'),
        ('02', '2'),
        ('03', '3'),
        ('04', '4'),
        ('05', '5'),
        ('06', '6'),
        ('07', '7'),
        ('08', '8'),
        ('09', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('15', '15')], validators=[DataRequired()])

    first_name = StringField('First name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last name', validators=[DataRequired(), Length(max=50)])
    phone_number = StringField('Phone number', validators=[DataRequired(), Length(min=10, max=10), phone_check])
    email = StringField('IcyFire email', validators=[DataRequired(), Email(), Length(max=120), icyfire_email_check])
    password = PasswordField('Password (8 characters minimum)', validators=[DataRequired(), Length(min=8)])
    verify_password = PasswordField('Verify password', validators=[DataRequired(), password_check])
    submit = SubmitField('Register')

    def validate_email(self, email):
        '''
        If an account already exists with that email address, this check raises a ValidationError.
        '''
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
    
    def validate_crta(self, icyfire_region, icyfire_team, icyfire_agent):
        '''
        If an account already exists with that CRTA code, this check raises a ValidationError.
        '''
        crta = 'USA-' + icyfire_region.data + '-' + icyfire_team.data + '-' + icyfire_agent.data
        icyfire_crta = User.query.filter_by(icyfire_crta=crta).first()
        if icyfire_crta is not None:
            raise ValidationError('A user already exists with that CRTA code. Please contact your administrator.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request password reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    verify_password = PasswordField('Verify password', validators=[DataRequired(), password_check])
    submit = SubmitField('Submit')

# FACEBOOK
class FacebookCreds(FlaskForm):
    alias = StringField('Account alias (e.g. Facebook-1)', validators=[DataRequired(), Length(max=50)])
    access_token = StringField('Access token', validators=[DataRequired()])
    schedule_monday = SelectField('Schedule post on Mondays', coerce=int, validators=[DataRequired()])
    schedule_tuesday = SelectField('Schedule post on Tuesdays', coerce=int, validators=[DataRequired()])
    schedule_wednesday = SelectField('Schedule post on Wednesdays', coerce=int, validators=[DataRequired()])
    schedule_thursday = SelectField('Schedule post on Thursdays', coerce=int, validators=[DataRequired()])
    schedule_friday = SelectField('Schedule post on Fridays', coerce=int, validators=[DataRequired()])
    schedule_saturday = SelectField('Schedule post on Saturdays', coerce=int, validators=[DataRequired()])
    schedule_sunday = SelectField('Schedule post on Sundays', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def check_creds(self, access_token):
        if request.endpoint == 'auth.edit_cred':
            pass
        try:
            graph = facebook.GraphAPI(access_token=access_token.data)
            graph.put_object(parent_object='me', connection_name='feed', message='How many tickles does it take to get an octopus to laugh?\n\nTen-ticles.')
        except:
            raise ValidationError("Can't verify your credentials. Please try again.")
    
    def check_time_slot(self, schedule_monday, schedule_tuesday, schedule_wednesday, schedule_thursday, schedule_friday, schedule_saturday, schedule_sunday):
        if schedule_monday.data == '0' and schedule_tuesday.data == '0' and schedule_wednesday.data == '0' and schedule_thursday.data == '0' and schedule_friday.data == '0' and schedule_saturday.data == '0' and schedule_sunday == '0':
            raise ValidationError("No time slot chosen. Please try again.")

# TWITTER
class TwitterCreds(FlaskForm):
    alias = StringField('Account alias (e.g. Twitter-1)', validators=[DataRequired(), Length(max=50)])
    consumer_key = StringField('Consumer key', validators=[DataRequired()])
    consumer_secret = StringField('Consumer secret', validators=[DataRequired()])
    access_token_key = StringField('Access token key', validators=[DataRequired()])
    access_token_secret = StringField('Access token secret', validators=[DataRequired()])
    schedule_monday = SelectField('Schedule post on Mondays', coerce=int, validators=[DataRequired()])
    schedule_tuesday = SelectField('Schedule post on Tuesdays', coerce=int, validators=[DataRequired()])
    schedule_wednesday = SelectField('Schedule post on Wednesdays', coerce=int, validators=[DataRequired()])
    schedule_thursday = SelectField('Schedule post on Thursdays', coerce=int, validators=[DataRequired()])
    schedule_friday = SelectField('Schedule post on Fridays', coerce=int, validators=[DataRequired()])
    schedule_saturday = SelectField('Schedule post on Saturdays', coerce=int, validators=[DataRequired()])
    schedule_sunday = SelectField('Schedule post on Sundays', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def check_creds(self, consumer_key, consumer_secret, access_token_key, access_token_secret):
        if request.endpoint == 'auth.edit_cred':
            pass
        try:
            api = twitter.Api(consumer_key=consumer_key.data, consumer_secret=consumer_secret.data, access_token_key=access_token_key.data, access_token_secret=access_token_secret.data)
            api.PostUpdate("What's the difference between bird flu and swine flu?\n\nOne requires tweetment and the other an oinkment.")
        except:
            raise ValidationError("Can't verify your credentials. Please try again.")

    def check_time_slot(self, schedule_monday, schedule_tuesday, schedule_wednesday, schedule_thursday, schedule_friday, schedule_saturday, schedule_sunday):
        if schedule_monday.data == '0' and schedule_tuesday.data == '0' and schedule_wednesday.data == '0' and schedule_thursday.data == '0' and schedule_friday.data == '0' and schedule_saturday.data == '0' and schedule_sunday == '0':
            raise ValidationError("No time slot chosen. Please try again.")

# TUMBLR
class TumblrCreds(FlaskForm):
    alias = StringField('Account alias (e.g. Tumblr-1)', validators=[DataRequired(), Length(max=50)])
    consumer_key = StringField('Consumer key', validators=[DataRequired()])
    consumer_secret = StringField('Consumer secret', validators=[DataRequired()])
    oauth_token = StringField('OAuth token', validators=[DataRequired()])
    oauth_secret = StringField('OAuth secret', validators=[DataRequired()])
    blog_name = StringField('URL for your blog', validators=[DataRequired()])
    schedule_monday = SelectField('Schedule post on Mondays', coerce=int, validators=[DataRequired()])
    schedule_tuesday = SelectField('Schedule post on Tuesdays', coerce=int, validators=[DataRequired()])
    schedule_wednesday = SelectField('Schedule post on Wednesdays', coerce=int, validators=[DataRequired()])
    schedule_thursday = SelectField('Schedule post on Thursdays', coerce=int, validators=[DataRequired()])
    schedule_friday = SelectField('Schedule post on Fridays', coerce=int, validators=[DataRequired()])
    schedule_saturday = SelectField('Schedule post on Saturdays', coerce=int, validators=[DataRequired()])
    schedule_sunday = SelectField('Schedule post on Sundays', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def check_creds(self, consumer_key, consumer_secret, oauth_token, oauth_secret, blog_name):
        if request.endpoint == 'auth.edit_cred':
            pass
        try:
            client = pytumblr.TumblrRestClient(consumer_key.data, consumer_secret.data, oauth_token.data, oauth_secret.data)
            client.create_text(blog_name.data, state='published', title='Why did the bike fall over?', body='It was two tired.')
        except:
            raise ValidationError("Can't verify your credentials. Please try again.")
    
    def check_time_slot(self, schedule_monday, schedule_tuesday, schedule_wednesday, schedule_thursday, schedule_friday, schedule_saturday, schedule_sunday):
        if schedule_monday.data == '0' and schedule_tuesday.data == '0' and schedule_wednesday.data == '0' and schedule_thursday.data == '0' and schedule_friday.data == '0' and schedule_saturday.data == '0' and schedule_sunday == '0':
            raise ValidationError("No time slot chosen. Please try again.")

# REDDIT
class RedditCreds(FlaskForm):
    alias = StringField('Account alias (e.g. Reddit-1)', validators=[DataRequired(), Length(max=50)])
    target_subreddit = StringField('URL for your subreddit', validators=[DataRequired()])
    client_id = StringField('Client ID', validators=[DataRequired()])
    client_secret = StringField('Client secret', validators=[DataRequired()])
    user_agent = StringField('User agent', validators=[DataRequired()])
    username = StringField('Reddit username', validators=[DataRequired()])
    password = PasswordField('Reddit password', validators=[DataRequired()])
    schedule_monday = SelectField('Schedule post on Mondays', coerce=int, validators=[DataRequired()])
    schedule_tuesday = SelectField('Schedule post on Tuesdays', coerce=int, validators=[DataRequired()])
    schedule_wednesday = SelectField('Schedule post on Wednesdays', coerce=int, validators=[DataRequired()])
    schedule_thursday = SelectField('Schedule post on Thursdays', coerce=int, validators=[DataRequired()])
    schedule_friday = SelectField('Schedule post on Fridays', coerce=int, validators=[DataRequired()])
    schedule_saturday = SelectField('Schedule post on Saturdays', coerce=int, validators=[DataRequired()])
    schedule_sunday = SelectField('Schedule post on Sundays', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def check_creds(self, client_id, client_secret, user_agent, username, password):
        if request.endpoint == 'auth.edit_cred':
            pass
        try:
            reddit = praw.Reddit(client_id=client_id.data, client_secret=client_secret.data, user_agent=user_agent.data, username=username.data, password=password.data)
            reddit.subreddit(target_subreddit.data).submit('What do cows most like to read?', selftext='Cattle-logs.')
        except:
            raise ValidationError("Can't verify your credentials. Please try again.")
    
    def check_time_slot(self, schedule_monday, schedule_tuesday, schedule_wednesday, schedule_thursday, schedule_friday, schedule_saturday, schedule_sunday):
        if schedule_monday.data == '0' and schedule_tuesday.data == '0' and schedule_wednesday.data == '0' and schedule_thursday.data == '0' and schedule_friday.data == '0' and schedule_saturday.data == '0' and schedule_sunday == '0':
            raise ValidationError("No time slot chosen. Please try again.")