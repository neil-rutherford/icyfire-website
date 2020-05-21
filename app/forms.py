from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User, Domain
from flask_login import current_user

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

class SaleForm(FlaskForm):
    client_name = StringField('Client name', validators=[DataRequired(), Length(max=100)])
    client_street_address = StringField('Street address', validators=[DataRequired(), Length(max=100)])
    client_city = StringField('City', validators=[DataRequired(), Length(max=60)])
    client_state = SelectField('State', choices=[
        ('Alabama','Alabama'),
        ('Alaska', 'Alaska'),
        ('Arizona', 'Arizona'),
        ('Arkansas', 'Arkansas'),
        ('California', 'California'),
        ('Colorado', 'Colorado'),
        ('Connecticut', 'Connecticut'),
        ('District of Columbia', 'District of Columbia'),
        ('Delaware', 'Delaware'),
        ('Florida', 'Florida'),
        ('Georgia', 'Georgia'),
        ('Hawaii', 'Hawaii'),
        ('Idaho', 'Idaho'),
        ('Illinois', 'Illinois'),
        ('Indiana', 'Indiana'),
        ('Iowa', 'Iowa'),
        ('Kansas', 'Kansas'),
        ('Kentucky', 'Kentucky'),
        ('Louisiana', 'Louisiana'),
        ('Maine', 'Maine'),
        ('Maryland', 'Maryland'),
        ('Massachusetts', 'Massachusetts'),
        ('Michigan', 'Michigan'),
        ('Minnesota', 'Minnesota'),
        ('Mississippi', 'Mississippi'),
        ('Missouri', 'Missouri'),
        ('Nebraska', 'Nebraska'),
        ('Nevada', 'Nevada'),
        ('New Jersey', 'New Jersey'),
        ('New Mexico', 'New Mexico'),
        ('New York', 'New York'),
        ('North Carolina', 'North Carolina'),
        ('North Dakota', 'North Dakota'),
        ('Ohio', 'Ohio'),
        ('Oklahoma', 'Oklahoma'),
        ('Pennsylvania', 'Pennsylvania'),
        ('Rhode Island', 'Rhode Island'),
        ('South Carolina', 'South Carolina'),
        ('South Dakota', 'South Dakota'),
        ('Tennessee', 'Tennessee'),
        ('Texas', 'Texas'),
        ('Utah', 'Utah'),
        ('Vermont', 'Vermont'),
        ('Virginia', 'Virginia'),
        ('Washington', 'Washington'),
        ('West Virginia', 'West Virginia'),
        ('Wisconsin', 'Wisconsin'),
        ('Wyoming', 'Wyoming')
    ],
    validators=[DataRequired(), Length(max=50)])
    client_zip = StringField('ZIP code', validators=[DataRequired(), Length(max=15)])
    client_phone_number = StringField('Contact phone number', validators=[DataRequired(), Length(min=10, max=10), phone_check])
    client_email = StringField('Contact email', validators=[DataRequired(), Email(), Length(max=120)])
    quantity = StringField('Quantity sold', validators=[DataRequired(), phone_check])
    submit = SubmitField('Submit')

class GenerateIcaForm(FlaskForm):
    contractor_type = SelectField('Contractor type', choices=[
        ('agent', 'Agent'),
        ('team_lead', 'Team lead'),
        ('region_lead', 'Region lead')
    ], validators=[DataRequired()])
    first_name = StringField('First name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last name', validators=[DataRequired(), Length(max=50)])
    street_address = StringField('Mailing address', validators=[DataRequired(), Length(max=35)])
    city = StringField('City', validators=[DataRequired(), Length(max=35)])
    state = StringField('State', validators=[DataRequired(), Length(max=15)])
    zip_code = StringField('ZIP code', validators=[DataRequired(), Length(max=9)])
    submit = SubmitField('Generate ICA')