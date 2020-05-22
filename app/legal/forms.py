from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length

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