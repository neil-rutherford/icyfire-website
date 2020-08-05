from flask import render_template, flash, redirect, url_for, request, send_from_directory
from app import db
from app.models import Sentry, CountryLead, RegionLead, TeamLead, Agent, Sale, Domain
from app.sales.forms import SaleForm
from flask_login import current_user, login_required
import os
import uuid
from app.sales import bp
from datetime import datetime, date
import pdfrw

# HELPER FUNCTIONS
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

def fill_pdf(input_path, output_path, data_dict):
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

# SALES DASHBOARD
@bp.route('/sales/dashboard')
@login_required
def dashboard():
    '''
    - Sentry logs:
        + 200 = ok; content has been viewed (`status_message`=view_type)
        + 400 = malformed request; catch-all that probably means the server is melting or something
        + 403 = permission denied; a normal user is trying to access the sales dash
    - Shows sales data for that individual's domain, as well as contact info for their subordinates
    '''
    crta = current_user.icyfire_crta
    if crta is None:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=403, status_message='Permission denied.')
        flash("ERROR: You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    country = str(current_user.icyfire_crta).split('-')[0]
    region = str(current_user.icyfire_crta).split('-')[1]
    team = str(current_user.icyfire_crta).split('-')[2]
    agent = str(current_user.icyfire_crta).split('-')[3]
    start = date(year={}, month={}, day=1).format(datetime.utcnow().strftime('%Y'), datetime.utcnow().strftime('%m'))
    # Country lead
    if country != '00' and region == '00' and team == '00' and agent == '00':
        country_lead = CountryLead.query.filter_by(crta_code=crta).first()
        #sales = Sale.query.filter_by(country_lead_id=country_lead.id).filter(Sale.timestamp >= start)
        sales = Sale.query.filter(Sale.country_lead_id == country_lead.id, Sale.timestamp >= start).all()
        subs = country_lead.region_leads
        label = 'country_lead'
        title = 'Dashboard - {} Country Lead'.format(country)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=200, status_message='country_lead')
    # Region lead
    elif country != '00' and region != '00' and team == '00' and agent == '00':
        region_lead = RegionLead.query.filter_by(crta_code=crta).first()
        #sales = Sale.query.filter_by(region_lead_id=region_lead.id).filter(Sale.timestamp >= start)
        sales = Sale.query.filter(Sale.region_lead_id == region_lead.id, Sale.timestamp >= start).all()
        subs = region_lead.team_leads
        label = 'region_lead'
        title = 'Dashboard - {} Region Lead'.format(region)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=200, status_message='region_lead')
    # Team lead
    elif country != '00' and region != '00' and team != '00' and agent == '00':
        team_lead = TeamLead.query.filter_by(crta_code=crta).first()
        #sales = Sale.query.filter_by(team_lead_id=team_lead.id).filter(Sale.timestamp >= start)
        sales = Sale.query.filter(Sale.team_lead_id == team_lead.id, Sale.timestamp >= start).all()
        subs = team_lead.agents
        label = 'team_lead'
        title = 'Dashboard - {} Team Lead'.format(team)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=200, status_message='team_lead')
    # Agent
    elif country != '00' and region != '00' and team != '00' and agent != '00':
        agent = Agent.query.filter_by(crta_code=crta).first()
        #sales = Sale.query.filter_by(agent_id=agent.id).filter(Sale.timestamp >= start)
        sales = Sale.query.filter(Sale.agent_id == agent.id, Sale.timestamp >= start).all()
        subs = None
        label = 'agent'
        title = 'Dashboard - Agent {}'.format(agent)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=200, status_message='agent')
    # Else??
    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=400, status_message='Malformed request; content not found.')
        flash("ERROR: Couldn't process that request.")
        return redirect(url_for('main.dashboard'))
    return render_template('sales/sales_dashboard.html', sales=sales, subs=subs, title=title, label=label)

