from flask import render_template, request, url_for, redirect, flash
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User, Sentry, Domain
from datetime import datetime, timedelta

# HELPER FUNCTION
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

@bp.route('/admin/subscription-elapsed')
@login_required
def subscription_elapsed():
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    flash("Your subscription has elasped. To continue using the service, please renew your subscription.")
    return render_template('admin/subscription_elapsed.html', title='Please renew your subscription.', domain=domain)

# ADMIN DASHBOARD - TESTED
@bp.route('/admin/dashboard', methods=['GET'])
@login_required
def dashboard():
    '''
    - Sentry logs:
        + 200 = `is_admin` is True
        + 403 = `is_admin` is False
    - Displays a list of users for that domain, their CRUD permissions, and an option to grant/revoke permission
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.dashboard', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.dashboard', status_code=200, status_message='Successful admin access.')
    users = User.query.filter_by(domain_id=current_user.domain_id).order_by(User.id.desc()).all()
    return render_template('admin/dashboard.html', title='Admin Console', users=users)

# GRANT PERMISSION - TESTED
@bp.route('/admin/<user_id>/+<permission>', methods=['GET', 'POST'])
@login_required
def grant_permission(user_id, permission):
    '''
    - Sentry logs:
        + 200 = `is_admin` is True AND target's domain == perpetrator's domain (`status_message` = user_id|permission)
        + 403 = `is_admin` is False OR target's domain != perpetrator's domain (`status_message` = user_id|permission|description)
        + 400 = permission doesn't exist (`status_message` = user_id|permission)
    - If target's domain != perpetrator's domain, the target's domain ID is recorded in `domain_id` instead of the perpetrator. This is so that the target domain's admin is notified.
    - "c" = create
    - "r" = read
    - "u" = update
    - "d" = delete
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    user = User.query.filter_by(id=int(user_id)).first()
    if user is None:
        flash("ERROR: Can't find that user.")
        make_sentry(user_id=current_user.id, domain_id=user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=404, status_message='{}'.format(int(user_id)))
        return redirect(url_for('admin.dashboard'))
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=403, status_message='{}|{}|Not an admin.'.format(int(user_id), str(permission)))
        return redirect(url_for('main.dashboard'))
    elif current_user.domain_id != user.domain_id:
        flash("ERROR: That user isn't part of your domain.")
        make_sentry(user_id=current_user.id, domain_id=user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=403, status_message='{}|{}|Not part of that domain.'.format(int(user_id), str(permission)))
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'c':
        user.is_create = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        flash("Create permission granted.")
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'r':
        user.is_read = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        flash("Read permission granted.")
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'u':
        user.is_update = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        flash("Update permission granted.")
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'd':
        user.is_delete = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        flash('Delete permission granted.')
        return redirect(url_for('admin.dashboard'))
    else:
        flash('ERROR: Not a valid permission.')
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.grant_permission', status_code=400, status_message='{}|{}|Not a valid permission.'.format(int(user_id), str(permission)))
        return redirect(url_for('admin.dashboard'))

