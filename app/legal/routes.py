from app.legal import bp
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from app import db
from app.legal.forms import GenerateIcaForm
from app.models import Domain, User, Sentry, Sale, Partner #CountryLead, RegionLead, TeamLead, Sale
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
        crta = current_user.partner_id
        if crta is None:
            contractor = None
            sales = None
        else:
            contractor = Partner.query.filter_by(id=crta).first()
            sales = Sale.query.filter_by(partner_id=crta).all()
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
@bp.route('/legal/hacker/vulnerability-disclosure-program')
def vulnerability_disclosure_program():
    return render_template('legal/vdp.html', title='Vulnerability Disclosure Program (VDP)')

# Tested 2020-08-04
@bp.route('/legal/hacker/report-vulnerability')
def report_vulnerability():
    return redirect('https://docs.google.com/forms/d/e/1FAIpQLSdz9635l_yBfSXg9-a3aXOejkOqVQcVCQf-3svF8VEdQekmNw/viewform?usp=sf_link')

@bp.route('/legal/user/email-opt-out/<email>')
def email_opt_out(email):
    var = User.query.filter_by(email=email).first()
    if not email:
        flash("Sorry, we can't find that email address.")
        return redirect(url_for('promo.home'))
    var.email_opt_in = False
    db.session.add(var)
    db.session.commit()
    return render_template('legal/email_opt_out.html', title='Email opt-out successful!', email=email)

@bp.route('/legal/client/service-agreement')
def service_agreement():
    return send_from_directory('static/agreements', 'service_agreement.pdf')