from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app
from app import db, create_app
from app.models import Sentry, Sale, Domain, Lead, Partner#, CountryLead, RegionLead, TeamLead, Agent,
from app.sales.forms import SaleForm
from flask_login import current_user, login_required
import os
import uuid
from app.sales import bp
from datetime import datetime, date
import pdfrw
from app.main.transfer import TransferData
from dotenv import load_dotenv

load_dotenv('.env')

# HELPER FUNCTIONS
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

def write_fillable_pdf(input_pdf_path, output_pdf_path, data_dict):
    ANNOT_KEY = '/Annots'
    ANNOT_FIELD_KEY = '/T'
    ANNOT_VAL_KEY = '/V'
    ANNOT_RECT_KEY = '/Rect'
    SUBTYPE_KEY = '/Subtype'
    WIDGET_SUBTYPE_KEY = '/Widget'
    template_pdf = pdfrw.PdfReader(input_pdf_path)
    template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'))) 
    annotations = template_pdf.pages[0][ANNOT_KEY]
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key in data_dict.keys():
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(data_dict[key]))
                    )
    pdfrw.PdfWriter().write(output_pdf_path, template_pdf)

# Works, 2020-08-11
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
    crta = current_user.partner_id
    if crta is None:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=403, status_message='Permission denied.')
        flash("ERROR: You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    if current_user.is_read is False:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=403, status_message='Read permission denied.')
        return render_template('main/dashboard_defense.html', title="Insufficient permissions")
    year = int(datetime.utcnow().strftime('%Y'))
    month = int(datetime.utcnow().strftime('%m'))
    start = date(year=year, month=month, day=1)

    partner = Partner.query.filter_by(id=current_user.partner_id).first()
    sales = Sale.query.filter(Sale.partner_id == partner.id, Sale.timestamp >= start).all()
    leads = Lead.query.filter_by().all()

    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.dashboard', status_code=200, status_message='{}'.format(partner.id))

    return render_template('sales/dashboard.html', sales=sales, title='Your sales dashboard', leads=leads)

# Works (weird bug with < 5, but whatever), 2020-08-11
@bp.route('/sales/lead/<lead_id>')
@login_required
def lead_info(lead_id):
    lead = Lead.query.filter_by(id=lead_id).first()
    partner = Partner.query.filter_by(id=current_user.partner_id).first()
    if partner.id != lead.partner_id:
        flash("ERROR: You don't have permission to do that.")
        return redirect(url_for('sales.dashboard'))
    history = []
    timestamps = []
    time_spent = []
    endpoints = []
    incidents = Sentry.query.filter_by(ip_address=lead.ip_address).all()
    for x in incidents:
        timestamps.append(x.timestamp)
        endpoints.append(x.endpoint)
    for y in range(0, len(timestamps)-1):
        z = timestamps[y+1] - timestamps[y]
        time_spent.append(z.seconds)
    for z in range(0, len(endpoints)-1):
        history.append({'time_spent': time_spent[z], 'endpoint': endpoints[z]})
    return render_template('sales/lead.html', title='Lead info - {} {}'.format(lead.first_name, lead.last_name), lead=lead, history=history)

# Works I think, 2020-08-11
# Jumping off point for CRM???
@bp.route('/sales/contacted-lead/<lead_id>')
@login_required
def contacted_lead(lead_id):
    lead = Lead.query.filter_by(id=lead_id).first()
    if current_user.partner_id != lead.partner_id:
        flash("ERROR: You don't have permission to do that.")
        return redirect(url_for('sales.dashboard'))
    lead.is_contacted = True
    db.session.add(lead)
    db.session.commit()
    flash("Nice! Keep up the good work! :)")
    return redirect(url_for('sales.dashboard'))

# Works, 2020-08-11
# CREATE SALE
@bp.route('/create/sale', methods=['GET', 'POST'])
@login_required
def create_sale():
    '''
    - Sentry logs:
        + 403: permission denied; not a contractor OR not an agent
        + 200: ok; sale created
    - Makes a sale and generates a receipt
    '''
    if current_user.partner_id is None:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='sales.create_sale', status_code=403, status_message='Permission denied.')
        flash("ERROR: Only IcyFire partners are able to create sales.")
        return redirect(url_for('sales.dashboard'))
    form = SaleForm()
    if form.validate_on_submit():
        partner = Partner.query.filter_by(id=current_user.partner_id).first()
        activation_code = str(uuid.uuid4())
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
        sales_tax = float(100 * sales_tax_dict[form.client_state.data])
        total = 100 + sales_tax
        data_dict = {
            'receipt_date': datetime.utcnow().strftime('%m/%d/%Y %H:%M'),
            'agent_name': f'{str(partner.first_name).upper()} {str(partner.last_name).upper()}',
            'agent_email': f'{partner.email}',
            'agent_phone': f'({str(partner.phone_number)[0:3]}) {str(partner.phone_number)[3:6]}-{str(partner.phone_number)[6:10]}',
            'client_name': f'{str(form.client_name.data).upper()}',
            'client_street_address': f'{str(form.client_street_address.data).upper()}',
            'client_city': f'{str(form.client_city.data).upper()}',
            'client_state': f'{str(form.client_state.data).upper()}',
            'client_zip': f'{form.client_zip.data}',
            'client_email': f'{form.client_email.data}',
            'client_phone': f'({str(form.client_phone.data)[0:3]}) {str(form.client_phone.data)[3:6]}-{str(form.client_phone.data)[6:10]}',
            'sales_tax': f'${sales_tax:.2f}',
            'total': f'${total:.2f}',
            'activation_code': activation_code
        }
        write_fillable_pdf(input_pdf_path='./app/static/agreements/receipt_template.pdf', output_pdf_path='./app/static/agreements/{}_receipt.pdf'.format(form.client_name.data), data_dict=data_dict)
        
        transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
        file_from = './app/static/agreements/{}_receipt.pdf'.format(form.client_name.data)
        file_to = '/receipts/{}.pdf'.format(form.client_name.data)
        transfer_data.upload_file(file_from, file_to)

        sale = Sale(partner_id=partner.id)
        sale.client_name = form.client_name.data
        sale.client_street_address = form.client_street_address.data
        sale.client_city = form.client_city.data
        sale.client_state = form.client_state.data
        sale.client_country = 'United States'
        sale.client_zip = form.client_zip.data
        sale.client_phone_country = 1
        sale.client_phone_number = form.client_phone.data
        sale.client_email = form.client_email.data
        sale.unit_price = 100
        sale.quanity = 1
        sale.subtotal = 100
        sale.sales_tax = float(sales_tax)
        sale.total = float(total)
        sale.product_id = 'prod_I2uIS76ymDfaT4'
        sale.receipt_url = 'dropbox/home/Apps/icyfire/receipts/{}_receipt.pdf'.format(form.client_name.data)
        sale.payment_reference = form.payment_reference.data

        domain = Domain(activation_code=activation_code)

        db.session.add(sale)
        db.session.add(domain)
        db.session.commit()

        return send_from_directory('static/agreements', '{}_receipt.pdf'.format(form.client_name.data))
    return render_template('sales/create_sale.html', title='New Sale', form=form)