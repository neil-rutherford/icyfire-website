from flask import render_template, flash, redirect, url_for, request, jsonify, Response, send_from_directory
from app import app, db
from app.forms import LoginForm, DomainRegistrationForm, UserRegistrationForm, ContractorRegistrationForm, ShortTextPostForm, LongTextPostForm, ImagePostForm, VideoPostForm, SaleForm, GenerateIcaForm
from app.models import Domain, User, FacebookPost, TwitterPost, TumblrPost, RedditPost, YoutubePost, LinkedinPost, Ewok, Sentry, CountryLead, RegionLead, TeamLead, Agent
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import logging
from datetime import datetime, date
import uuid
import pdfrw
import os

'''
TO-DO:

    - Finish link_social()
    - Finish link_social.html

    - DOMAIN REGISTRATION
        + Link social networks and store tokens
        + Request time slots
        + User registration (must be linked to domain) (permissions)
    - USER INTERFACE
        + Create
        + Read
        + Update
        + Delete
    - API
        + Read
        + Delete
        + Get creds
    - LOGIN
    - ERROR HANDLING
    - EMAIL SUPPORT
    - ARTICLES AND MARKETING PAGES
    - HELP PAGES AND TUTORIALS
    - SECURITY
        + Domain-level
        + App-level
'''

def make_sentry(user_id, ip_address, endpoint, status_code, status_message):
    activity = Sentry(ip_address=str(ip_address), user_id=int(user_id), endpoint=str(endpoint))
    activity.status_code = int(status_code)
    activity.status_message = str(status_message)
    db.session.add(activity)
    db.session.commit()

def fill_pdf_template(input_path, output_path, data_dict):
    ANNOT_KEY = '/Annots'
    ANNOT_FIELD_KEY = '/T'
    ANNOT_VAL_KEY = '/V'
    ANNOT_RECT_KEY = '/Rect'
    SUBTYPE_KEY = '/Subtype'
    WIDGET_SUBTYPE_KEY = '/Widget'
    template_pdf = pdfrw.PdfReader(input_path)
    annotations = template_pdf.pages[0][ANNOT_KEY]
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key in data_dict.keys():
                    annotation.update(
                        pdfrw.PdfDict(AP=data_dict[key], V='{}'.format(data_dict[key]))
                    )
    pdfrw.PdfWriter().write(output_path, template_pdf)

# Post management

# Help

# Sales pathway

@app.route('/create/sale', methods=['GET', 'POST'])
@login_required
def create_sale():
    if current_user.icyfire_crta is None or str(current_user.icyfire_crta).split('-')[3] == '00':
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/sale', status_code=403, status_message='Permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))
    form = SaleForm()
    if form.validate_on_submit():
        sale = Sale(client_name=str(form.client_name.data))
        sale.agent_id = current_user.id
        sale.client_street_address = str(form.client_street_address.data)
        sale.client_city = str(form.client_city.data)
        sale.client_state = str(form.client_state.data)
        sale.client_country = 'United States'
        sale.client_zip = str(form.client_zip.data)
        sale.client_phone_country = int(1)
        sale.client_phone_number = int(form.client_phone_number.data)
        sale.client_email = str(form.client_email.data)
        sale.unit_price = float(3000)
        sale.quantity = int(form.quantity.data)
        sale.subtotal = sale.quantity * sale.unit_price
        sales_tax_dict = {
            'Alabama': 0.04,
            'Alaska': 0.00,
            'Arizona': 0.056,
            'Arkansas': 0.00,
            'California': 0.00,
            'Colorado': 0.00,
            'Connecticut': 0.01,
            'District of Columbia': 0.06,
            'Delaware': 0.00,
            'Florida': 0.00,
            'Georgia': 0.00,
            'Hawaii': 0.04,
            'Idaho': 0.00,
            'Illinois': 0.00,
            'Indiana': 0.00,
            'Iowa': 0.06,
            'Kansas': 0.00,
            'Kentucky': 0.06,
            'Louisiana': 0.00,
            'Maine': 0.055,
            'Maryland': 0.00,
            'Massachusetts': 0.00,
            'Michigan': 0.00,
            'Minnesota': 0.00,
            'Mississippi': 0.07,
            'Missouri': 0.00,
            'Nebraska': 0.00,
            'Nevada': 0.0685,
            'New Jersey': 0.00,
            'New Mexico': 0.05125,
            'New York': 0.04,
            'North Carolina': 0.00,
            'North Dakota': 0.05,
            'Ohio': 0.0575,
            'Oklahoma': 0.00,
            'Pennsylvania': 0.06,
            'Rhode Island': 0.07,
            'South Carolina': 0.06,
            'South Dakota': 0.045,
            'Tennessee': 0.07,
            'Texas': 0.0625,
            'Utah': 0.061,
            'Vermont': 0.00,
            'Virginia': 0.00,
            'Washington': 0.065,
            'West Virginia': 0.06,
            'Wisconsin': 0.00,
            'Wyoming': 0.00
            # (Source: https://blog.taxjar.com/saas-sales-tax/, https://taxfoundation.org/2020-sales-taxes/)
        }
        sale.sales_tax = sales_tax_dict[str(form.client_state.data)] * sale.subtotal
        sale.total = sale.sales_tax + sale.subtotal
        country, region, team = str(current_user.icyfire_crta).split('-')[0], str(current_user.icyfire_crta).split('-')[1], str(current_user.icyfire_crta).split('-')[2]
        country_lead = CountryLead.query.filter_by(crta_code=country + '-00-00-00').first()
        sale.country_lead_id = country_lead.id
        region_lead = RegionLead.query.filter_by(crta_code=country + '-' + region + '-00-00').first()
        sale.region_lead_id = region_lead.id
        team_lead = TeamLead.query.filter_by(crta_code=country + '-' + region + '-' + team + '-00').first()
        sale.team_lead_id = team_lead.id
        db.session.add(sale)
        db.session.commit()
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/sale', status_code=200, status_message='Sale created.')
        return redirect(url_for('create_invoice', sale_id=sale.id))
    return render_template('create_sale.html', title='New Sale', form=form)

