from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired

class DomainForm(FlaskForm):
    domain_name = StringField('Domain name')
    sale_id = SelectField('Sale', coerce=int)
    activation_code = StringField('Activation code')
    submit = SubmitField('Submit')

class UserForm(FlaskForm):
    email = StringField('Email')
    password = StringField('Password')
    domain_id = SelectField('Domain', coerce=int)
    is_admin = SelectField('Admin', choices=[('True', 'True'), ('False', 'False')])
    is_create = SelectField('Create', choices=[('True', 'True'), ('False', 'False')])
    is_read = SelectField('Read', choices=[('True', 'True'), ('False', 'False')])
    is_update = SelectField('Update', choices=[('True', 'True'), ('False', 'False')])
    is_delete = SelectField('Delete', choices=[('True', 'True'), ('False', 'False')])
    email_opt_in = SelectField('Email opt-in', choices=[('True', 'True'), ('False', 'False')])
    icyfire_crta = StringField('IcyFire CRTA')
    submit = SubmitField('Submit')

class CountryLeadForm(FlaskForm):
    user_id = SelectField('User', coerce=int)
    first_name = StringField('First name')
    last_name = StringField('Last name')
    phone_number = StringField('Phone number')
    email = StringField('Email')
    crta_code = StringField('IcyFire CRTA')
    submit = SubmitField('Submit')

class RegionLeadForm(FlaskForm):
    user_id = SelectField('User', coerce=int)
    first_name = StringField('First name')
    last_name = StringField('Last name')
    phone_number = StringField('Phone number')
    email = StringField('Email')
    crta_code = StringField('IcyFire CRTA')
    country_lead_id = StringField('Country Lead CRTA')
    submit = SubmitField('Submit')

class TeamLeadForm(FlaskForm):
    user_id = SelectField('User', coerce=int)
    first_name = StringField('First name')
    last_name = StringField('Last name')
    phone_number = StringField('Phone number')
    email = StringField('Email')
    crta_code = StringField('IcyFire CRTA')
    region_lead_id = StringField('Region Lead CRTA')
    submit = SubmitField('Submit')

class AgentForm(FlaskForm):
    user_id = SelectField('User', coerce=int)
    first_name = StringField('First name')
    last_name = StringField('Last name')
    phone_number = StringField('Phone number')
    email = StringField('Email')
    crta_code = StringField('IcyFire CRTA')
    team_lead_id = StringField('Team Lead CRTA')
    submit = SubmitField('Submit')

class SaleForm(FlaskForm):
    agent_id = StringField('Agent CRTA')
    team_lead_id = StringField('Team Lead CRTA')
    region_lead_id = StringField('Region Lead CRTA')
    country_lead_id = StringField('Country Lead CRTA')
    client_name = StringField('Client name (company name)')
    client_street_address = StringField('Client street address')
    client_city = StringField('Client city')
    client_state = StringField('Client state')
    client_country = StringField('Client country')
    client_zip = StringField('Client ZIP code')
    client_phone_country = StringField('Client country code')
    client_phone_number = StringField('Client phone number')
    client_email = StringField('Client email')
    unit_price = StringField('Unit price')
    quantity = StringField('Quantity')
    subtotal = StringField('Subtotal')
    sales_tax = StringField('Sales tax')
    total = StringField('Total')
    receipt_url = StringField('Receipt URL')
    payment_reference = StringField('Payment reference')
    submit = SubmitField('Submit')

