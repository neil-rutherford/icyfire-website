from flask import render_template, flash, redirect, url_for, request, jsonify, Response, send_from_directory
from app import app, db
from app.forms import LoginForm, DomainRegistrationForm, UserRegistrationForm, ContractorRegistrationForm, ShortTextPostForm, LongTextPostForm, ImagePostForm, VideoPostForm, SaleForm
from app.models import Domain, User, FacebookPost, TwitterPost, TumblrPost, RedditPost, YoutubePost, LinkedinPost, Ewok, Sentry, CountryLead, RegionLead, TeamLead, Agent
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import uuid
import pdfrw
import os

'''
TO-DO:

    - Finish link_social()
    - Finish link_social.html

    - DOMAIN REGISTRATION
        + Link social networks and store tokens
        + Request time slots
        + User registration (must be linked to domain) (permissions)
    - USER INTERFACE
        + Create
        + Read
        + Update
        + Delete
    - API
        + Read
        + Delete
        + Get creds
    - LOGIN
    - ERROR HANDLING
    - EMAIL SUPPORT
    - ARTICLES AND MARKETING PAGES
    - HELP PAGES AND TUTORIALS
    - SECURITY
        + Domain-level
        + App-level
'''

def make_ewok(user_id, ip_address, endpoint, status_code, status_message):
    incident = Ewok(ip_address=str(ip_address), endpoint=str(endpoint))
    incident.user_id = user_id
    incident.status_code = int(status_code)
    incident.status_message = str(status_message)
    db.session.add(incident)
    db.session.commit()

def make_sentry(user_id, ip_address, endpoint, status_code, status_message):
    activity = Sentry(ip_address=str(ip_address), user_id=int(user_id), endpoint=str(endpoint))
    activity.status_code = int(status_code)
    activity.status_message = str(status_message)
    db.session.add(activity)
    db.session.commit()

def make_facebook(domain_id, user_id, post_type, body, link_url, multimedia_url, tags):
    post = FacebookPost(body=body)
    post.domain_id = domain_id
    post.user_id = user_id
    post.post_type = post_type
    post.link_url = link_url
    post.multimedia_url = multimedia_url
    post.tags = tags
    db.session.add(post)
    db.session.commit()

def make_twitter(domain_id, user_id, post_type, body, link_url, multimedia_url, tags):
    post = TwitterPost(body=body)
    post.domain_id = domain_id
    post.user_id = user_id
    post.post_type = post_type
    post.link_url = link_url
    post.multimedia_url = multimedia_url
    post.tags = tags
    db.session.add(post)
    db.session.commit()

def make_tumblr(domain_id, user_id, post_type, title, body, link_url, multimedia_url, tags, caption):
    post = TumblrPost(body=body)
    post.domain_id = domain_id
    post.user_id = user_id
    post.post_type = post_type
    post.title = title
    post.link_url = link_url
    post.multimedia_url = multimedia_url
    post.tags = tags
    post.caption = caption
    db.session.add(post)
    db.session.commit()

def make_reddit(domain_id, user_id, post_type, title, body, link_url, image_url, video_url):
    post = RedditPost(body=body)
    post.domain_id = domain_id
    post.user_id = user_id
    post.post_type = post_type
    post.title = title
    post.link_url = link_url
    post.image_url = image_url
    post.video_url = video_url
    db.session.add(post)
    db.session.commit()

def make_youtube(domain_id, user_id, multimedia_url, title, caption, tags, category):
    post = YoutubePost(title=title)
    post.domain_id = domain_id
    post.user_id = user_id
    post.multimedia_url = multimedia_url
    post.caption = caption
    post.tags = tags
    post.category = category
    db.session.add(post)
    db.session.commit()

def make_linkedin(domain_id, user_id, post_type, title, body, caption, multimedia_url, link_url, tags):
    post = LinkedinPost(body=body)
    post.domain_id = domain_id
    post.user_id = user_id
    post.post_type = post_type
    post.title = title
    post.caption = caption
    post.multimedia_url = multimedia_url
    post.link_url = link_url
    post.tags = tags
    db.session.add(post)
    db.session.commit()

def fill_pdf_template(input_path, output_path, data_dict):
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

# User control and permissions

@app.route('/register/domain', methods=['GET', 'POST'])
def register_domain():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = DomainRegistrationForm()
    if form.validate_on_submit():
        user = User(email=str(form.email.data))
        domain = Domain.query.filter_by(activation_code=str(form.activation_code.data)).first()
        user.set_password(str(form.password.data))
        user.domain_id = int(domain.id)
        user.post_count = int(0)
        user.is_admin = bool(True)
        user.is_create = bool(True)
        user.is_read = bool(True)
        user.is_update = bool(True)
        user.is_delete = bool(True)
        domain.domain_name = str(form.domain_name.data)
        db.session.add(user)
        db.session.add(domain)
        db.session.commit()
        login_user(user, remember_me=bool(form.remember_me.data))
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/register/domain', status_code=200, status_message='Domain creation successful.')
        flash("Welcome to IcyFire! Let's link your social media accounts.")
        return redirect(url_for('link_social'))
    return render_template('register_domain.html', title='Register Your New Domain', form=form)

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        user = User(email=str(form.email.data))
        domain = Domain.query.filter_by(domain_name=str(form.domain_name.data)).first()
        user.set_password(str(form.password.data))
        user.domain_id = int(domain.id)
        user.post_count = int(0)
        user.is_admin = bool(False)
        user.is_create = bool(False)
        user.is_read = bool(False)
        user.is_update = bool(False)
        user.is_delete = bool(False)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember_me=bool(form.remember_me.data))
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/register/user', status_code=200, status_message='User creation successful.')
        flash("As a security precaution, new users have limited permissions by default. This will change once your domain admin gives your account the all clear.")
        return redirect(url_for('dashboard'))
    return render_template('register_user.html', title='New User Registration', form=form)

