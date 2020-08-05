from flask import render_template, request, url_for, redirect, flash
from flask_login import login_required, current_user
from app import db
from app.security import bp
from app.models import User, Sentry, Domain
from datetime import datetime, timedelta

def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

# FLAGS
@bp.route('/security/flags')
@login_required
def get_flags():
    '''
    - sentry logs:
        + endpoint: 'security.get_flags'
        + 200: ok
        + 403: denied
    - this shows all of the issues that domain admins have raised
    '''
    if current_user.email != 'ciso@icy-fire.com':
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.get_flags', status_code=403, status_message='Access denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    flags = Sentry.query.filter_by(flag=True).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.get_flags', status_code=200, status_message='OK')
    return render_template('security/flags.html', title='SENTRY - Flagged Incidents', flags=flags)

# SORT BY USER
@bp.route('/security/sort-by/user/<user_id>')
@login_required
def sort_by_user(user_id):
    '''
    - sentry logs:
        + endpoint: 'security.sort_by_user'
        + 200: ok
        + 403: denied
    - allows ciso to see everything that a particular user has been doing
    - used for investigative purposes
    '''
    if current_user.email != 'ciso@icy-fire.com':
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_user', status_code=403, status_message='{}'.format(user_id))
        flash("You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    user = User.query.filter_by(id=user_id).first()
    activity = Sentry.query.filter_by(user_id=user_id).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_user', status_code=200, status_message='{}'.format(user_id))
    return render_template('security/user.html', title='User Profile', user=user, activity=activity)

# SORT BY DOMAIN
@bp.route('/security/sort-by/domain/<domain_id>')
@login_required
def sort_by_domain(domain_id):
    '''
    - sentry logs:
        + endpoint: 'security.sort_by_domain'
        + 200: ok
        + 403: denied
    - allows ciso to see everything going on in a particular domain
    - used for investigative purposes
    '''
    if current_user.email != 'ciso@icy-fire.com':
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_domain', status_code=403, status_message='{}'.format(domain_id))
        flash("You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    domain = Domain.query.filter_by(id=domain_id).first()
    activity = Sentry.query.filter_by(domain_id=domain_id).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_domain', status_code=200, status_message='{}'.format(domain_id))
    return render_template('security/domain.html', title='Domain Profile', domain=domain, activity=activity)

# SORT BY IP ADDRESS
@bp.route('/security/sort-by/ip-address/<ip_address>')
@login_required
def sort_by_ip(ip_address):
    '''
    - sentry logs:
        + endpoint: 'security.sort_by_ip'
        + 200: ok
        + 403: denied
    - allows ciso to see everything that a particular ip address has been doing
    - used for investigative purposes and cross-checking with normal user behavior
    '''
    if current_user.email != 'ciso@icy-fire.com':
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_ip', status_code=403, status_message='{}'.format(ip_address))
        flash("You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    activity = Sentry.query.filter_by(ip_address=ip_address).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_ip', status_code=200, status_message='{}'.format(ip_address))
    return render_template('security/ip.html', title='IP Address Profile', ip_address=ip_address, activity=activity)

# SORT BY STATUS CODE
@bp.route('/security/sort-by/status-code/<status_code>')
@login_required
def sort_by_status_code(status_code):
    '''
    - sentry logs:
        + endpoint: 'security.sort_by_status_code'
        + 200: ok
        + 403: denied
    - used for diagnostics and website monitoring, as well as early warning for malintent
    '''
    if current_user.email != 'ciso@icy-fire.com':
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_status_code', status_code=403, status_message='{}'.format(status_code))
        flash("You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    results = Sentry.query.filter_by(status_code=int(status_code)).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.sort_by_status_code', status_code=200, status_message='{}'.format(status_code))
    return render_template('security/status_code.html', title='{} Status Code Records'.format(status_code), status_code=status_code, results=results)

# VIEW THE 200s and 403s FOR ANY GIVEN BLUEPRINT
@bp.route('/security/view/<blueprint_name>')
@login_required
def view_blueprint(blueprint_name):
    '''
    - sentry logs:
        + endpoint: 'security.view_blueprint'
        + 200: ok
        + 403: denied
    - shows all 200s and 403s for that blueprint
    - available blueprints:
        + admin
        + api
        + auth
        + legal
        + main
        + sales
        + security
    '''
    if current_user.email != 'ciso@icy-fire.com':
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.view_blueprint', status_code=403, status_message='{}'.format(blueprint_name))
        flash("You don't have permission to do that.")
        return redirect(url_for('main.dashboard'))
    granted = Sentry.query.filter(Sentry.endpoint.split('.')[0] == blueprint_name.lower(), Sentry.status_code == 200).all()
    denied = Sentry.query.filter(Sentry.endpoint.split('.')[0] == blueprint_name.lower(), Sentry.status_code == 403).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='security.view_blueprint', status_code=200, status_message='{}'.format(blueprint_name))
    return render_template('security/view_blueprint.html', title='SENTRY - {}'.format(str(blueprint_name).upper()), granted=granted, denied=denied, blueprint_name=blueprint_name.upper())
