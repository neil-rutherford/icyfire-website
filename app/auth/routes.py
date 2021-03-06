from flask import render_template, redirect, url_for, flash, request, current_app, send_from_directory
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required, fresh_login_required
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, DomainRegistrationForm, UserRegistrationForm, PartnerRegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, FacebookCreds, TwitterCreds, TumblrCreds, RedditCreds
from app.models import User, Sentry, Domain, FacebookCred, TwitterCred, TumblrCred, RedditCred, TimeSlot, FacebookPost, TwitterPost, TumblrPost, RedditPost, Partner
from app.auth.email import send_password_reset_email, send_verify_email_email
import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env')

# SENTRY HELPER FUNCTION
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

# Works, 2020-08-11
# ENCRYPTION HELPER FUNCTION
def encrypt(message):
    password_provided = os.environ['SECRET_KEY']
    password = password_provided.encode()
    salt = os.environ['SALT'].encode()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password))
    message = message.encode()
    f = Fernet(key)
    encrypted = f.encrypt(message)
    return encrypted

# Works, 2020-08-11
# LOGIN DEFENSE
@bp.route('/login-defense')
def login_defense():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.login', status_code=303, status_message='Redirected', flag=True)
    return render_template('auth/login_defense.html', title='Woah there!')

# Works, 2020-08-11
# LOGIN PAGE
@bp.route('/login', methods=['GET', 'POST'])
def login():
    '''
    - Sentry logs:
        + 200 = credentials are correct
        + 401 = credentials are incorrect (credentials stored in `status_message`)
    - If user is already logged in, it redirects them to their dashboard.
    - If the user enters the wrong creds, it asks them to try again. Sentry also logs the attempt and hopefully looks for dictionary/brute force attacks.
    - If the user enters the right creds, it redirects them to where they were trying to go before they were redirected to the login page (or else to the dashboard).
    '''
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    records = Sentry.query.filter(Sentry.ip_address == request.remote_addr, Sentry.endpoint == 'auth.login', Sentry.status_code == 401).all()
    login_attempts = []
    for attempt in records:
        if str(attempt.timestamp)[0:10] == str(datetime.utcnow())[0:10]:
            login_attempts.append(attempt)
    if len(login_attempts) > 7:
        return redirect(url_for('auth.login_defense'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=str(form.email.data)).first()
        if user is None or not user.check_password(str(form.password.data)):
            make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.login', status_code=401, status_message='{}|{}'.format(str(form.email.data), str(form.password.data)))
            flash('ERROR: Invalid email or password.')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.login', status_code=200, status_message='Successful login.')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    return render_template('auth/login.html', title='Log In', form=form)

# Works, 2020-08-11
# LOGOUT PAGE
@bp.route('/logout')
def logout():
    '''
    - Sentry logs:
        + 200 = successful logout
    - Logs the user out and redirects them to the home page.
    '''
    logout_user()
    #make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.logout', status_code=200, status_message='Successful logout.')
    return redirect(url_for('promo.home'))

# Works, 2020-08-11
@bp.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register.html', title='Register')

# Works, 2020-08-11
# NEW DOMAIN REGISTRATION PAGE
@bp.route('/register/domain', methods=['GET', 'POST'])
def register_domain():
    '''
    - Sentry logs:
        + 200 = domain registration success (domain name in `status_message`)
    - If the user is already logged in, it directs them to their dashboard.
    - The individual enters the activation code, which is then used to find the existing domain (originally created when the sale was recorded).
    - A name is given to the domain. 
    - A new user account is generated and linked to the domain.
    - The user account is granted admin permissions and is logged in. 
    '''
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = DomainRegistrationForm()
    if form.validate_on_submit():
        user = User(email=str(form.email.data))
        domain = Domain.query.filter_by(activation_code=str(form.activation_code.data)).first()
        user.set_password(str(form.password.data))
        user.domain_id = domain.id
        user.post_count = 0
        user.is_admin = True
        user.is_create = True
        user.is_read = True
        user.is_update = True
        user.is_delete = True
        user.is_verified = False
        user.email_opt_in = form.email_opt_in.data
        user.partner_id = None
        domain.domain_name = str(form.domain_name.data)
        db.session.add(user)
        db.session.add(domain)
        db.session.commit()
        send_verify_email_email(user)
        login_user(user, remember=True)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_domain', status_code=200, status_message='{}'.format(domain.domain_name))
        flash("Welcome to IcyFire! Let's link your social media accounts.")
        return redirect(url_for('auth.link_social'))
    return render_template('auth/register_domain.html', title='Register Your New Domain', form=form)

# Works, 2020-08-11
# NEW USER REGISTRATION PAGE
@bp.route('/register/user', methods=['GET', 'POST'])
def register_user():
    '''
    - Sentry logs:
        + 200 = user successfully created
    - If the user is already logged in, it directs them to their dashboard.
    - The individual enters the domain name, which is used to find the existing domain (registered by the domain admin).
    - A new user account is created and linked to the domain.
    - As a security measure, all of the user's CRUD permissions are set to False.
    '''
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        user = User(email=str(form.email.data))
        domain = Domain.query.filter_by(domain_name=str(form.domain_name.data)).first()
        user.set_password(str(form.password.data))
        user.domain_id = domain.id
        user.post_count = 0
        user.is_admin = False
        user.is_create = False
        user.is_read = False
        user.is_update = False
        user.is_delete = False
        user.email_opt_in = form.email_opt_in.data
        user.partner_id = None
        user.is_verified = False
        db.session.add(user)
        db.session.commit()
        send_verify_email_email(user)
        login_user(user, remember=True)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_user', status_code=200, status_message='{}'.format(str(form.domain_name.data)))
        flash("As a security precaution, new users have limited permissions by default. This will change once your domain admin gives your account the all clear.")
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register_user.html', title='New User Registration', form=form)

# Not tested yet
@bp.route('/register/partner', methods=['GET', 'POST'])
def register_partner():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = PartnerRegistrationForm()
    if form.validate_on_submit():
        domain = Domain.query.filter_by(domain_name='IcyFire Technologies, LLC').first()
        partner = Partner(first_name=form.first_name.data)
        partner.last_name = form.last_name.data
        partner.phone_number = form.phone_number.data
        partner.email = form.email.data
        db.session.add(partner)
        db.session.commit()
        user = User(email=str(form.email.data))
        user.domain_id = domain.id
        user.set_password(str(form.password.data))
        user.is_admin = False
        user.is_create = False
        user.is_read = False
        user.is_update = False
        user.is_delete = False
        user.email_opt_in = True
        user.is_verified = False
        user.post_count = 0
        user.partner_id = partner.id
        db.session.add(user)
        db.session.commit()
        send_verify_email_email(user)
        login_user(user)
        flash("As a security precaution, new users have limited permissions by default. This will change once your domain admin gives your account the all clear.")
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register_partner.html', title='New Partner Registration', form=form)


# Works, 2020-08-12
@bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions to reset your password.')
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.reset_password_request', status_code=200, status_message='{}'.format(form.email.data))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

# Works, 2020-08-12
@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    user = User.verify_reset_password_token(token)
    if not user:
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.reset_token', status_code=404, status_message='User not found')
        return redirect(url_for('promo.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.reset_token', status_code=200, status_message='OK')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.verify_verify_email_token(token)
    if not user:
        return redirect(url_for('promo.home'))
    else:
        user.is_verified = True
        db.session.add(user)
        db.session.commit()
        flash("Your email has been verified. Thanks!")
        return redirect(url_for('main.dashboard'))
    

# Works, 2020-08-13
@bp.route('/register/link-social')
@login_required
def link_social():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_social', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    domain = Domain.query.filter_by(id=current_user.domain_id).first()

    facebook_creds = FacebookCred.query.filter_by(domain_id=domain.id).order_by(FacebookCred.id).all()
    facebook_timeslots = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.facebook_cred_id != None).order_by(TimeSlot.id).all()

    twitter_creds = TwitterCred.query.filter_by(domain_id=domain.id).order_by(TwitterCred.id).all()
    twitter_timeslots = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.twitter_cred_id != None).order_by(TimeSlot.id).all()

    tumblr_creds = TumblrCred.query.filter_by(domain_id=domain.id).order_by(TumblrCred.id).all()
    tumblr_timeslots = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.tumblr_cred_id != None).order_by(TimeSlot.id).all()

    reddit_creds = RedditCred.query.filter_by(domain_id=domain.id).order_by(RedditCred.id).all()
    reddit_timeslots = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.reddit_cred_id != None).order_by(TimeSlot.id).all()

    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_social', status_code=200, status_message='OK')
    return render_template('auth/link_social.html', title="Link Your Social Media Accounts", domain=domain, facebook_creds=facebook_creds, facebook_timeslots=facebook_timeslots, twitter_creds=twitter_creds, twitter_timeslots=twitter_timeslots, tumblr_creds=tumblr_creds, tumblr_timeslots=tumblr_timeslots, reddit_creds=reddit_creds, reddit_timeslots=reddit_timeslots)