@app.route('/register/sales', methods=['GET', 'POST'])
def register_sales():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/register/sales', status_code=200, status_message='User creation successful.')
        if str(form.icyfire_team.data) == '00' and str(form.icyfire_agent.data) == '00':
            region_lead = RegionLead(user_id=current_user.id)
            region_lead.first_name = str(form.first_name.data)
            region_lead.last_name = str(form.last_name.data)
            region_lead.phone_country = int(1)
            region_lead.phone_number = int(form.phone_number.data)
            region_lead.crta_code = current_user.icyfire_crta
            country_lead = CountryLead.query.filter_by(crta_code='USA-00-00-00').first()
            region_lead.country_lead_id = country_lead.id
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/register/sales', status_code=200, status_message='Region Lead creation successful.')
            db.session.add(region_lead)
            db.session.commit()
        elif str(form.icyfire_agent.data) == '00':
            team_lead = TeamLead(user_id=current_user.id)
            team_lead.first_name = str(form.first_name.data)
            team_lead.last_name = str(form.last_name.data)
            team_lead.phone_country = int(1)
            team_lead.phone_number = int(form.phone_number.data)
            team_lead.crta_code = current_user.icyfire_crta
            region_lead = RegionLead.query.filter_by(crta_code='USA-{}-00-00'.format(str(form.icyfire_region.data))).first()
            team_lead.region_lead_id = region_lead.id
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/register/sales', status_code=200, status_message='Team Lead creation successful.')
            db.session.add(team_lead)
            db.session.commit()
        else:
            agent = Agent(user_id=current_user.id)
            agent.first_name = str(form.first_name.data)
            agent.last_name = str(form.last_name.data)
            agent.phone_country = int(1)
            agent.phone_number = int(form.phone_number.data)
            agent.crta_code = current_user.icyfire_crta
            team_lead = TeamLead.query.filter_by(crta_code='USA-{}-{}-00'.format(str(form.icyfire_region.data), str(form.icyfire_team.data))).first()
            agent.team_lead_id = team_lead.id
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/register/sales', status_code=200, status_message='Agent creation successful.')
            db.session.add(agent)
            db.session.commit()
    return render_template('register_sales.html', title='New Contractor Registration', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/login', status_code=401, status_message='{}/{}'.format(str(form.email.data), str(form.password.data)))
            flash('Invalid email or password!')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/login', status_code=200, status_message='Successful login.')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Log In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/logout', status_code=200, status_message='Successful logout.')
    return redirect(url_for('home'))

# Not done
@app.route('/register/link/social')
@login_required
def link_social():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/register/link/social', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('dashboard'))
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
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('link_social'))
    return render_template('link_social.html', title="Link Your Social Media Accounts", facebook_creds=facebook_creds, twitter_creds=twitter_creds, tumblr_creds=tumblr_creds, reddit_creds=reddit_creds, youtube_creds=youtube_creds, linkedin_creds=linkedin_creds)

@app.route('/admin')
@login_required
def admin():
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/admin', status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('dashboard'))
    make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/admin', status_code=200, status_message='Successful admin access.')
    users = User.query.filter_by(domain_id=current_user.domain_id).order_by(User.id.desc()).all()
    return render_template('admin.html', title='User Control Panel', users=users)