# REVOKE PERMISSION - TESTED
@bp.route('/admin/<user_id>/-<permission>')
@login_required
def revoke_permission(user_id, permission):
    '''
    - Sentry logs:
        + 200 = `is_admin` is True AND target's domain == perpetrator's domain (`status_message` = user_id|permission)
        + 403 = `is_admin` is False OR target's domain != perpetrator's domain (`status_message` = user_id|permission|description)
        + 400 = permission doesn't exist (`status_message` = user_id|permission)
    - If target's domain != perpetrator's domain, the target's domain ID is recorded in `domain_id` instead of the perpetrator. This is so that the target domain's admin is notified.
    - "c" = create
    - "r" = read
    - "u" = update
    - "d" = delete
    - "kill" = delete user
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    user = User.query.filter_by(id=int(user_id)).first()
    if user is None:
        flash("ERROR: Can't find that user.")
        make_sentry(user_id=current_user.id, domain_id=user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=404, status_message='{}'.format(int(user_id)))
        return redirect(url_for('admin.dashboard'))
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=403, status_message='{}|{}|Not an admin.'.format(int(user_id), str(permission)))
        return redirect(url_for('main.dashboard'))
    elif current_user.domain_id != user.domain_id:
        flash("ERROR: That user isn't part of your domain.")
        make_sentry(user_id=current_user.id, domain_id=user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=403, status_message='{}|{}|Not part of that domain.'.format(int(user_id), str(permission)))
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'c':
        user.is_create = False
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        flash("Create permission revoked.")
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'r':
        user.is_read = False
        db.session.add(user)
        db.session.commit()
        flash("Read permission revoked.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'u':
        user.is_update = False
        db.session.add(user)
        db.session.commit()
        flash("Update permission revoked.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'd':
        user.is_delete = False
        db.session.add(user)
        db.session.commit()
        flash('Delete permission revoked.')
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        return redirect(url_for('admin.dashboard'))
    elif str(permission) == 'kill':
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.')
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=200, status_message='{}|{}'.format(int(user_id), str(permission)))
        return(redirect(url_for('admin.dashboard')))
    else:
        flash('ERROR: Not a valid permission.')
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.revoke_permission', status_code=400, status_message='{}|{}|Not a valid permission.'.format(int(user_id), str(permission)))
        return redirect(url_for('admin.dashboard'))

# ESCALATE TO CISO - TESTED
@bp.route('/admin/sentry/escalate-ciso/<post_id>')
def escalate_ciso(post_id):
    '''
    This is the domain admin's way of calling to us for help if needed.
    Looks up incident in Sentry table, sets the flag to true, and returns user to the admin dashboard.
    '''
    incident = Sentry.query.filter_by(id=int(post_id)).first()
    if incident is None:
        flash("ERROR: Can't find that incident.")
        return redirect(url_for('admin.dashboard'))
    incident.flag = True
    db.session.add(incident)
    db.session.commit()
    flash("Thank you for your feedback. You'll hear from us shortly.")
    return redirect(url_for('admin.dashboard'))

# GET USER INFORMATION - TESTED
@bp.route('/admin/sentry/user/<user_id>')
@login_required
def get_user_info(user_id):
    '''
    - Sentry logs:
        + Endpoint: 'admin.get_user_info'
        + 200 = ok
        + 403 = permission denied
    Provides basic information about the user's domain, email address, and post count. 
    Also shows what they have been doing over the past 14 days (for monitoring sketchy behavior).
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.get_user_info', status_code=403, status_message='{}'.format(user_id))
    user = User.query.filter_by(id=int(user_id)).first()
    if user is None:
        flash("ERROR: Can't find that user.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.get_user_info', status_code=404, status_message='{}'.format(user_id))
        return redirect(url_for('admin.dashboard'))
    limit = datetime.utcnow() - timedelta(days=14)
    activities = Sentry.query.filter(Sentry.user_id == user_id, Sentry.domain_id == current_user.domain_id, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.get_user_info', status_code=200, status_message='{}'.format(user_id))
    return render_template('admin/get_user_info.html', title='SENTRY - Get User Info', user=user, activities=activities)

# CREATE-200 - TESTED
@bp.route('/admin/sentry/create/success', methods=['GET'])
@login_required
def sentry_create_success():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_create_success'
        + 200 = ok
        + 403 = permission denied
    - This is a list of all incidents where users successfully created posts over the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_create_success', status_code=403, status_message='Access denied.')
        return redirect(url_for('main.dashboard'))
    limit = datetime.utcnow() - timedelta(days=14)
    short_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_short_text', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    long_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_long_text', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    images = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_image', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    videos = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_video', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_create_success', status_code=200, status_message='OK')
    return render_template('admin/create_success.html', title='Successful Creations', short_texts=short_texts, long_texts=long_texts, images=images, videos=videos)

# CREATE-403 - TESTED
@bp.route('/admin/sentry/create/fail', methods=['GET'])
@login_required
def sentry_create_fail():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_create_fail'
        + 200 = ok
        + 403 = ok
    - This is a list of all incidents where users attempted to create posts (but failed) over the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_create_fail', status_code=403, status_message='Access denied.')
        return redirect(url_for('main.dashboard'))
    limit = datetime.utcnow() - timedelta(days=14)
    short_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_short_text', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    long_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_long_text', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    images = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_image', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    videos = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.create_video', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_create_fail', status_code=200, status_message='OK')
    return render_template('admin/create_fail.html', title='Attempted Creations', short_texts=short_texts, long_texts=long_texts, images=images, videos=videos)

# READ-200 - TESTED
@bp.route('/admin/sentry/read/success', methods=['GET'])
@login_required
def sentry_read_success():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_read_success'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users had access to their dashboards (and could see all of the company's social queues) in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_read_success', status_code=403, status_message='Access denied.')
        return redirect(url_for('main.dashboard'))
    limit = datetime.utcnow() - timedelta(days=14)
    reads = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.dashboard', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_read_success', status_code=200, status_message='OK')
    return render_template('admin/read_success.html', title='Successful Reads', reads=reads)

