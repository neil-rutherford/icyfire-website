from flask import render_template, request, url_for, redirect, flash
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User, Sentry, Domain

# HELPER FUNCTION
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message):
    activity = Sentry(ip_address=str(ip_address), user_id=int(user_id), endpoint=str(endpoint), status_code=int(status_code), status_message=str(status_message), domain_id=int(domain_id))
    db.session.add(activity)
    db.session.commit()

# ADMIN DASHBOARD
@bp.route('/admin/dashboard', methods=['GET'])
@login_required
def dashboard():
    '''
    - Sentry logs:
        + 200 = `is_admin` is True
        + 403 = `is_admin` is False
    - Displays a list of users for that domain, their CRUD permissions, and an option to grant/revoke permission
    '''
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.dashboard', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.dashboard', status_code=200, status_message='Successful admin access.')
    users = User.query.filter_by(domain_id=current_user.domain_id).order_by(User.id.desc()).all()
    return render_template('admin/dashboard.html', title='User Control Panel', users=users)

# GRANT PERMISSION PROCESS
@bp.route('/admin/<user_id>/+<permission>', methods=['GET', 'POST'])
@login_required
def grant_permission(user_id, permission):
    '''
    - Sentry logs:
        + 200 = `is_admin` is True AND target's domain == perpetrator's domain
        + 403 = `is_admin` is False OR target's domain != perpetrator's domain
        + 400 = permission doesn't exist
    - If target's domain != perpetrator's domain, the target's domain ID is recorded in `domain_id` instead of the perpetrator. This is so that the target domain's admin is notified.
    - "c" = create
    - "r" = read
    - "u" = update
    - "d" = delete
    '''
    user = User.query.filter_by(id=int(user_id)).first()
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

# REVOKE PERMISSION PAGE
@bp.route('/admin/<user_id>/-<permission>')
@login_required
def revoke_permission(user_id, permission):
    '''
    - Sentry logs:
        + 200 = `is_admin` is True AND target's domain == perpetrator's domain
        + 403 = `is_admin` is False OR target's domain != perpetrator's domain
        + 400 = permission doesn't exist
    - If target's domain != perpetrator's domain, the target's domain ID is recorded in `domain_id` instead of the perpetrator. This is so that the target domain's admin is notified.
    - "c" = create
    - "r" = read
    - "u" = update
    - "d" = delete
    - "kill" = delete user
    '''
    user = User.query.filter_by(id=int(user_id)).first()
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

# Domain security dash for when we get around to it
#@bp.route('/admin/activity')
#@login_required
#def activity():
    #if current_user.is_admin is False:
        #flash("ERROR: You don't have permission to do that.")
        #make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='admin.activity', status_code=403, status_message='Not an admin.')
        #return redirect(url_for('main.dashboard'))
    #start = datetime.utcnow() - timedelta(days=14)
    #facebook_creates
    #twitter_creates
    #tumblr_creates
    #reddit_creates
    #youtube_creates
    #linkedin_creates
    #facebook_updates
    #twitter_updates
    #tumblr_updates
    #reddit_updates
    #youtube_updates
    #linkedin_updates
    #facebook_deletes
    #twitter_deletes
    #tumblr_deletes
    #reddit_deletes
    #youtube_deletes
    #linkedin_deletes
    #facebook_posts
    #twitter_posts
    #tumblr_posts
    #reddit_posts
    #youtube_posts
    #linkedin_posts
    #new_users = Sentry.query.filter(Sentry.domain_id == current_user.domain_id and Sentry.endpoint == 'auth.register_user' and Sentry.status_code == 200 and Sentry.timestamp >= start).order_by(Sentry.timestamp.desc()).all()
    #permission_grants = Sentry.query.filter(Sentry.domain_id == current_user.domain_id and Sentry.endpoint == 'admin.grant_permission' and Sentry.status_code == 200 and Sentry.timestamp >= start).order_by(Sentry.timestamp.desc()).all()
    #permission_revokes = Sentry.query.filter(Sentry.domain_id == current_user.domain_id and Sentry.endpoint == 'admin.revoke_permission' and Sentry.status_codes == 200 and Sentry.timestamp >= start).order_by(Sentry.timestamp.desc()).all()
    #admin_access_attempts = Sentry.query.filter(Sentry.domain_id == current_user.domain_id and Sentry.endpoint.split('.')[0] == 'admin' and Sentry.status_code == 403 and Sentry.timestamp >= start).order_by(Sentry.timestamp.desc()).all()
    #return render_template('admin/activity.html', title='Activity In Your Domain', )