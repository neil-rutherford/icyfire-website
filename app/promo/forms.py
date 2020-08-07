from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import Lead

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

class LeadForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=50)])
    company_name = StringField("Company name", validators=[DataRequired(), Length(max=100)])
    job_title = StringField("Job title", validators=[DataRequired(), Length(max=100)])
    number_of_employees = SelectField("How many employees does your company you have?", choices=[
        ("1", "Just me"),
        ("2", "2-10"),
        ("3", "11-50"),
        ("4", "51-250"),
        ("5", "251-500"),
        ("6", "501-1,000"),
        ("7", "1,001-5,000"),
        ("8", "5,001-10,000"),
        ("9", "10,000+")
    ], validators=[DataRequired()])
    time_zone = SelectField("Time zone", choices=[
        ("1", "Eastern Time"),
        ("2", "Central Time"),
        ("3", "Mountain Time"),
        ("4", "Pacific Time"),
        ("5", "Alaska Time"),
        ("6", "Hawaii-Aleutian Time"),
        ("7", "Other")
    ], validators=[DataRequired()])
    phone_number = StringField("Phone number", validators=[DataRequired(), Length(min=10, max=10), phone_check])
    email = StringField("Business email", validators=[DataRequired(), Email(), Length(max=50)])
    contact_preference = SelectField("How would you like us to contact you?", choices=[
        ('0', 'No preference'),
        ('1', 'Email'),
        ('2', 'Phone call')
    ], validators=[DataRequired()])
    time_preference = SelectField("What time of day would you like us to contact you?", choices=[
        ("0", "Any time on a work day"),
        ("1", "Early morning (8-9:30am)"),
        ("2", "Late morning (9:30-11am)"),
        ("3", "Lunch break (11am-1pm)"),
        ("4", "Early afternoon (1-3pm)"),
        ("5", "Late afternoon (3-5pm)")
    ], validators=[DataRequired()])
    email_opt_in = BooleanField("Want to subscribe to our mailing list? (No spam, we promise.)")
    submit = SubmitField("Let's talk")

class SaleForm(FlaskForm):
    client_name = StringField
    client_street_address = StringField
    client_city = StringField
    client_state = StringField
    client_country = StringField
    client_zip = StringField
    client_phone_country = StringField
    client_phone_number = StringField
    client_email = StringField
    submit = SubmitField