# READ-403 - TESTED
@bp.route('/admin/sentry/read/fail', methods=['GET'])
@login_required
def sentry_read_fail():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_read_fail'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users tried unsuccessfully to access the company's social queues in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_read_fail', status_code=403, status_message='Access denied.')
        return redirect(url_for('main.dashboard'))
    limit = datetime.utcnow() - timedelta(days=14)
    reads = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.dashboard', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_read_fail', status_code=200, status_message='OK')
    return render_template('admin/read_fail.html', title='Attempted Reads', reads=reads)

# UPDATE-200 - TESTED
@bp.route('/admin/sentry/update/success', methods=['GET'])
@login_required
def sentry_update_success():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_update_success'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users successfully edited/updated posts in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_update_success', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    short_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_short_text', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    long_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_long_text', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    images = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_image', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    videos = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_video', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_update_success', status_code=200, status_message='OK')
    return render_template('admin/update_success.html', title='Successful Updates', short_texts=short_texts, long_texts=long_texts, images=images, videos=videos)

# UPDATE-403 - TESTED
@bp.route('/admin/sentry/update/fail', methods=['GET'])
@login_required
def sentry_update_fail():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_update_fail'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users unsuccessfully attempted to edit/update posts in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_update_fail', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    short_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_short_text', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    long_texts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_long_text', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    images = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_image', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    videos = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.update_video', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_update_fail', status_code=200, status_message='OK')
    return render_template('admin/update_fail.html', title='Attempted Updates', short_texts=short_texts, long_texts=long_texts, images=images, videos=videos)

# DELETE-204 - TESTED
@bp.route('/admin/sentry/delete/success', methods=['GET'])
@login_required
def sentry_delete_success():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_delete_success'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users successfully deleted posts in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_delete_success', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    deletes = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.delete_post', Sentry.status_code == 204, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_delete_success', status_code=200, status_message='OK')
    return render_template('admin/delete_success.html', title='Successful Deletes', deletes=deletes)

# DELETE-403 - TESTED
@bp.route('/admin/sentry/delete/fail', methods=['GET'])
@login_required
def sentry_delete_fail():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_delete_fail'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users unsuccessfully attempted to delete a post in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_delete_fail', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    deletes = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'main.delete_post', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_delete_fail', status_code=200, status_message='OK')
    return render_template('admin/delete_fail.html', title='Failed Deletes', deletes=deletes)

# PERMISSION-200 - TESTED
@bp.route('/admin/sentry/permission/success', methods=['GET'])
@login_required
def sentry_permission_success():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_permission_success'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users successfully changed another user's permissions in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_permission_success', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    grants = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.grant_permission', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    revokes = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.revoke_permission', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_permission_success', status_code=200, status_message='OK')
    return render_template('admin/permission_success.html', title='Successful Permission Changes', grants=grants, revokes=revokes)

# PERMISSION-403 - TESTED
@bp.route('/admin/sentry/permission/fail', methods=['GET'])
@login_required
def sentry_permission_fail():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_permission_fail'
        + 200 = ok
        + 403 = access denied
    - This is a list of all incidents where users unsuccessfully attempted to change another user's permissions in the past 14 days.
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_permission_fail', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    grants = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.grant_permission', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    revokes = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.revoke_permission', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_permission_fail', status_code=200, status_message='OK')
    return render_template('admin/permission_fail.html', title='Attempted Permission Changes', grants=grants, revokes=revokes)