@app.route('/admin/<user_id>/+<permission>', methods=['GET', 'POST'])
@login_required
def grant_permission(user_id, permission):
    user = User.query.filter_by(id=int(user_id)).first()
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/+{}'.format(user_id, permission), status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('dashboard'))
    elif current_user.domain_id != user.domain_id:
        flash("ERROR: That user isn't part of your domain.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/+{}'.format(user_id, permission), status_code=403, status_message='User not in domain.')
        return redirect(url_for('admin'))
    elif str(permission) == 'c':
        user.is_create = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/+{}'.format(user_id, permission), status_code=200, status_message='Permission granted: Create.')
        flash("Create permission granted.")
        return redirect(url_for('admin'))
    elif str(permission) == 'r':
        user.is_read = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/+{}'.format(user_id, permission), status_code=200, status_message='Permission granted: Read.')
        flash("Read permission granted.")
        return redirect(url_for('admin'))
    elif str(permission) == 'u':
        user.is_update = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/+{}'.format(user_id, permission), status_code=200, status_message='Permission granted: Update.')
        flash("Update permission granted.")
        return redirect(url_for('admin'))
    elif str(permission) == 'd':
        user.is_delete = True
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/+{}'.format(user_id, permission), status_code=200, status_message='Permission granted: Delete.')
        flash('Delete permission granted.')
        return redirect(url_for('admin'))
    else:
        flash('ERROR: Not a valid permission.')
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/+{}'.format(user_id, permission), status_code=400, status_message='Not a valid permission.')
        return redirect(url_for('admin'))

@app.route('/admin/<user_id>/-<permission>', methods=['GET', 'POST'])
@login_required
def revoke_permission(user_id, permission):
    user = User.query.filter_by(id=int(user_id)).first()
    if current_user.is_admin is False:
        flash("ERROR: You don't have permission to do that.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=403, status_message='Admin permission denied.')
        return redirect(url_for('admin'))
    elif current_user.domain_id != user.domain_id:
        flash("ERROR: That user isn't part of your domain.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=403, status_message='User not in domain.')
        return redirect(url_for('admin'))
    elif str(permission) == 'c':
        user.is_create = False
        db.session.add(user)
        db.session.commit()
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=200, status_message='Permission revoked: Create.')
        flash("Create permission revoked.")
        return redirect(url_for('admin'))
    elif str(permission) == 'r':
        user.is_read = False
        db.session.add(user)
        db.session.commit()
        flash("Read permission revoked.")
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=200, status_message='Permission revoked: Read.')
        return redirect(url_for('admin'))
    elif str(permission) == 'u':
        user.is_update = False
        db.session.add(user)
        db.session.commit()
        flash("Update permission revoked.")
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=200, status_message='Permission revoked: Update.')
        return redirect(url_for('admin'))
    elif str(permission) == 'd':
        user.is_delete = False
        db.session.add(user)
        db.session.commit()
        flash('Delete permission revoked.')
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=200, status_message='Permission revoked: Delete.')
        return redirect(url_for('admin'))
    elif str(permission) == 'kill':
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.')
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=200, status_message='User deleted.')
        return(redirect(url_for('admin')))
    else:
        flash('ERROR: Not a valid permission.')
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/{}/-{}'.format(user_id, permission), status_code=400, status_message='Not a valid permission.')
        return redirect(url_for('admin'))