class LeadForm(FlaskForm):
    agent_id = StringField('Assign to agent (IcyFire CRTA)')
    is_contacted = SelectField('Is contacted', choices=[('True', 'True'), ('False', 'False')])
    first_name = StringField('First name')
    last_name = StringField('Last name')
    company_name = StringField('Company name')
    job_title = StringField('Job title')
    number_of_employees = SelectField('Number of employees', choices=[
        ('1', '1'), 
        ('2', '2-10'),
        ('3', '11-50'), 
        ('4', '51-250'), 
        ('5', '251-500'), 
        ('6','501-1,000'), 
        ('7','1,001-5,000'), 
        ('8','5,001-10,000'), 
        ('9', '10,000+')
    ])
    time_zone = SelectField('Time zone', choices=[
        ('1','Eastern'), 
        ('2','Central'), 
        ('3','Mountain'), 
        ('4','Pacific'), 
        ('5','Alaska'), 
        ('6','Hawaii-Aleutian'), 
        ('7','Other')
    ])
    phone_number = StringField('Phone number')
    email = StringField('Email')
    contact_preference = SelectField('Contact preference', choices=[
        ('0', 'No preference'), 
        ('1', 'Email'), 
        ('2','Phone call')
    ])
    time_preference = SelectField('Time preference', choices=[
        ('0','No preference'), 
        ('1','8:00-9:30am'), 
        ('2','9:30-11:00am'), 
        ('3','11:00am-1:00pm'), 
        ('4','1:00-3:00pm'), 
        ('5','3:00-5:00pm')
    ])
    email_opt_in = SelectField('Email opt-in', choices=[('True', 'True'), ('False', 'False')])
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    domain_var = SelectField('Domain search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'ID'),
        ('domain_name', 'Domain name'),
        ('activation_code', 'Activation code')
    ])
    user_var = SelectField('User search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'ID'),
        ('email', 'Email'),
        ('domain_id', 'Domain ID'),
        ('email_opt_in', 'Email opt in'),
        ('icyfire_crta', 'CRTA')
    ])
    country_lead_var = SelectField('Country Lead search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'ID'),
        ('last_name', 'Last name'),
        ('phone_number', 'Phone number'),
        ('email', 'Email'),
        ('crta_code', 'CRTA')
    ])
    region_lead_var = SelectField('Region Lead search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'ID'),
        ('last_name', 'Last name'),
        ('phone_number', 'Phone number'),
        ('email', 'Email'),
        ('crta_code', 'CRTA')
    ])
    team_lead_var = SelectField('Team Lead search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'ID'),
        ('last_name', 'Last name'),
        ('phone_number', 'Phone number'),
        ('email', 'Email'),
        ('crta_code', 'CRTA')
    ])
    agent_var = SelectField('Agent search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'ID'),
        ('last_name', 'Last name'),
        ('phone_number', 'Phone number'),
        ('email', 'Email'),
        ('crta_code', 'CRTA')
    ])
    sale_var = SelectField('Sale search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'Sale ID'),
        ('agent_id', 'Agent ID'),
        ('team_lead_id', 'Team Lead ID'),
        ('region_lead_id', 'Region Lead ID'),
        ('country_lead_id', 'Country Lead ID'),
        ('client_name', 'Client name'),
        ('client_city', 'Client city'),
        ('client_state', 'Client state'),
        ('client_zip', 'Client ZIP'),
        ('client_phone_number', 'Client phone number'),
        ('payment_reference', 'Payment reference'),
        ('receipt_url', 'Receipt URL')
    ])
    lead_var = SelectField('Lead search criteria', choices=[
        ('0', 'Not searching for this'),
        ('id', 'Lead ID'),
        ('agent_id', 'Agent ID'),
        ('is_contacted', 'Is contacted'),
        ('company_name', 'Company name'),
        ('number_of_employees', 'Number of employees'),
        ('time_zone', 'Time zone'),
        ('phone_number', 'Phone number'),
        ('email', 'Email'),
        ('contact_preference', 'Contact preference'),
        ('time_preference', 'Time preference'),
        ('email_opt_in', 'Email opt in')
    ])
    value = StringField('Search term', validators=[DataRequired()])
    #query_type = SelectField('Query type', choices=[('first', 'First'), ('all', 'All')], validators=[DataRequired()])
    submit = SubmitField('Search >')

    def check_not_all_blank(self, domain_var, user_var, country_lead_var, region_lead_var, team_lead_var, agent_var, sale_var, lead_var):
        if domain_var.data == '0' and user_var.data == '0' and country_lead_var.data == '0' and region_lead_var.data == '0' and team_lead_var.data == '0' and agent_var.data == '0' and sale_var.data == '0' and lead_var.data == '0':
            raise ValidationError("They can't all be blank!")
    
    def check_only_one(self, domain_var, user_var, country_lead_var, region_lead_var, team_lead_var, agent_var, sale_var, lead_var):
        submission_list = [domain_var.data, user_var.data, country_lead_var.data, region_lead_var.data, team_lead_var.data, agent_var.data, sale_var.data, lead_var.data]
        count = 0
        for x in submission_list:
            if x != '0':
                count += 1
        if count > 1:
            raise ValidationError("You can only search for one term at a time!")