# ADMIN CONSOLE-200 - TESTED
@bp.route('/admin/sentry/admin/success', methods=['GET'])
@login_required
def sentry_admin_success():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_admin_success'
        + 200 = ok
        + 403 = access denied
    - This is a list of all admin console access (i.e. all of the admin tools on this page) in the past 14 days
    - This should all be the domain admin...
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_admin_success', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    dashboard = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.dashboard', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    get_user_info = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.get_user_info', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    create_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_create_success', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    create_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_create_fail', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    read_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_read_success', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    read_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_read_fail', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    update_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_update_success', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    update_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_update_fail', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    delete_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_delete_success', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    delete_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_delete_fail', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    permission_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_permission_success', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    permission_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_permission_fail', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    admin_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_admin_success', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    admin_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_admin_fail', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    creds_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_creds_success', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    creds_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_creds_fail', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_admin_success', status_code=200, status_message='OK')
    return render_template('admin/admin_success.html', title='Successful Admin Console Access', dashboard=dashboard, get_user_info=get_user_info, create_success=create_success, create_fail=create_fail, read_success=read_success, read_fail=read_fail, update_success=update_success, update_fail=update_fail, delete_success=delete_success, delete_fail=delete_fail, permission_success=permission_success, permission_fail=permission_fail, admin_success=admin_success, admin_fail=admin_fail, creds_success=creds_success, creds_fail=creds_fail)

# ADMIN CONSOLE-403 - TESTED
@bp.route('/admin/sentry/admin/fail', methods=['GET'])
@login_required
def sentry_admin_fail():
    '''
    - Sentry logs: 
        + Endpoint: 'admin.sentry_admin_fails'
        + 200 = ok
        + 403 = access denied
    - This is a list of all attempted (unsuccessful) admin console access in the past 14 days
    - This should be empty
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_admin_fail', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    dashboard = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.dashboard', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    get_user_info = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.get_user_info', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    create_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_create_success', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    create_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_create_fail', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    read_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_read_success', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    read_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_read_fail', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    update_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_update_success', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    update_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_update_fail', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    delete_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_delete_success', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    delete_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_delete_fail', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    permission_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_permission_success', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    permission_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_permission_fail', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    admin_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_admin_success', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    admin_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_admin_fail', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    creds_success = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_creds_success', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    creds_fail = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'admin.sentry_creds_fail', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_admin_fail', status_code=200, status_message='OK')
    return render_template('admin/admin_fail.html', title='Attempted Admin Console Access', dashboard=dashboard, get_user_info=get_user_info, create_success=create_success, create_fail=create_fail, read_success=read_success, read_fail=read_fail, update_success=update_success, update_fail=update_fail, delete_success=delete_success, delete_fail=delete_fail, permission_success=permission_success, permission_fail=permission_fail, admin_success=admin_success, admin_fail=admin_fail, creds_success=creds_success, creds_fail=creds_fail)

# CREDS-200 - TESTED
@bp.route('/admin/sentry/creds/success', methods=['GET'])
@login_required
def sentry_creds_success():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_creds_success'
        + 200 = ok
        + 403 = access denied
    - This is a list of all successful changes to the domain's social media creds in the past 14 days
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))

    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_creds_success', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    creds = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'auth.update_creds', Sentry.status_code == 200, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_creds_success', status_code=200, status_message='OK')
    return render_template('admin/creds_success.html', title='Successful Credentials Access', creds=creds)

# CREDS-403 - TESTED
@bp.route('/admin/sentry/creds/fail', methods=['GET'])
@login_required
def sentry_creds_fail():
    '''
    - Sentry logs:
        + Endpoint: 'admin.sentry_creds_fail'
        + 200 = ok
        + 403 = access denied
    - This is a list of all unsuccessful attempts to change the domain's social media creds in the past 14 days
    '''
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.expires_on - datetime.utcnow() < timedelta(0):
        return redirect(url_for('admin.subscription_elapsed'))
        
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_creds_fail', status_code=403, status_message='Access denied.')
    limit = datetime.utcnow() - timedelta(days=14)
    creds = Sentry.query.filter(Sentry.domain_id == current_user.domain_id, Sentry.endpoint == 'auth.update_creds', Sentry.status_code == 403, Sentry.timestamp >= limit).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.sentry_creds_fail', status_code=200, status_message='OK')
    return render_template('admin/creds_fail.html', title='Attempted Credentials Access', creds=creds)