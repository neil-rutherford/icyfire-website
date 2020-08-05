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

# Tested 2020-08-04
@bp.route('/legal/user/privacy-policy', methods=['GET'])
def privacy_policy():
    if current_user.is_authenticated:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='legal.privacy_policy', status_code=200, status_message='OK')
        domain = Domain.query.filter_by(id=current_user.domain_id).first()
        user = User.query.filter_by(id=current_user.id).first()
        incidents = Sentry.query.filter_by(user_id=current_user.id).all()
        crta = current_user.icyfire_crta
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

# Tested 2020-08-04
@bp.route('/legal/user/cookie-policy', methods=['GET'])
def cookie_policy():
    return render_template('legal/cookie_policy.html', title='Cookie Policy')

# Tested 2020-08-04
@bp.route('/legal/user/terms-of-service', methods=['GET'])
def terms_of_service():
    return render_template('legal/terms_of_service.html', title='Terms of Service')

# Tested 2020-08-04
@bp.route('/legal/vulnerability-disclosure-program')
def vulnerability_disclosure_program():
    return render_template('legal/vdp.html', title='IcyFire - Vulnerability Disclosure Program (VDP)')

# Tested 2020-08-04
@bp.route('/legal/report-vulnerability')
def report_vulnerability():
    return redirect('https://docs.google.com/forms/d/e/1FAIpQLSdz9635l_yBfSXg9-a3aXOejkOqVQcVCQf-3svF8VEdQekmNw/viewform?usp=sf_link')