# Post management

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.is_read is False:
        flash("ERROR: Talk to your domain admin about getting read permissions.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/dashboard', status_code=403, status_message='Read permission denied.')
        return redirect(url_for('dashboard'))
    facebook_queue = FacebookPost.query.filter_by(domain_id=current_user.domain_id).order_by(FacebookPost.timestamp.asc()).all()
    twitter_queue = TwitterPost.query.filter_by(domain_id=current_user.domain_id).order_by(TwitterPost.timestamp.asc()).all()
    tumblr_queue = TumblrPost.query.filter_by(domain_id=current_user.domain_id).order_by(TumblrPost.timestamp.asc()).all()
    reddit_queue = RedditPost.query.filter_by(domain_id=current_user.domain_id).order_by(RedditPost.timestamp.asc()).all()
    youtube_queue = YoutubePost.query.filter_by(domain_id=current_user.domain_id).order_by(YoutubePost.timestamp.asc()).all()
    linkedin_queue = LinkedinPost.query.filter_by(domain_id=current_user.domain_id).order_by(LinkedinPost.timestamp.asc()).all()
    make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/dashboard', status_code=200, status_message='Successful dashboard access.')
    return render_template('dashboard.html', facebook_queue=facebook_queue, twitter_queue=twitter_queue, tumblr_queue=tumblr_queue, reddit_queue=reddit_queue, youtube_queue=youtube_queue, linkedin_queue=linkedin_queue)

@app.route('/create/short-text', methods=['GET', 'POST'])
@login_required
def create_short_text():
    if current_user.is_create is False:
        flash("You don't have permission to do that.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/short-text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('dashboard'))
    form = ShortTextPostForm()
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if form.is_facebook.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/short-text', status_code=200, status_message='Facebook short text created.')
        if form.is_twitter.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/short-text', status_code=200, status_message='Twitter short text created.')
        if form.is_tumblr.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=str(tags), caption=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/short-text', status_code=200, status_message='Tumblr short text created.')
        if form.is_reddit.data is True:
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/short-text', status_code=200, status_message='Reddit short text created.')
        if form.is_linkedin.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/short-text', status_code=200, status_message='LinkedIn short text created.')
        flash('Successfully queued!')
        return redirect(url_for('dashboard'))
    return render_template('create_short_text.html', title='New Short Text Post', form=form)

@app.route('/create/long-text', methods=['GET', 'POST'])
@login_required
def create_long_text():
    if current_user.is_create is False:
        flash("You don't have permission to do that.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/long-text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('dashboard'))
    form = LongTextPostForm()
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if form.is_facebook.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/long-text', status_code=200, status_message='Facebook long text created.')
        if form.is_tumblr.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=str(tags), caption=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/long-text', status_code=200, status_message='Tumblr long text created.')
        if form.is_reddit.data is True:
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/long-text', status_code=200, status_message='Reddit long text created.')
        if form.is_linkedin.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/long-text', status_code=200, status_message='LinkedIn long text created.')
        flash('Successfully queued!')
        return redirect(url_for('dashboard'))
    return render_template('create_long_text.html', title='New Long Text Post', form=form)

@app.route('/create/image', methods=['GET', 'POST'])
#@login_required
def create_image():
    #if current_user.is_create is False:
        #flash("You don't have permission to do that.")
        #make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/image', status_code=403, status_message='Create permission denied.')
        #return redirect(url_for('dashboard'))
    form = ImagePostForm()
    if form.validate_on_submit():
        #current_user.post_count += 1
        #db.session.add(current_user)
        #db.session.commit()
        image_name = str(uuid.uuid4())
        f = form.image.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if form.is_facebook.data is True:
            filename = secure_filename('facebook-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            #make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_image', filename), tags='#' + tagline)
            #make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/image', status_code=200, status_message='Facebook image created.')
        if form.is_twitter.data is True:
            filename = secure_filename('twitter-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_image', filename), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/image', status_code=200, status_message='Twitter image created.')
        if form.is_tumblr.data is True:
            filename = secure_filename('tumblr-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('get_image', filename), tags=str(tags), caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/image', status_code=200, status_message='Tumblr image created.')
        if form.is_reddit.data is True:
            filename = secure_filename('reddit-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=url_for('get_image', filename), video_url=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/image', status_code=200, status_message='Reddit image created.')
        if form.is_linkedin.data is True:
            filename = secure_filename('linkedin-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('get_image', filename), link_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/image', status_code=200, status_message='LinkedIn image created.')
        flash('Successfully queued!')
        return redirect(url_for('dashboard'))
    return render_template('create_image.html', title='New Image Post', form=form)    

@app.route('/create/video', methods=['GET', 'POST'])
@login_required
def create_video():
    if current_user.is_create is False:
        flash("You don't have permission to do that.")
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/video', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('dashboard'))
    form = VideoPostForm()
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        video_name = str(uuid.uuid4())
        f = form.video.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if form.is_facebook.data is True:
            filename = secure_filename('facebook-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_video', filename), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/video', status_code=200, status_message='Facebook video created.')
        if form.is_twitter.data is True:
            filename = secure_filename('twitter-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_video', filename), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/video', status_code=200, status_message='Twitter video created.')
        if form.is_tumblr.data is True:
            filename = secure_filename('tumblr-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('get_video', filename), tags=str(tags), caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/video', status_code=200, status_message='Tumblr video created.')
        if form.is_reddit.data is True:
            filename = secure_filename('reddit-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=None, video_url=url_for('get_video', filename))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/video', status_code=200, status_message='Reddit video created.')
        if form.is_youtube.data is True:
            filename = secure_filename('youtube-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_youtube(domain_id=current_user.domain_id, user_id=current_user.id, multimedia_url=url_for('get_video', filename), title=str(form.title.data), caption=str(form.caption.data), tags='#' + tagline, category=int(form.category.data))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/video', status_code=200, status_message='YouTube video created.')
        if form.is_linkedin.data is True:
            filename = secure_filename('linkedin-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('get_video', filename), link_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/video', status_code=200, status_message='LinkedIn video created.')
        flash('Successfully queued!')
        return redirect(url_for('dashboard'))
    return render_template('create_video.html', title='New Video Post', form=form)

@app.route('/update/short-text/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_short_text(platform, post_id):
    if current_user.is_update is False:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text', status_code=403, status_message='Update permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/facebook', status_code=404, status_message='Facebook post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/twitter', status_code=404, status_message='Twitter post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/tumblr', status_code=404, status_message='Tumblr post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/reddit', status_code=404, status_message='Reddit post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/linkedin', status_code=404, status_message='LinkedIn post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    else:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/?', status_code=400, status_message='Malformed request; platform not found.')
        flash('ERROR: Malformed request; network not found.')
        return redirect(url_for('dashboard'))
    form = ShortTextPostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if platform == 'facebook':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/facebook/{}'.format(post_id), status_code=200, status_message='Facebook short text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'twitter':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/twitter/{}'.format(post_id), status_code=200, status_message='Twitter short text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'tumblr':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=str(tags), caption=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/tumblr/{}'.format(post_id), status_code=200, status_message='Tumblr short text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'reddit':
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/reddit/{}'.format(post_id), status_code=200, status_message='Reddit short text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'linkedin':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/short-text/linkedin/{}'.format(post_id), status_code=200, status_message='LinkedIn short text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
    return render_template('update_short_text.html', title='Edit Short Text Post', form=form)

@app.route('/update/long-text/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_long_text(platform, post_id):
    if current_user.is_update is False:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text', status_code=403, status_message='Update permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/facebook', status_code=404, status_message='Facebook post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/tumblr', status_code=404, status_message='Tumblr post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/reddit', status_code=404, status_message='Reddit post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/linkedin', status_code=404, status_message='LinkedIn post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    else:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/?', status_code=400, status_message='Malformed request; platform not found.')
        flash('ERROR: Malformed request; network not found.')
        return redirect(url_for('dashboard'))
    form = LongTextPostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if platform == 'facebook':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/facebook/{}'.format(post_id), status_code=200, status_message='Facebook long text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'tumblr':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=str(tags), caption=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/tumblr/{}'.format(post_id), status_code=200, status_message='Tumblr long text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'reddit':
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/reddit/{}'.format(post_id), status_code=200, status_message='Reddit long text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'linkedin':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/long-text/linkedin/{}'.format(post_id), status_code=200, status_message='LinkedIn long text updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
    return render_template('update_long_text.html', title='Edit Long Text Post', form=form)

@app.route('/update/image/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_image(platform, post_id):
    if current_user.is_update is False:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image', status_code=403, status_message='Update permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/facebook', status_code=404, status_message='Facebook post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/twitter', status_code=404, status_message='Twitter post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/tumblr', status_code=404, status_message='Tumblr post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/reddit', status_code=404, status_message='Reddit post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/linkedin', status_code=404, status_message='LinkedIn post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    else:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/?', status_code=400, status_message='Malformed request; platform not found.')
        flash('ERROR: Malformed request; network not found.')
        return redirect(url_for('dashboard'))
    form = ImagePostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        image_name = str(uuid.uuid4())
        f = form.image.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if platform == 'facebook':
            filename = secure_filename('facebook-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_image', filename), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/facebook/{}'.format(post_id), status_code=200, status_message='Facebook image updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'twitter':
            filename = secure_filename('twitter-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_image', filename), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/twitter/{}'.format(post_id), status_code=200, status_message='Twitter image updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'tumblr':
            filename = secure_filename('tumblr-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('get_image', filename), tags=str(tags), caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/tumblr/{}'.format(post_id), status_code=200, status_message='Tumblr image updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'reddit':
            filename = secure_filename('reddit-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=url_for('get_image', filename), video_url=None)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/reddit/{}'.format(post_id), status_code=200, status_message='Reddit image updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'linkedin':
            filename = secure_filename('linkedin-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(app.instance_path, 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('get_image', filename), link_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/image/linkedin/{}'.format(post_id), status_code=200, status_message='LinkedIn image updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
    return render_template('update_image.html', title='Edit Image Post', form=form)

@app.route('/update/video/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_video(platform, post_id):
    if current_user.is_update is False:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video', status_code=403, status_message='Update permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/facebook', status_code=404, status_message='Facebook post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/twitter', status_code=404, status_message='Twitter post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/tumblr', status_code=404, status_message='Tumblr post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/reddit', status_code=404, status_message='Reddit post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'youtube':
        post = YoutubePost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/youtube', status_code=404, status_message='YouTube post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/linkedin', status_code=404, status_message='LinkedIn post not found.')
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('dashboard'))
    else:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/?', status_code=400, status_message='Malformed request; platform not found.')
        flash('ERROR: Malformed request; network not found.')
        return redirect(url_for('dashboard'))
    form = VideoPostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        video_name = str(uuid.uuid4())
        f = form.video.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if platform == 'facebook':
            filename = secure_filename('facebook-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_video', filename), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/facebook/{}'.format(post_id), status_code=200, status_message='Facebook video updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'twitter':
            filename = secure_filename('twitter-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('get_video', filename), tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/twitter/{}'.format(post_id), status_code=200, status_message='Twitter video updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'tumblr':
            filename = secure_filename('tumblr-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('get_video', filename), tags=str(tags), caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/tumblr/{}'.format(post_id), status_code=200, status_message='Tumblr video updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'reddit':
            filename = secure_filename('reddit-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=None, video_url=url_for('get_video', filename))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/reddit/{}'.format(post_id), status_code=200, status_message='Reddit video updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'youtube':
            filename = secure_filename('youtube-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_youtube(domain_id=current_user.domain_id, user_id=current_user.id, multimedia_url=url_for('get_video', filename), title=str(form.title.data), caption=str(form.caption.data), tags='#' + tagline, category=int(form.category.data))
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/youtube/{}'.format(post_id), status_code=200, status_message='YouTube video updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
        elif platform == 'linkedin':
            filename = secure_filename('linkedin-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(app.instance_path, 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('get_video', filename), link_url=None, tags='#' + tagline)
            make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/update/video/linkedin/{}'.format(post_id), status_code=200, status_message='LinkedIn video updated.')
            flash('Successfully edited!')
            return redirect(url_for('dashboard'))
    return render_template('update_video.html', title='Edit Video Post', form=form)

@app.route('/delete/post/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(platform, post_id):
    if current_user.is_delete is True:
        if platform == 'facebook':
            post = FacebookPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/facebook', status_code=204, status_message='Facebook post deleted.')
                flash('Successfully deleted!')
                return redirect(url_for('dashboard'))
            else:
                make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/facebook', status_code=403, status_message='Attempted to delete post from domain {}.'.format(post.domain_id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('dashboard'))
        elif platform == 'twitter':
            post = TwitterPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/twitter', status_code=204, status_message='Twitter post deleted.')
                flash('Successfully deleted!')
                return redirect(url_for('dashboard'))
            else:
                make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/twitter', status_code=403, status_message='Attempted to delete post from domain {}.'.format(post.domain_id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('dashboard'))
        elif platform == 'tumblr':
            post = TumblrPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/tumblr', status_code=204, status_message='Tumblr post deleted.')
                flash('Successfully deleted!')
                return redirect(url_for('dashboard'))
            else:
                make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/tumblr', status_code=403, status_message='Attempted to delete post from domain {}.'.format(post.domain_id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('dashboard'))
        elif platform == 'reddit':
            post = RedditPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/reddit', status_code=204, status_message='Reddit post deleted.')
                flash('Successfully deleted!')
                return redirect(url_for('dashboard'))
            else:
                make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/reddit', status_code=403, status_message='Attempted to delete post from domain {}.'.format(post.domain_id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('dashboard'))
        elif platform == 'youtube':
            post = YoutubePost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/youtube', status_code=204, status_message='YouTube post deleted.')
                flash('Successfully deleted!')
                return redirect(url_for('dashboard'))
            else:
                make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/youtube', status_code=403, status_message='Attempted to delete post from domain {}.'.format(post.domain_id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('dashboard'))
        elif platform == 'linkedin':
            post = LinkedinPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/linkedin', status_code=204, status_message='LinkedIn post deleted.')
                flash('Successfully deleted!')
                return redirect(url_for('dashboard'))
            else:
                make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/linkedin', status_code=403, status_message='Attempted to delete post from domain {}.'.format(post.domain_id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('dashboard'))
        else:
            make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post/?', status_code=400, status_message='Malformed request; network not found.')
            flash('ERROR: Malformed request; network not found.')
            return redirect(url_for('dashboard'))
    else:
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/delete/post', status_code=403, status_message='Delete permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))

@app.route('/get/image/<filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory(os.path.join(app.instance_path, 'images'), filename, as_attachment=True)

@app.route('/get/video/<filename>', methods=['GET'])
def get_video(filename):
    return send_from_directory(os.path.join(app.instance_path, 'videos'), filename, as_attachment=True)

# API

@app.route('/api/_r/<domain_id>/<platform>/auth=<read_token>', methods=['GET'])
def api_read(domain_id, platform, read_token):
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if str(read_token) == app.config['READ_TOKEN']:
        if str(platform) == 'facebook':
            post = FacebookPost.query.filter_by(domain_id=int(domain_id)).order_by(FacebookPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=200, status_message='Accessed post.')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags), 200
        elif str(platform) == 'twitter':
            post = TwitterPost.query.filter_by(domain_id=int(domain_id)).order_by(TwitterPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=200, status_message='Accessed post.')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags), 200
        elif str(platform) == 'tumblr':
            post = TumblrPost.query.filter_by(domain_id=int(domain_id)).order_by(TumblrPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=200, status_message='Accessed post.')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, title=post.title, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags, caption=post.caption), 200
        elif str(platform) == 'reddit':
            post = RedditPost.query.filter_by(domain_id=int(domain_id)).order_by(RedditPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=200, status_message='Accessed post.')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, title=post.title, body=post.body, link_url=post.link_url, image_url=post.image_url, video_url=post.video_url), 200
        elif str(platform) == 'youtube':
            post = YoutubePost.query.filter_by(domain_id=int(domain_id)).order_by(YoutubePost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=200, status_message='Accessed post.')
                return jsonify(timestamp=post.timestamp, multimedia_url=post.multimedia_url, title=post.title, caption=post.caption, tags=post.tags, category=post.category), 200
        elif str(platform) == 'linkedin':
            post = LinkedinPost.query.filter_by(domain_id=int(domain_id)).order_by(LinkedinPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=200, status_message='Accessed post.')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, title=post.title, body=post.body, caption=post.caption, multimedia_url=post.multimedia_url, link_url=post.link_url, tags=post.tags), 200
        else:
            make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/?'.format(domain_id), status_code=400, status_message='Malformed request; platform not found.')
            return jsonify(endpoint='api/_r', status='400 Bad Request', utc_timestamp=timestamp, ip_address=ip_address, error_details='Malformed request; platform not found.'), 400
    else:
        make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/{}'.format(domain_id, platform), status_code=403, status_message='Incorrect read token: {}'.format(str(read_token)))
        return jsonify(endpoint='api/_r', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403

@app.route('/api/_d/<domain_id>/<platform>/auth=<read_token>&<delete_token>', methods=['GET'])
def api_delete(domain_id, platform, read_token, delete_token):
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if str(read_token) == app.config['READ_TOKEN'] and str(delete_token) == app.config['DELETE_TOKEN']:
        if str(platform) == 'facebook':
            post = FacebookPost.query.filter_by(domain_id=int(domain_id)).order_by(FacebookPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=204, status_message='Post deleted.')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'twitter':
            post = TwitterPost.query.filter_by(domain_id=int(domain_id)).order_by(TwitterPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=204, status_message='Post deleted.')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'tumblr':
            post = TumblrPost.query.filter_by(domain_id=int(domain_id)).order_by(TumblrPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=204, status_message='Post deleted.')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'reddit':
            post = RedditPost.query.filter_by(domain_id=int(domain_id)).order_by(RedditPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=204, status_message='Post deleted.')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'youtube':
            post = YoutubePost.query.filter_by(domain_id=int(domain_id)).order_by(YoutubePost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=204, status_message='Post deleted.')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'linkedin':
            post = LinkedinPost.query.filter_by(domain_id=int(domain_id)).order_by(LinkedinPost.timestamp.asc()).first()
            if post is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=404, status_message='Post not found.')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=204, status_message='Post deleted.')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        else:
            make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/?'.format(domain_id), status_code=400, status_message='Malformed request; platform not found.')
            return jsonify(endpoint='api/_d', status='400 Bad Request', utc_timestamp=timestamp, ip_address=ip_address, error_details='Malformed request; platform not found.'), 400
    else:
        make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_d/{}/{}'.format(domain_id, platform), status_code=403, status_message='{}/{}'.format(str(read_token), str(delete_token)))
        return jsonify(endpoint='api/_d', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403

@app.route('/api/_p/<domain_id>/<platform>/auth=<read_token>&<delete_token>&<permission_token>', methods=['GET'])
def api_permission(domain_id, platform, read_token, delete_token, permission_token):
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if str(read_token) == app.config['READ_TOKEN'] and str(delete_token) == app.config['DELETE_TOKEN'] and str(permission_token) == app.config['PERMISSION_TOKEN']:
        domain = Domain.query.filter_by(id=int(domain_id)).first()
        if str(platform) == 'facebook':
            facebook_token = domain.facebook_token
            if facebook_token is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/facebook'.format(domain_id), status_code=404, status_message='Credential not found.')
                return jsonify(endpoint='/api/_p/facebook', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/facebook'.format(domain_id), status_code=200, status_message='Credential accessed.')
                return jsonify(facebook_token=facebook_token), 200
        elif str(platform) == 'twitter':
            twitter_token = domain.twitter_token
            twitter_secret = domain.twitter_secret
            if twitter_token is None or twitter_secret is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/twitter'.format(domain_id), status_code=404, status_message='Credential not found.')
                return jsonify(endpoint='/api/_p/twitter', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/twitter'.format(domain_id), status_code=200, status_message='Credentials accessed.')
                return jsonify(twitter_token=twitter_token, twitter_secret=twitter_secret), 200
        elif str(platform) == 'tumblr':
            tumblr_blog_name = domain.tumblr_blog_name
            tumblr_token = domain.tumblr_token
            tumblr_secret = domain.tumblr_secret
            if tumblr_blog_name is None or tumblr_token is None or tumblr_secret is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/tumblr'.format(domain_id), status_code=404, status_message='Credential not found.')
                return jsonify(endpoint='/api/_p/tumblr', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/tumblr'.format(domain_id), status_code=200, status_message='Credentials accessed.')
                return jsonify(tumblr_blog_name=tumblr_blog_name, tumblr_token=tumblr_token, tumblr_secret=tumblr_secret), 200
        elif str(platform) == 'reddit':
            reddit_subreddit = domain.reddit_subreddit
            reddit_username = domain.reddit_username
            reddit_password = domain.reddit_password
            if reddit_subreddit is None or reddit_username is None or reddit_password is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/reddit'.format(domain_id), status_code=404, status_message='Credential not found.')
                return jsonify(endpoint='/api/_p/reddit', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/tumblr'.format(domain_id), status_code=200, status_message='Credentials accessed.')
                return jsonify(reddit_subreddit=reddit_subreddit, reddit_username=reddit_username, reddit_password=reddit_password), 200
        elif str(platform) == 'youtube':
            youtube_refresh = domain.youtube_refresh
            youtube_access = domain.youtube_access
            if youtube_refresh is None or youtube_access is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/youtube'.format(domain_id), status_code=404, status_message='Credential not found.')
                return jsonify(endpoint='/api/_p/youtube', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/youtube'.format(domain_id), status_code=200, status_message='Credentials accessed.')
                return jsonify(youtube_refresh=youtube_refresh, youtube_access=youtube_access), 200
        elif str(platform) == 'linkedin':
            linkedin_author = domain.linkedin_author
            linkedin_token = domain.linkedin_token
            linkedin_secret = domain.linkedin_secret
            if linkedin_author is None or linkedin_token is None or linkedin_secret is None:
                make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/linkedin'.format(domain_id), status_code=404, status_message='Credential not found.')
                return jsonify(endpoint='/api/_p/linkedin', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='api/_p/{}/youtube'.format(domain_id), status_code=200, status_message='Credentials accessed.')
                return jsonify(linkedin_author=linkedin_author, linkedin_token=linkedin_token, linkedin_secret=linkedin_secret), 200
        else:
            make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_r/{}/?'.format(domain_id), status_code=400, status_message='Malformed request; platform not found.')
            return jsonify(endpoint='api/_d', status='400 Bad Request', utc_timestamp=timestamp, ip_address=ip_address, error_details='Malformed request; platform not found.'), 400
    else:
        make_ewok(user_id=None, ip_address=request.remote_addr, endpoint='/api/_p/{}/{}'.format(domain_id, platform), status_code=403, status_message='{}/{}/{}'.format(str(read_token), str(delete_token), str(permission_token)))
        return jsonify(endpoint='api/_p', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403

# Help

@app.route('/help')
def help():
    return render_template('help.html', title='Help')

# Sales pathway

@app.route('/create/sale', methods=['GET', 'POST'])
@login_required
def create_sale():
    if current_user.icyfire_crta is None or str(current_user.icyfire_crta).split('-')[3] == '00':
        make_ewok(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/sale', status_code=403, status_message='Permission denied.')
        flash("You don't have permission to do that.")
        return redirect(url_for('dashboard'))
    form = SaleForm()
    if form.validate_on_submit():
        sale = Sale(client_name=str(form.client_name.data))
        sale.agent_id = current_user.id
        sale.client_street_address = str(form.client_street_address.data)
        sale.client_city = str(form.client_city.data)
        sale.client_state = str(form.client_state.data)
        sale.client_country = 'United States'
        sale.client_zip = str(form.client_zip.data)
        sale.client_phone_country = int(1)
        sale.client_phone_number = int(form.client_phone_number.data)
        sale.client_email = str(form.client_email.data)
        sale.unit_price = float(3000)
        sale.quantity = int(form.quantity.data)
        sale.subtotal = sale.quantity * sale.unit_price
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
        sale.sales_tax = sales_tax_dict[str(form.client_state.data)] * sale.subtotal
        sale.total = sale.sales_tax + sale.subtotal
        country, region, team = str(current_user.icyfire_crta).split('-')[0], str(current_user.icyfire_crta).split('-')[1], str(current_user.icyfire_crta).split('-')[2]
        country_lead = CountryLead.query.filter_by(crta_code=country + '-00-00-00').first()
        sale.country_lead_id = country_lead.id
        region_lead = RegionLead.query.filter_by(crta_code=country + '-' + region + '-00-00').first()
        sale.region_lead_id = region_lead.id
        team_lead = TeamLead.query.filter_by(crta_code=country + '-' + region + '-' + team + '-00').first()
        sale.team_lead_id = team_lead.id
        db.session.add(sale)
        db.session.commit()
        make_sentry(user_id=current_user.id, ip_address=request.remote_addr, endpoint='/create/sale', status_code=200, status_message='Sale created.')
        return redirect(url_for('create_invoice', sale_id=sale.id))
    return render_template('create_sale.html', title='New Sale', form=form)

@app.route('/create/invoice/<sale_id>')
def create_invoice(sale_id):
    sale = Sale.query.filter_by(id=sale_id).first()
    agent = Agent.query.filter_by(id=sale.agent_id).first()
    user = User.query.filter_by(id=agent.user_id).first()
    activation_code = str(uuid.uuid4())
    basedir = os.path.abspath(os.path.dirname(__file__))
    data_dict = {
        'invoice_date': sale.timestamp.strftime('%Y-%d-%m'),
        'agent_name': '{} {}'.format(agent.first_name.upper(), agent.last_name.upper()),
        'agent_email': user.email,
        'agent_phone': '+{}-({})-{}-{}'.format(agent.phone_country, str(agent.phone_number)[0:3], str(agent.phone_number)[3:6], str(agent.phone_number)[6:10]),
        'client_name': sale.client_name.upper(),
        'client_street_address': sale.client_street_address.upper(),
        'client_city': sale.client_city.upper(),
        'client_state': sale.client_state.upper(),
        'client_zip_code': sale.client_zip,
        'client_email': sale.client_email,
        'client_phone': '+{}-({})-{}-{}'.format(sale.client_phone_country, str(sale.client_phone_number)[0:3], str(sale.client_phone_number)[3:6], str(sale.client_phone_number)[6:10]),
        'quantity': sale.quantity,
        'unit_price': '${}'.format(float(sale.unit_price)),
        'subtotal': '${}'.format(float(sale.subtotal)),
        'sales_tax': '${}'.format(float(sale.sales_tax)),
        'total_due': '${}'.format(float(sale.total)),
        'activation_code': activation_code
    }
    input_file = os.path.join(basedir, 'app', 'static', 'agreements', 'client_invoice_template.pdf')
    output_file = os.path.join(basedir, 'app', 'static', 'records', 'invoices', '{}.pdf'.format(sale_id))
    fill_pdf_template(input_path=input_file, output_path=output_file, data_dict=data_dict)
    domain = Domain(activation_code=activation_code)
    db.session.add(domain)
    db.session.commit()
    return send_from_directory(os.path.join(basedir, 'app', 'static', 'records', 'invoices'), '{}.pdf'.format(sale_id), as_attachment=True)