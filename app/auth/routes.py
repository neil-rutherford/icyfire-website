from flask import render_template, redirect, url_for, flash, request, current_app, send_from_directory
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required, fresh_login_required
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, DomainRegistrationForm, UserRegistrationForm, ContractorRegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, FacebookCreds, TwitterCreds, TumblrCreds, RedditCreds
from app.models import User, Sentry, Domain, FacebookCred, TwitterCred, TumblrCred, RedditCred, TimeSlot
from app.auth.email import send_password_reset_email
import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from datetime import datetime

# SENTRY HELPER FUNCTION
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

# ENCRYPTION HELPER FUNCTION
def encrypt(message):
    password_provided = current_app.config['SECRET_KEY']
    password = password_provided.encode()
    salt = current_app.config['SALT'].encode()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password))
    message = message.encode()
    f = Fernet(key)
    encrypted = f.encrypt(message)
    return encrypted

# LOGIN DEFENSE
@bp.route('/login-defense')
def login_defense():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.login', status_code=303, status_message='Redirected', flag=True)
    return render_template('auth/login_defense.html', title='Woah there!')

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

@bp.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register.html', title='Register')

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
        user.email_opt_in = form.email_opt_in.data
        domain.domain_name = str(form.domain_name.data)
        db.session.add(user)
        db.session.add(domain)
        db.session.commit()
        login_user(user, remember=True)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_domain', status_code=200, status_message='{}'.format(domain.domain_name))
        flash("Welcome to IcyFire! Let's link your social media accounts.")
        return redirect(url_for('auth.link_social'))
    return render_template('auth/register_domain.html', title='Register Your New Domain', form=form)

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
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_user', status_code=200, status_message='{}'.format(str(form.domain_name.data)))
        flash("As a security precaution, new users have limited permissions by default. This will change once your domain admin gives your account the all clear.")
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register_user.html', title='New User Registration', form=form)