@app.route('/create/invoice/<sale_id>')
def create_invoice(sale_id):
    sale = Sale.query.filter_by(id=sale_id).first()
    agent = Agent.query.filter_by(id=sale.agent_id).first()
    user = User.query.filter_by(id=agent.user_id).first()
    activation_code = str(uuid.uuid4())
    basedir = os.path.abspath(os.path.dirname(__file__))
    data_dict = {
        'invoice_date': sale.timestamp.strftime('%Y-%d-%m'),
        'icyfire_address1': '6558 S Cook Way',
        'icyfire_address2': 'CENTENNIAL, COLORADO, USA 80121',
        'agent_name': '{} {}'.format(agent.first_name.upper(), agent.last_name.upper()),
        'agent_email': user.email,
        'agent_phone': '+{}-({})-{}-{}'.format(agent.phone_country, str(agent.phone_number)[0:3], str(agent.phone_number)[3:6], str(agent.phone_number)[6:10]),
        'client_name': sale.client_name.upper(),
        'client_street_address': sale.client_street_address.upper(),
        'client_city': sale.client_city.upper(),
        'client_state': sale.client_state.upper(),
        'client_zip_code': sale.client_zip,
        'client_email': sale.client_email,
        'client_phone': '+{}-({})-{}-{}'.format(sale.client_phone_country, str(sale.client_phone_number)[0:3], str(sale.client_phone_number)[3:6], str(sale.client_phone_number)[6:10]),
        'quantity': sale.quantity,
        'unit_price': '${}'.format(float(sale.unit_price)),
        'subtotal': '${}'.format(float(sale.subtotal)),
        'sales_tax': '${}'.format(float(sale.sales_tax)),
        'total_due': '${}'.format(float(sale.total)),
        'activation_code': activation_code
    }
    input_file = os.path.join(basedir, 'app', 'static', 'agreements', 'client_invoice_template.pdf')
    output_file = os.path.join(basedir, 'app', 'static', 'records', 'invoices', '{}.pdf'.format(sale_id))
    fill_pdf_template(input_path=input_file, output_path=output_file, data_dict=data_dict)
    domain = Domain(activation_code=activation_code)
    db.session.add(domain)
    db.session.commit()
    return send_from_directory(os.path.join(basedir, 'app', 'static', 'records', 'invoices'), '{}.pdf'.format(sale_id), as_attachment=True)

@app.route('/sales/dashboard')
@login_required
def sales_dashboard():
    crta = current_user.icyfire_crta
    country = str(current_user.icyfire_crta).split('-')[0]
    region = str(current_user.icyfire_crta).split('-')[1]
    team = str(current_user.icyfire_crta).split('-')[2]
    agent = str(current_user.icyfire_crta).split('-')[3]
    start = date(year={}, month={}, day=1).format(datetime.utcnow().strftime('%Y'), datetime.utcnow().strftime('%m'))
    if crta is None:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/sales/dashboard', status_code=403, status_message='Permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))
    # Country lead
    if country != '00' and region == '00' and team == '00' and agent == '00':
        country_lead = CountryLead.query.filter_by(crta_code=crta).first()
        sales = Sale.query.filter_by(country_lead_id=country_lead.id).filter(Sale.timestamp >= start)
        subs = country_lead.region_leads
        label = 'country_lead'
        title = 'Dashboard - {} Country Lead'.format(country)
    # Region lead
    elif country != '00' and region != '00' and team == '00' and agent == '00':
        region_lead = RegionLead.query.filter_by(crta_code=crta).first()
        sales = Sale.query.filter_by(region_lead_id=region_lead.id).filter(Sale.timestamp >= start)
        subs = region_lead.team_leads
        label = 'region_lead'
        title = 'Dashboard - {} Region Lead'.format(region)
    # Team lead
    elif country != '00' and region != '00' and team != '00' and agent == '00':
        team_lead = TeamLead.query.filter_by(crta_code=crta).first()
        sales = Sale.query.filter_by(team_lead_id=team_lead.id).filter(Sale.timestamp >= start)
        subs = team_lead.agents
        label = 'team_lead'
        title = 'Dashboard - {} Team Lead'.format(team)
    # Agent
    elif country != '00' and region != '00' and team != '00' and agent != '00':
        agent = Agent.query.filter_by(crta_code=crta).first()
        sales = Sale.query.filter_by(agent_id=agent.id).filter(Sale.timestamp >= start)
        subs = None
        label = 'agent'
        title = 'Dashboard - Agent {}'.format(agent)
    # Else??
    else:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/sales/dashboard', status_code=400, status_message='Malformed request; content not found.')
        flash("ERROR: Couldn't process that request.")
        return redirect(url_for('dashboard'))
    return render_template('sales_dashboard.html', sales=sales, subs=subs, title=title, label=label)

