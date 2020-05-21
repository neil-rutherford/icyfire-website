from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, DomainRegistrationForm, UserRegistrationForm, ContractorRegistrationForm
from app.models import User, Sentry, Domain

# HELPER FUNCTION
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id)
    db.session.add(activity)
    db.session.commit()

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
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=str(form.email.data)).first()
        if user is None or not user.check_password(str(form.password.data)):
            make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='auth.login', status_code=401, status_message='{}|{}'.format(str(form.email.data), str(form.password.data)))
            flash('Invalid email or password!')
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
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.logout', status_code=200, status_message='Successful logout.')
    return redirect(url_for('promo.home'))

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
        domain.domain_name = str(form.domain_name.data)
        db.session.add(user)
        db.session.add(domain)
        db.session.commit()
        login_user(user, remember_me=bool(form.remember_me.data))
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
        db.session.add(user)
        db.session.commit()
        login_user(user, remember_me=bool(form.remember_me.data))
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
        user.icyfire_crta = 'USA-' + str(form.icyfire_region.data) + '-' + str(form.icyfire_team.data) + '-' + str(form.icyfire_agent.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.register_user', status_code=200, status_message='User creation successful.')
        if str(form.icyfire_team.data) == '00' and str(form.icyfire_agent.data) == '00':
            region_lead = RegionLead(user_id=current_user.id)
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

# Not finished
@bp.route('/register/link-social')
@login_required
def link_social():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='auth.link_social', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('main.dashboard'))
    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    if domain.facebook_token is None:
        facebook_creds = False
    if domain.twitter_token is None or domain.twitter_secret is None:
        twitter_creds = False
    if domain.tumblr_blog_name is None or domain.tumblr_token is None or domain.tumblr_secret is None:
        tumblr_creds = False
    if domain.reddit_subreddit is None or domain.reddit_username is None or domain.reddit_password is None:
        reddit_creds = False
    if domain.youtube_refresh is None or domain.youtube_access is None:
        youtube_creds = False
    if domain.linkedin_author is None or domain.linkedin_token is None or domain.linkedin_secret is None:
        linkedin_creds = False
    if facebook_creds is True and twitter_creds is True and tumblr_creds is True and reddit_creds is True and youtube_creds is True and linkedin_creds is True:
        flash("Welcome to IcyFire! We're so glad you're here.")
        return redirect(url_for('main.dashboard'))
    else:
        return redirect(url_for('auth.link_social'))
    return render_template('auth/link_social.html', title="Link Your Social Media Accounts", facebook_creds=facebook_creds, twitter_creds=twitter_creds, tumblr_creds=tumblr_creds, reddit_creds=reddit_creds, youtube_creds=youtube_creds, linkedin_creds=linkedin_creds)