# NEW CONTRACTOR REGISTRATION PAGE
@bp.route('/register/contractor', methods=['GET', 'POST'])
def register_contractor():
    '''
    - Sentry logs:
        + auth.register_user 200 = user created successfully 
        + auth.register_contractor.region_lead 200 = region lead created successfully
        + auth.register_contractor.team_lead 200 = team lead created successfully
        + auth.register_contractor.agent 200 = agent created successfully
    - If the user is already logged in, it directs them to their dashboard.
    - A new user is created and linked to the IcyFire domain.
    - As a security measure, all of the user's CRUD permissions are set to False.
    - Sentry logs the user creation event and hopefully updates the domain admin.
    - The new user is logged in.
    - Depending upon the user's CRTA (Country-Region-Team-Agent) code, a hierarchical entry will also be created. This will be used to track sales performance.
    - The user is redirected to their dashboard.
    '''
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = ContractorRegistrationForm()
    if form.validate_on_submit():
        domain = Domain.query.filter_by(domain_name='icyfire').first()
        user = User(email=str(form.email.data))
        user.domain_id = domain.id
        user.set_password(str(form.password.data))
        user.is_admin = False
        user.is_create = False
        user.is_read = False
        user.is_update = False
        user.is_delete = False
        user.email_opt_in = True
        user.icyfire_crta = 'USA-' + str(form.icyfire_region.data) + '-' + str(form.icyfire_team.data) + '-' + str(form.icyfire_agent.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_user', status_code=200, status_message='User creation successful.')
        if str(form.icyfire_team.data) == '00' and str(form.icyfire_agent.data) == '00':
            region_lead = RegionLead(user_id=current_user.id)
            region_lead.email = current_user.email
            region_lead.first_name = str(form.first_name.data)
            region_lead.last_name = str(form.last_name.data)
            region_lead.phone_country = 1
            region_lead.phone_number = int(form.phone_number.data)
            region_lead.crta_code = current_user.icyfire_crta
            country_lead = CountryLead.query.filter_by(crta_code='USA-00-00-00').first()
            region_lead.country_lead_id = country_lead.id
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_contractor.region_lead', status_code=200, status_message='Region Lead creation successful.')
            db.session.add(region_lead)
            db.session.commit()
        elif str(form.icyfire_agent.data) == '00':
            team_lead = TeamLead(user_id=current_user.id)
            team_lead.email = current_user.email
            team_lead.first_name = str(form.first_name.data)
            team_lead.last_name = str(form.last_name.data)
            team_lead.phone_country = 1
            team_lead.phone_number = int(form.phone_number.data)
            team_lead.crta_code = current_user.icyfire_crta
            region_lead = RegionLead.query.filter_by(crta_code='USA-{}-00-00'.format(str(form.icyfire_region.data))).first()
            team_lead.region_lead_id = region_lead.id
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_contractor.team_lead', status_code=200, status_message='Team Lead creation successful.')
            db.session.add(team_lead)
            db.session.commit()
        else:
            agent = Agent(user_id=current_user.id)
            agent.email = current_user.email
            agent.first_name = str(form.first_name.data)
            agent.last_name = str(form.last_name.data)
            agent.phone_country = 1
            agent.phone_number = int(form.phone_number.data)
            agent.crta_code = current_user.icyfire_crta
            team_lead = TeamLead.query.filter_by(crta_code='USA-{}-{}-00'.format(str(form.icyfire_region.data), str(form.icyfire_team.data))).first()
            agent.team_lead_id = team_lead.id
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_contractor.agent', status_code=200, status_message='Agent creation successful.')
            db.session.add(agent)
            db.session.commit()
        flash("As a security precaution, new users have limited permissions by default. This will change once your domain admin gives your account the all clear.")
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register_contractor.html', title='New Contractor Registration', form=form)

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
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.reset_password_request', status_code=200, status_message='OK')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    user = User.verify_reset_password_token(token)
    if not user:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.reset_token', status_code=404, status_message='User not found')
        return redirect(url_for('promo.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.reset_token', status_code=200, status_message='OK')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@bp.route('/register/link-social')
@login_required
def link_social():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_social', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
    twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
    tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
    reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_social', status_code=200, status_message='OK')
    return render_template('auth/link_social.html', title="Link Your Social Media Accounts", domain=domain, facebook_creds=facebook_creds, twitter_creds=twitter_creds, tumblr_creds=tumblr_creds, reddit_creds=reddit_creds)

@bp.route('/register/link-social/facebook', methods=['GET', 'POST'])
@login_required
def link_facebook():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_facebook', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).all()
    #
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, ('0', "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, ('0', "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, ('0', "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, ('0', "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, ('0', "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, ('0', "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, ('0', "I don't want to post on Sundays."))
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
        cred.domain_id = current_user.domain_id
        cred.alias = form.alias.data
        db.session.add(cred)
        db.session.commit()
        if form.schedule_monday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_tuesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_wednesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_thursday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_friday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_saturday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        if form.schedule_sunday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.facebook_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_facebook'))
        flash("Facebook account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_facebook', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_facebook.html', title='Link A Facebook Account', form=form, time=datetime.utcnow())

@bp.route('/register/link-social/twitter', methods=['GET', 'POST'])
@login_required
def link_twitter():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_twitter', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, ('0', "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, ('0', "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, ('0', "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, ('0', "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, ('0', "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, ('0', "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, ('0', "I don't want to post on Sundays."))
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
        if form.schedule_monday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_tuesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_wednesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_thursday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_friday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_saturday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        if form.schedule_sunday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.twitter_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_twitter'))
        flash("Twitter account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_twitter', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_twitter.html', title='Link A Twitter Account', form=form, time=datetime.utcnow())

@bp.route('/register/link-social/tumblr', methods=['GET', 'POST'])
@login_required
def link_tumblr():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_tumblr', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, ('0', "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, ('0', "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, ('0', "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, ('0', "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, ('0', "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, ('0', "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, ('0', "I don't want to post on Sundays."))
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
        cred.alias = form.alias.data
        db.session.add(cred)
        db.session.commit()
        if form.schedule_monday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_tuesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_wednesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_thursday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_friday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_saturday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        if form.schedule_sunday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.tumblr_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_tumblr'))
        flash("Tumblr account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_tumblr', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_tumblr.html', title='Link A Tumblr Account', form=form, time=datetime.utcnow())

@bp.route('/register/link-social/reddit', methods=['GET', 'POST'])
@login_required
def link_reddit():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_reddit', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, ('0', "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, ('0', "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, ('0', "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, ('0', "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, ('0', "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, ('0', "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, ('0', "I don't want to post on Sundays."))
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
        db.session.add(cred)
        db.session.commit()
        if form.schedule_monday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_tuesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_wednesday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_thursday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_friday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_saturday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        if form.schedule_sunday.data != '0':
            slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
            if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                slot.reddit_cred_id = cred.id
                db.session.add(slot)
                db.session.commit()
            else:
                flash("We just double-checked and that Sunday time slot isn't available anymore. Sorry!")
                return redirect(url_for('auth.link_reddit'))
        flash("Reddit account linked!")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_reddit', status_code=200, status_message='{}'.format(cred.id))
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_reddit.html', title='Link A Reddit Account', form=form, time=datetime.utcnow())

@bp.route('/edit/cred/<platform>/<cred_id>', methods=['GET', 'POST'])
@fresh_login_required
def edit_cred(platform, cred_id):
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.edit_cred', status_code=403, status_message='{}|{}'.format(platform, cred_id))
        return redirect(url_for('main.dashboard'))
    monday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 1).all()
    tuesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 2).all()
    wednesday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 3).all()
    thursday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 4).all()
    friday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 5).all()
    saturday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 6).all()
    sunday_availability = TimeSlot.query.filter(TimeSlot.facebook_cred_id == None, TimeSlot.twitter_cred_id == None, TimeSlot.tumblr_cred_id == None, TimeSlot.reddit_cred_id == None, TimeSlot.day_of_week == 7).all()
    monday_list = [(i.id, i.time) for i in monday_availability]
    monday_list.insert(0, ('0', "I don't want to post on Mondays."))
    tuesday_list = [(i.id, i.time) for i in tuesday_availability]
    tuesday_list.insert(0, ('0', "I don't want to post on Tuesdays."))
    wednesday_list = [(i.id, i.time) for i in wednesday_availability]
    wednesday_list.insert(0, ('0', "I don't want to post on Wednesdays."))
    thursday_list = [(i.id, i.time) for i in thursday_availability]
    thursday_list.insert(0, ('0', "I don't want to post on Thursdays."))
    friday_list = [(i.id, i.time) for i in friday_availability]
    friday_list.insert(0, ('0', "I don't want to post on Fridays."))
    saturday_list = [(i.id, i.time) for i in saturday_availability]
    saturday_list.insert(0, ('0', "I don't want to post on Saturdays."))
    sunday_list = [(i.id, i.time) for i in sunday_availability]
    sunday_list.insert(0, ('0', "I don't want to post on Sundays."))
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
            db.session.add(slot)
            db.session.commit()
        form = FacebookCreds(obj=cred)
        if form.validate_on_submit():
            cred.alias = form.alias.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.facebook_cred_id = cred.id
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
            db.session.add(slot)
            db.session.commit()
        form = TwitterCreds(obj=cred)
        if form.validate_on_submit():
            cred.alias = form.alias.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.twitter_cred_id = cred.id
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
            db.session.add(slot)
            db.session.commit()
        form = TumblrCreds(obj=cred)
        if form.validate_on_submit():
            cred.alias = form.alias.data
            cred.blog_name = form.blog_name.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.tumblr_cred_id = cred.id
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
            db.session.add(slot)
            db.session.commit()
        form = RedditCreds(obj=cred)
        if form.validate_on_submit():
            cred.alias = form.alias.data
            cred.target_subreddit = form.target_subreddit.data
            db.session.add(cred)
            db.session.commit()
            if form.schedule_monday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_monday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Monday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_tuesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_tuesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Tuesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_wednesday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_wednesday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Wednesday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_thursday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_thursday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Thursday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_friday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_friday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Friday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_saturday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_saturday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
                    db.session.add(slot)
                    db.session.commit()
                else:
                    flash("We just double-checked and that Saturday time slot isn't available anymore. Sorry!")
                    return redirect(url_for("auth.edit_cred, platform=platform, cred_id=cred_id"))
            if form.schedule_sunday.data != '0':
                slot = TimeSlot.query.filter_by(id=form.schedule_sunday.data).first()
                if slot.facebook_cred_id is None and slot.twitter_cred_id is None and slot.tumblr_cred_id is None and slot.reddit_cred_id is None:
                    slot.reddit_cred_id = cred.id
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

@bp.route('/literature/<document_name>')
def send_literature(document_name):
    basedir = os.path.abspath(os.path.dirname(__file__))
    document_folder = os.path.join(basedir, 'app', 'static', 'resources')
    document_folder = document_folder.replace('\\', '/')
    filename = '{}.pdf'.format(document_name)
    return send_from_directory(document_folder, filename, as_attachment=True)