@app.route('/legal/user/privacy-policy', methods=['GET'])
def privacy_policy():
    if current_user.is_authenticated:
        domain = Domain.query.filter_by(id=current_user.domain_id).first()
        user = User.query.filter_by(id=current_user.id).first()
        incidents = Sentry.query.filter_by(user_id=current_user.id).all()
        crta = current_user.icyfire_crta
        country = str(current_user.icyfire_crta).split('-')[0]
        region = str(current_user.icyfire_crta).split('-')[1]
        team = str(current_user.icyfire_crta).split('-')[2]
        agent = str(current_user.icyfire_crta).split('-')[3]
        if crta is None:
            contractor = None
            sales = None
        elif country != '00' and region == '00' and team == '00' and agent == '00':
            contractor = CountryLead.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(country_lead_id=contractor.id).all()
        elif country != '00' and region != '00' and team == '00' and agent == '00':
            contractor = RegionLead.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(region_lead_id=contractor.id).all()
        elif country != '00' and region != '00' and team != '00' and agent == '00':
            contractor = TeamLead.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(team_lead_id=contractor.id).all()
        elif country != '00' and region != '00' and team != '00' and agent != '00':
            contractor = Agent.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(agent_id=contractor.id).all()
    return render_template('privacy_policy.html', domain=domain, user=user, contractor=contractor, sales=sales, incidents=incidents, title='Privacy Policy')

@app.route('/legal/user/cookie-policy', methods=['GET'])
def cookie_policy():
    return render_template('cookie_policy.html', title='Cookie Policy')

@app.route('/legal/user/terms-of-service', methods=['GET'])
def terms_of_service():
    return render_template('terms_of_service.html', title='Terms of Service')

@app.route('/legal/contractor/ica', methods=['GET'])
@login_required
def independent_contractor_agreement():
    form = GenerateIcaForm()
    if form.validate_on_submit():
        basedir = os.path.abspath(os.path.dirname(__file__))
        data_dict = {
            'contract_day': datetime.utcnow().strftime('%d'),
            'contract_month': datetime.utcnow().strftime('%B'),
            'contract_year': datetime.utcnow().strftime('%Y'),
            'contractor_name1': '{} {}'.format(str(form.first_name.data), str(form.last_name.data)),
            'client_address1': '6558 S Cook Way',
            'client_address2': 'Centennial, Colorado 80121',
            'contractor_address1': '{}'.format(str(form.street_address.data)),
            'contractor_address2': '{}, {} {}'.format(str(form.city.data), str(form.state.data), str(form.zip_code.data)),
            'contract_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'contractor_name2': '{} {}'.format(str(form.first_name.data), str(form.last_name.data))
        }
        if str(form.contractor_type.data) == 'agent':
            input_path = os.path.join(basedir, 'app', 'static', 'agreements', 'agent_ica.pdf')
            output_path = os.path.join(basedir, 'app', 'static', 'records', 'contracts', '{}_ica.pdf'.format(str(form.last_name.data)))
            fill_pdf_template(input_path=input_path, output_path=output_path, data_dict=data_dict)
        elif str(form.contractor_type.data) == 'team_lead':
            input_path = os.path.join(basedir, 'app', 'static', 'agreements', 'team_lead_ica.pdf')
            output_path = os.path.join(basedir, 'app', 'static', 'records', 'contracts', '{}_ica.pdf'.format(str(form.last_name.data)))
            fill_pdf_template(input_path=input_path, output_path=output_path, data_dict=data_dict)
        elif str(form.contractor_type.data) == 'region_lead':
            input_path = os.path.join(basedir, 'app', 'static', 'agreements', 'region_lead_ica.pdf')
            output_path = os.path.join(basedir, 'app', 'static', 'records', 'contracts', '{}_ica.pdf'.format(str(form.last_name.data)))
            fill_pdf_template(input_path=input_path, output_path=output_path, data_dict=data_dict)
        return send_from_directory(os.path.join(basedir, 'app', 'static', 'records', 'contracts', '{}_ica.pdf'.format(str(form.last_name.data)))
    return render_template('independent_contractor_agreement.html', title='Generate Independent Contractor Agreement', form=form)