# CREATE SALE
@bp.route('/create/sale', methods=['GET', 'POST'])
@login_required
def create_sale():
    '''
    - Sentry logs:
        + 403: permission denied; not a contractor OR not an agent
        + 200: ok; sale created
    - Makes a sale and generates an invoice
    '''
    if current_user.icyfire_crta is None or str(current_user.icyfire_crta).split('-')[3] == '00':
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.create_sale', status_code=403, status_message='Permission denied.')
        flash("ERROR: Only IcyFire agents are able to create sales.")
        return redirect(url_for('sales.dashboard'))
    form = SaleForm()
    if form.validate_on_submit():
        agent = Agent.query.filter_by(crta_code=current_user.icyfire_crta).first()
        unit_price = float(3000)
        quantity = int(form.quantity.data)
        subtotal = unit_price * quantity
        sale = Sale(client_name=str(form.client_name.data))
        sale.agent_id = agent.id
        sale.client_street_address = str(form.client_street_address.data)
        sale.client_city = str(form.client_city.data)
        sale.client_state = str(form.client_state.data)
        sale.client_country = 'United States'
        sale.client_zip = str(form.client_zip.data)
        sale.client_phone_country = int(1)
        sale.client_phone_number = int(form.client_phone_number.data)
        sale.client_email = str(form.client_email.data)
        sale.unit_price = unit_price
        sale.quantity = quantity
        sale.subtotal = subtotal
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
        sales_tax = sales_tax_dict[str(form.client_state.data)] * subtotal
        sale.sales_tax = sales_tax
        sale.total = sale.sales_tax + sale.subtotal
        country, region, team = str(current_user.icyfire_crta).split('-')[0], str(current_user.icyfire_crta).split('-')[1], str(current_user.icyfire_crta).split('-')[2]
        country_lead = CountryLead.query.filter_by(crta_code=country + '-00-00-00').first()
        sale.country_lead_id = country_lead.id
        region_lead = RegionLead.query.filter_by(crta_code=country + '-' + region + '-00-00').first()
        sale.region_lead_id = region_lead.id
        team_lead = TeamLead.query.filter_by(crta_code=country + '-' + region + '-' + team + '-00').first()
        sale.team_lead_id = team_lead.id
        activation_code = str(uuid.uuid4())
        basedir = os.path.abspath(os.path.dirname(__file__))
        data_dict = {
            'invoice_date': datetime.utcnow().strftime('%Y-%d-%m'),
            'icyfire_address1': '6058 S HILL ST',
            'icyfire_address2': 'LITTLETON, COLORADO, USA 80120',
            'agent_name': '{} {}'.format(agent.first_name, agent.last_name),
            'agent_email': current_user.email,
            'agent_phone': '+{}-({})-{}-{}'.format(agent.phone_country, str(agent.phone_number)[0:3], str(agent.phone_number)[3:6], str(agent.phone_number)[6:10]),
            'client_name': str(form.client_name.data),
            'client_street_address': str(form.client_street_address.data),
            'client_city': str(form.client_state.data),
            'client_state': str(form.client_state.data),
            'client_zip_code': str(form.client_zip.data),
            'client_email': str(form.client_email.data),
            'client_phone': '+{}-({})-{}-{}'.format(1, str(form.client_phone_number.data)[0:3], str(form.client_phone_number.data)[3:6], str(form.client_phone_number.data)[6:10]),
            'quantity': quantity,
            'unit_price': '${}'.format(unit_price),
            'subtotal': '${}'.format(subtotal),
            'sales_tax': '${}'.format(sales_tax),
            'total_due': '${}'.format(sales_tax + subtotal),
            'activation_code': activation_code
        }
        fill_pdf(input_path=os.path.join(basedir, 'app', 'static', 'agreements', 'client_invoice_template.pdf'), output_path=os.path.join(basedir, 'app', 'static', 'records', '{}_template.pdf'.format(str(form.client_name.data))), data_dict=data_dict)
        sale.invoice_url = url_for('sales.get_invoice', '{}_invoice.pdf'.format(str(form.client_name.data)))
        domain = Domain(activation_code=activation_code)
        db.session.add(sale)
        db.session.add(domain)
        db.session.commit()
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.create_sale', status_code=200, status_message='Sale created.')
        return redirect(url_for('sales.dashboard'))
    return render_template('sales/create_sale.html', title='New Sale', form=form)

# GET INVOICE
@bp.route('/sale/invoice/<filename>', methods=['GET'])
def get_invoice(filename):
    basedir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(os.path.join(basedir, 'app', 'static', 'records'), filename, as_attachment=True)