# Works, 2020-08-12
@bp.route('/register/link-social/facebook', methods=['GET', 'POST'])
@login_required
def link_facebook():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_facebook', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).order_by(TimeSlot.id).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).order_by(TimeSlot.id).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).order_by(TimeSlot.id).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).order_by(TimeSlot.id).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).order_by(TimeSlot.id).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).order_by(TimeSlot.id).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).order_by(TimeSlot.id).all()
    #
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, (0, "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, (0, "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, (0, "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, (0, "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, (0, "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, (0, "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, (0, "I don't want to post on Sundays."))
    form = FacebookCreds()
    form.schedule_monday.choices = monday_list
    form.schedule_tuesday.choices = tuesday_list
    form.schedule_wednesday.choices = wednesday_list
    form.schedule_thursday.choices = thursday_list
    form.schedule_friday.choices = friday_list
    form.schedule_saturday.choices = saturday_list
    form.schedule_sunday.choices = sunday_list
    if form.validate_on_submit():
        cred = FacebookCred(access_token=encrypt(form.access_token.data).decode())
        cred.page_id = form.page_id.data
        cred.domain_id = current_user.domain_id
        cred.alias = form.alias.data
        db.session.add(cred)
        db.session.commit()
        if form.schedule_monday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_tuesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_wednesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_thursday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_friday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_saturday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_sunday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        flash("Facebook account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_facebook', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_facebook.html', title='Link A Facebook Account', form=form, time=datetime.utcnow())

# Works, 2020-08-11
@bp.route('/register/link-social/twitter', methods=['GET', 'POST'])
@login_required
def link_twitter():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_twitter', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).order_by(TimeSlot.id).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).order_by(TimeSlot.id).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).order_by(TimeSlot.id).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).order_by(TimeSlot.id).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).order_by(TimeSlot.id).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).order_by(TimeSlot.id).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).order_by(TimeSlot.id).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, (0, "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, (0, "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, (0, "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, (0, "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, (0, "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, (0, "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, (0, "I don't want to post on Sundays."))
    form = TwitterCreds()
    form.schedule_monday.choices = monday_list
    form.schedule_tuesday.choices = tuesday_list
    form.schedule_wednesday.choices = wednesday_list
    form.schedule_thursday.choices = thursday_list
    form.schedule_friday.choices = friday_list
    form.schedule_saturday.choices = saturday_list
    form.schedule_sunday.choices = sunday_list
    if form.validate_on_submit():
        cred = TwitterCred(consumer_key=encrypt(form.consumer_key.data).decode())
        cred.consumer_secret = encrypt(form.consumer_secret.data).decode()
        cred.access_token_key = encrypt(form.access_token_key.data).decode()
        cred.access_token_secret = encrypt(form.access_token_secret.data).decode()
        cred.alias = form.alias.data
        cred.domain_id = current_user.domain_id
        db.session.add(cred)
        db.session.commit()
        if form.schedule_monday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_tuesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_wednesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_thursday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_friday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_saturday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_sunday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        flash("Twitter account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_twitter', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_twitter.html', title='Link A Twitter Account', form=form, time=datetime.utcnow())

# Works, 2020-08-13
@bp.route('/register/link-social/tumblr', methods=['GET', 'POST'])
@login_required
def link_tumblr():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_tumblr', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).order_by(TimeSlot.id).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).order_by(TimeSlot.id).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).order_by(TimeSlot.id).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).order_by(TimeSlot.id).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).order_by(TimeSlot.id).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).order_by(TimeSlot.id).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).order_by(TimeSlot.id).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, (0, "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, (0, "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, (0, "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, (0, "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, (0, "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, (0, "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, (0, "I don't want to post on Sundays."))
    form = TumblrCreds()
    form.schedule_monday.choices = monday_list
    form.schedule_tuesday.choices = tuesday_list
    form.schedule_wednesday.choices = wednesday_list
    form.schedule_thursday.choices = thursday_list
    form.schedule_friday.choices = friday_list
    form.schedule_saturday.choices = saturday_list
    form.schedule_sunday.choices = sunday_list
    if form.validate_on_submit():
        cred = TumblrCred(consumer_key=encrypt(form.consumer_key.data).decode())
        cred.consumer_secret = encrypt(form.consumer_secret.data).decode()
        cred.oauth_token = encrypt(form.oauth_token.data).decode()
        cred.oauth_secret = encrypt(form.oauth_secret.data).decode()
        cred.blog_name = form.blog_name.data
        cred.domain_id = current_user.domain_id
        cred.alias = form.alias.data
        db.session.add(cred)
        db.session.commit()
        if form.schedule_monday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_tuesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_wednesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_thursday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_friday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_saturday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_sunday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        flash("Tumblr account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_tumblr', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_tumblr.html', title='Link A Tumblr Account', form=form, time=datetime.utcnow())

# Works, 2020-08-13
@bp.route('/register/link-social/reddit', methods=['GET', 'POST'])
@login_required
def link_reddit():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_reddit', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).order_by(TimeSlot.id).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).order_by(TimeSlot.id).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).order_by(TimeSlot.id).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).order_by(TimeSlot.id).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).order_by(TimeSlot.id).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).order_by(TimeSlot.id).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).order_by(TimeSlot.id).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, (0, "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, (0, "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, (0, "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, (0, "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, (0, "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, (0, "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, (0, "I don't want to post on Sundays."))
    form = RedditCreds()
    form.schedule_monday.choices = monday_list
    form.schedule_tuesday.choices = tuesday_list
    form.schedule_wednesday.choices = wednesday_list
    form.schedule_thursday.choices = thursday_list
    form.schedule_friday.choices = friday_list
    form.schedule_saturday.choices = saturday_list
    form.schedule_sunday.choices = sunday_list
    if form.validate_on_submit():
        cred = RedditCred(client_id=encrypt(form.client_id.data).decode())
        cred.client_secret = encrypt(form.client_secret.data).decode()
        cred.user_agent = encrypt(form.user_agent.data).decode()
        cred.username = encrypt(form.username.data).decode()
        cred.password = encrypt(form.password.data).decode()
        cred.target_subreddit = form.target_subreddit.data
        cred.alias = form.alias.data
        cred.domain_id = current_user.domain_id
        db.session.add(cred)
        db.session.commit()
        if form.schedule_monday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_tuesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_wednesday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_thursday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_friday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_saturday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_sunday.data != 0:
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                slot.domain_id = current_user.domain_id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        flash("Reddit account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_reddit', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_reddit.html', title='Link A Reddit Account', form=form, time=datetime.utcnow())

# Works, 2020-08-13
@bp.route('/edit/cred/<platform>/<cred_id>', methods=['GET', 'POST'])
@fresh_login_required
def edit_cred(platform, cred_id):
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=403, status_message='{}|{}'.format(platform, cred_id))
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).order_by(TimeSlot.id).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).order_by(TimeSlot.id).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).order_by(TimeSlot.id).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).order_by(TimeSlot.id).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).order_by(TimeSlot.id).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).order_by(TimeSlot.id).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).order_by(TimeSlot.id).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, (0, "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, (0, "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, (0, "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, (0, "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, (0, "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, (0, "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, (0, "I don't want to post on Sundays."))
    if platform == 'facebook':
        cred = FacebookCred.query.filter_by(id=cred_id).first()
        if cred is None:
            flash("ERROR: Account not found. Are you sure it wasn't deleted?")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=404, status_message='Cred not found')
            return redirect(url_for('auth.link_social'))
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=403, status_message='facebook|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        slots = TimeSlot.query.filter_by(facebook_cred_id=cred.id).all()
        for slot in slots:
            slot.facebook_cred_id = None
            slot.domain_id = None
            db.session.add(slot)
            db.session.commit()
        form = FacebookCreds(obj=cred)
        form.schedule_monday.choices = monday_list
        form.schedule_tuesday.choices = tuesday_list
        form.schedule_wednesday.choices = wednesday_list
        form.schedule_thursday.choices = thursday_list
        form.schedule_friday.choices = friday_list
        form.schedule_saturday.choices = saturday_list
        form.schedule_sunday.choices = sunday_list
        if form.validate_on_submit():
            cred.alias = form.alias.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            flash("Facebook account updated!")
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=200, status_message='facebook|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
    elif platform == 'twitter':
        cred = TwitterCred.query.filter_by(id=cred_id).first()
        if cred is None:
            flash("ERROR: Account not found. Are you sure it wasn't deleted?")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=404, status_message='Cred not found')
            return redirect(url_for('auth.link_social'))
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=403, status_message='twitter|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        slots = TimeSlot.query.filter_by(twitter_cred_id=cred.id).all()
        for slot in slots:
            slot.twitter_cred_id = None
            slot.domain_id = None
            db.session.add(slot)
            db.session.commit()
        form = TwitterCreds(obj=cred)
        form.schedule_monday.choices = monday_list
        form.schedule_tuesday.choices = tuesday_list
        form.schedule_wednesday.choices = wednesday_list
        form.schedule_thursday.choices = thursday_list
        form.schedule_friday.choices = friday_list
        form.schedule_saturday.choices = saturday_list
        form.schedule_sunday.choices = sunday_list
        if form.validate_on_submit():
            cred.alias = form.alias.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            flash("Twitter account updated!")
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=200, status_message='twitter|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
    elif platform == 'tumblr':
        cred = TumblrCred.query.filter_by(id=cred_id).first()
        if cred is None:
            flash("ERROR: Account not found. Are you sure it wasn't deleted?")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=404, status_message='Cred not found')
            return redirect(url_for('auth.link_social'))
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=403, status_message='tumblr|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        slots = TimeSlot.query.filter_by(tumblr_cred_id=cred.id).all()
        for slot in slots:
            slot.tumblr_cred_id = None
            slot.domain_id = None
            db.session.add(slot)
            db.session.commit()
        form = TumblrCreds(obj=cred)
        form.schedule_monday.choices = monday_list
        form.schedule_tuesday.choices = tuesday_list
        form.schedule_wednesday.choices = wednesday_list
        form.schedule_thursday.choices = thursday_list
        form.schedule_friday.choices = friday_list
        form.schedule_saturday.choices = saturday_list
        form.schedule_sunday.choices = sunday_list
        if form.validate_on_submit():
            cred.alias = form.alias.data
            cred.blog_name = form.blog_name.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            flash("Tumblr account updated!")
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=200, status_message='tumblr|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
    elif platform == 'reddit':
        cred = RedditCred.query.filter_by(id=cred_id).first()
        if cred is None:
            flash("ERROR: Account not found. Are you sure it wasn't deleted?")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=404, status_message='Cred not found')
            return redirect(url_for('auth.link_social'))
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=403, status_message='reddit|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        slots = TimeSlot.query.filter_by(reddit_cred_id=cred.id).all()
        for slot in slots:
            slot.reddit_cred_id = None
            slot.domain_id = None
            db.session.add(slot)
            db.session.commit()
        form = RedditCreds(obj=cred)
        form.schedule_monday.choices = monday_list
        form.schedule_tuesday.choices = tuesday_list
        form.schedule_wednesday.choices = wednesday_list
        form.schedule_thursday.choices = thursday_list
        form.schedule_friday.choices = friday_list
        form.schedule_saturday.choices = saturday_list
        form.schedule_sunday.choices = sunday_list
        if form.validate_on_submit():
            cred.alias = form.alias.data
            cred.target_subreddit = form.target_subreddit.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != 0:
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    slot.domain_id = current_user.domain_id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            flash("Reddit account updated!")
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=200, status_message='reddit|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
    else:
        flash("ERROR: Malformed request; platform not found.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=400, status_message='{}'.format(platform))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/edit_cred.html', title='Update Your {} Account'.format(str(platform).capitalize()), form=form, platform=str(platform).capitalize(), time=datetime.utcnow())

# Works, 2020-08-13
@bp.route('/delete/cred/<platform>/<cred_id>')
@fresh_login_required
def delete_cred(platform, cred_id):
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.delete_cred', status_code=403, status_message='{}|{}'.format(platform, cred_id))
        return redirect(url_for('main.dashboard'))
    if platform == 'facebook':
        cred = FacebookCred.query.filter_by(id=cred_id).first()
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.delete_cred', status_code=403, status_message='facebook|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        posts = FacebookPost.query.filter_by(cred_id=cred.id).all()
        slots = TimeSlot.query.filter_by(facebook_cred_id=cred.id).all()
        if cred is not None:
            db.session.delete(cred)
            db.session.commit()
            for slot in slots:
                slot.facebook_cred_id = None
                slot.domain_id = None
                db.session.add(slot)
                db.session.commit()
            for post in posts:
                db.session.delete(post)
                db.session.commit()
            flash("Successfully deleted!")
            return redirect(url_for('auth.link_social'))
        else:
            flash("ERROR: Account not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('auth.link_social'))
    elif platform == 'twitter':
        cred = TwitterCred.query.filter_by(id=cred_id).first()
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.delete_cred', status_code=403, status_message='twitter|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        posts = TwitterPost.query.filter_by(cred_id=cred.id).all()
        slots = TimeSlot.query.filter_by(twitter_cred_id=cred.id).all()
        if cred is not None:
            db.session.delete(cred)
            db.session.commit()
            for slot in slots:
                slot.twitter_cred_id = None
                slot.domain_id = None
                db.session.add(slot)
                db.session.commit()
            for post in posts:
                db.session.delete(post)
                db.session.commit()
            flash("Successfully deleted!")
            return redirect(url_for('auth.link_social'))
        else:
            flash("ERROR: Account not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('auth.link_social'))
    elif platform == 'tumblr':
        cred = TumblrCred.query.filter_by(id=cred_id).first()
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.delete_cred', status_code=403, status_message='tumblr|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        posts = TumblrPost.query.filter_by(cred_id=cred.id).all()
        slots = TimeSlot.query.filter_by(tumblr_cred_id=cred.id).all()
        if cred is not None:
            db.session.delete(cred)
            db.session.commit()
            for slot in slots:
                slot.tumblr_cred_id = None
                slot.domain_id = None
                db.session.add(slot)
                db.session.commit()
            for post in posts:
                db.session.delete(post)
                db.session.commit()
            flash("Successfully deleted!")
            return redirect(url_for('auth.link_social'))
        else:
            flash("ERROR: Account not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('auth.link_social'))
    elif platform == 'reddit':
        cred = RedditCred.query.filter_by(id=cred_id).first()
        if current_user.domain_id != cred.domain_id:
            flash("ERROR: You don't have permission to do that.")
            make_sentry(user_id=current_user.id, domain_id=cred.domain_id, ip_address=request.remote_addr, endpoint='auth.delete_cred', status_code=403, status_message='reddit|{}'.format(cred_id))
            return redirect(url_for('auth.link_social'))
        posts = RedditPost.query.filter_by(cred_id=cred.id).all()
        slots = TimeSlot.query.filter_by(reddit_cred_id=cred.id).all()
        if cred is not None:
            db.session.delete(cred)
            db.session.commit()
            for slot in slots:
                slot.reddit_cred_id = None
                slot.domain_id = None
                db.session.add(slot)
                db.session.commit()
            for post in posts:
                db.session.delete(post)
                db.session.commit()
            flash("Successfully deleted!")
            return redirect(url_for('auth.link_social'))
        else:
            flash("ERROR: Account not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('auth.link_social'))
    else:
        flash("ERROR: Malformed request; platform not found.")
        return redirect(url_for('auth.link_social'))

# Works, 2020-08-13
@bp.route('/literature/<document_name>')
def send_literature(document_name):
    return send_from_directory('static/resources', document_name)