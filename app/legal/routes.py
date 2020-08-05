from app.legal import bp
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from app import db
from app.legal.forms import GenerateIcaForm
from app.models import Domain, User, Sentry, CountryLead, RegionLead, TeamLead, Sale
from flask_login import current_user, login_required
from datetime import datetime, date
import uuid
import pdfrw
import os

def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    incident = Sentry(user_id=user_id, domain_id=domain_id, ip_address=ip_address, endpoint=endpoint, status_code=status_code, status_message=status_message, flag=flag)
    db.session.add(incident)
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

@bp.route('/legal/user/privacy-policy', methods=['GET'])
def privacy_policy():
    if current_user.is_authenticated:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='legal.privacy_policy', status_code=200, status_message='OK')
        domain = Domain.query.filter_by(id=current_user.domain_id).first()
        user = User.query.filter_by(id=current_user.id).first()
        incidents = Sentry.query.filter_by(user_id=current_user.id).all()
        crta = current_user.icyfire_crta
        #country = str(current_user.icyfire_crta).split('-')[0]
        #region = str(current_user.icyfire_crta).split('-')[1]
        #team = str(current_user.icyfire_crta).split('-')[2]
        #agent = str(current_user.icyfire_crta).split('-')[3]
        if crta is None:
            contractor = None
            sales = None
        elif str(current_user.icyfire_crta).split('-')[0] != '00' and str(current_user.icyfire_crta).split('-')[1] == '00' and str(current_user.icyfire_crta).split('-')[2] == '00' and str(current_user.icyfire_crta).split('-')[3] == '00':
            contractor = CountryLead.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(country_lead_id=contractor.id).all()
        elif str(current_user.icyfire_crta).split('-')[0] != '00' and str(current_user.icyfire_crta).split('-')[1] != '00' and str(current_user.icyfire_crta).split('-')[2] == '00' and str(current_user.icyfire_crta).split('-')[3] == '00':
            contractor = RegionLead.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(region_lead_id=contractor.id).all()
        elif str(current_user.icyfire_crta).split('-')[0] != '00' and str(current_user.icyfire_crta).split('-')[1] != '00' and str(current_user.icyfire_crta).split('-')[2] != '00' and str(current_user.icyfire_crta).split('-')[3] == '00':
            contractor = TeamLead.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(team_lead_id=contractor.id).all()
        elif str(current_user.icyfire_crta).split('-')[0] != '00' and str(current_user.icyfire_crta).split('-')[1] != '00' and str(current_user.icyfire_crta).split('-')[2] != '00' and str(current_user.icyfire_crta).split('-')[3] != '00':
            contractor = Agent.query.filter_by(crta_code=crta).first()
            sales = Sale.query.filter_by(agent_id=contractor.id).all()
    else:
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='legal.privacy_policy', status_code=200, status_message='OK')
        domain = None
        user = None
        contractor = None
        sales = None
        incidents = Sentry.query.filter_by(ip_address=request.remote_addr).all()
    return render_template('legal/privacy_policy.html', domain=domain, user=user, contractor=contractor, sales=sales, incidents=incidents, title='Privacy Policy')

@bp.route('/legal/user/cookie-policy', methods=['GET'])
def cookie_policy():
    return render_template('legal/cookie_policy.html', title='Cookie Policy')

@bp.route('/legal/user/terms-of-service', methods=['GET'])
def terms_of_service():
    return render_template('legal/terms_of_service.html', title='Terms of Service')

@bp.route('/legal/contractor/ica', methods=['GET'])
@login_required
def independent_contractor_agreement():
    if current_user.email != 'neilbolyard@gmail.com':
        flash("You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='legal.independent_contractor_agreement', status_code=403, status_message='Access denied.')
        return redirect(url_for('main.dashboard'))
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
            fill_pdf(input_path=input_path, output_path=output_path, data_dict=data_dict)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='legal.privacy_policy', status_code=200, status_message='OK')
        return send_from_directory(os.path.join(basedir, 'app', 'static', 'records', 'contracts'), '{}_ica.pdf'.format(str(form.last_name.data)), as_attachment=True)
    return render_template('legal/independent_contractor_agreement.html', title='Generate Independent Contractor Agreement', form=form)

@bp.route('/legal/vulnerability-disclosure-program')
def vulnerability_disclosure_program():
    return render_template('legal/vdp.html', title='IcyFire - Vulnerability Disclosure Program (VDP)')

@bp.route('/legal/report-vulnerability')
def report_vulnerability():
    return redirect('https://docs.google.com/forms/d/e/1FAIpQLSdz9635l_yBfSXg9-a3aXOejkOqVQcVCQf-3svF8VEdQekmNw/viewform?usp=sf_link')