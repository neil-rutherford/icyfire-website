from flask import render_template, flash, redirect, url_for, request, send_from_directory
from app import db
from app.models import Sentry, FacebookPost, TwitterPost, TumblrPost, RedditPost, YoutubePost, LinkedinPost
from app.main.forms import ShortTextPostForm, LongTextPostForm, ImagePostForm, VideoPostForm
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
import uuid
from app.main import bp
from datetime import datetime, date

# HELPER FUNCTIONS
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id)
    db.session.add(activity)
    db.session.commit()

def make_facebook(domain_id, user_id, post_type, body, link_url, multimedia_url, tags):
    post = FacebookPost(domain_id=domain_id, user_id=user_id, post_type=post_type, body=body, link_url=link_url, multimedia_url=multimedia_url, tags=tags)
    db.session.add(post)
    db.session.commit()

def make_twitter(domain_id, user_id, post_type, body, link_url, multimedia_url, tags):
    post = TwitterPost(domain_id=domain_id, user_id=user_id, post_type=post_type, body=body, link_url=link_url, multimedia_url=multimedia_url, tags=tags)
    db.session.add(post)
    db.session.commit()

def make_tumblr(domain_id, user_id, post_type, title, body, link_url, multimedia_url, tags, caption):
    post = TumblrPost(domain_id=domain_id, user_id=user_id, post_type=post_type, title=title, body=body, link_url=link_url, multimedia_url=multimedia_url, tags=tags, caption=caption)
    db.session.add(post)
    db.session.commit()

def make_reddit(domain_id, user_id, post_type, title, body, link_url, image_url, video_url):
    post = RedditPost(domain_id=domain_id, user_id=user_id, post_type=post_type, title=title, body=body, link_url=link_url, image_url=image_url, video_url=video_url)
    db.session.add(post)
    db.session.commit()

def make_youtube(domain_id, user_id, multimedia_url, title, caption, tags, category):
    post = YoutubePost(domain_id=domain_id, user_id=user_id, multimedia_url=multimedia_url, title=title, caption=caption, tags=tags, category=category)
    db.session.add(post)
    db.session.commit()

def make_linkedin(domain_id, user_id, post_type, title, body, caption, multimedia_url, link_url, tags):
    post = LinkedinPost(domain_id=domain_id, user_id=user_id, post_type=post_type, title=title, body=body, caption=caption, multimedia_url=multimedia_url, link_url=link_url, tags=tags)
    db.session.add(post)
    db.session.commit()

# USER DASHBOARD
@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    '''
    - Sentry logs:
        + ENDPOINT: 'main.dashboard'
        + 200 = ok; read access for all posts for all platforms registered to that domain
        + 403 = permission denied; user doesn't have read permission
    - If the user is an IcyFire contractor, then they are directed to the sales dashboard
    '''
    if current_user.icyfire_crta is not None:
        return redirect(url_for('sales.dashboard'))
    if current_user.is_read is False:
        flash("Talk to your domain admin about getting read permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.dashboard', status_code=403, status_message='Read permission denied.')
        return redirect(url_for('main.dashboard'))
    facebook_queue = FacebookPost.query.filter_by(domain_id=current_user.domain_id).order_by(FacebookPost.timestamp.asc()).all()
    twitter_queue = TwitterPost.query.filter_by(domain_id=current_user.domain_id).order_by(TwitterPost.timestamp.asc()).all()
    tumblr_queue = TumblrPost.query.filter_by(domain_id=current_user.domain_id).order_by(TumblrPost.timestamp.asc()).all()
    reddit_queue = RedditPost.query.filter_by(domain_id=current_user.domain_id).order_by(RedditPost.timestamp.asc()).all()
    youtube_queue = YoutubePost.query.filter_by(domain_id=current_user.domain_id).order_by(YoutubePost.timestamp.asc()).all()
    linkedin_queue = LinkedinPost.query.filter_by(domain_id=current_user.domain_id).order_by(LinkedinPost.timestamp.asc()).all()
    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.dashboard', status_code=200, status_message='Successful dashboard access.')
    return render_template('main/dashboard.html', facebook_queue=facebook_queue, twitter_queue=twitter_queue, tumblr_queue=tumblr_queue, reddit_queue=reddit_queue, youtube_queue=youtube_queue, linkedin_queue=linkedin_queue)

# CREATE SHORT TEXT POST
@bp.route('/create/short-text', methods=['GET', 'POST'])
@login_required
def create_short_text():
    '''
    - Sentry logs:
        + ENDPOINT: 'main.create_short_text'
        + 200 = ok; post created (`status_message` = platform)
        + 403 = permission denied; user doesn't have create permission
    - Creates post(s) depending on what platform(s) the user selected
    - Increments the `post_count` variable for the user
    - Redirects back to dashboard when finished
    '''
    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))
    form = ShortTextPostForm()
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if form.is_facebook.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Facebook')
        if form.is_twitter.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Twitter')
        if form.is_tumblr.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Tumblr')
        if form.is_reddit.data is True:
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Reddit')
        if form.is_linkedin.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='LinkedIn')
        flash('Successfully queued!')
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_short_text.html', title='New Short Text Post', form=form)

# CREATE LONG TEXT POST
@bp.route('/create/long-text', methods=['GET', 'POST'])
@login_required
def create_long_text():
    '''
    - Sentry logs:
        + ENDPOINT: 'main.create_long_text'
        + 200 = ok; post created successfully (`status_message`=platform)
        + 403 = permission denied; user doesn't have create permission
    - Creates post(s) depending on what platform(s) the user selected
    - Increments the `post_count` variable for the user
    - Redirects back to dashboard when finished
    '''
    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))
    form = LongTextPostForm()
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if form.is_facebook.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Facebook')
        if form.is_tumblr.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Tumblr')
        if form.is_reddit.data is True:
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Reddit')
        if form.is_linkedin.data is True:
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='LinkedIn')
        flash('Successfully queued!')
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_long_text.html', title='New Long Text Post', form=form)

# CREATE PHOTO POST
@bp.route('/create/image', methods=['GET', 'POST'])
@login_required
def create_image():
    '''
    - Sentry logs:
        + ENDPOINT: 'main.create_image'
        + 200 = ok; post created successfully (`status_message`=platform)
        + 403 = permission denied; user doesn't have create permission
    - Creates post(s) depending on what platform(s) the user selected
    - Image saved to: "dirname(__file__)/app/static/assets/images"
    - Image file name format: "{platform}-{uuid}.{file type}" (e.g. "facebook-50m3r4nd0m5tr1ng.jpg)
    - Increments the `post_count` variable for the user
    - Redirects back to dashboard when finished
    '''
    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('dashboard'))
    form = ImagePostForm()
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        basedir = os.path.abspath(os.path.dirname(__file__))
        image_name = str(uuid.uuid4())
        f = form.image.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if form.is_facebook.data is True:
            filename = secure_filename('facebook-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_image', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Facebook')
        if form.is_twitter.data is True:
            filename = secure_filename('twitter-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_image', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Twitter')
        if form.is_tumblr.data is True:
            filename = secure_filename('tumblr-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('main.get_image', filename), tags=tags, caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Tumblr')
        if form.is_reddit.data is True:
            filename = secure_filename('reddit-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=url_for('main.get_image', filename), video_url=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Reddit')
        if form.is_linkedin.data is True:
            filename = secure_filename('linkedin-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('main.get_image', filename), link_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='LinkedIn')
        flash('Successfully queued!')
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_image.html', title='New Image Post', form=form)

# CREATE VIDEO POST
@bp.route('/create/video', methods=['GET', 'POST'])
@login_required
def create_video():
    '''
    - Sentry logs:
        + ENDPOINT: 'main.create_video'
        + 200 = ok; post created successfully (`status_message`=platform)
        + 403 = permission denied; user doesn't have create permission
    - Creates post(s) depending on what platform(s) the user selected
    - Video saved to: "dirname(__file__)/app/static/assets/videos"
    - Video file name format: "{platform}-{uuid}.{file type}" (e.g. "facebook-50m3r4nd0m5tr1ng.mp4)
    - Increments the `post_count` variable for the user
    - Redirects back to dashboard when finished
    '''
    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))
    form = VideoPostForm()
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        basedir = os.path.abspath(os.path.dirname(__file__))
        video_name = str(uuid.uuid4())
        f = form.video.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if form.is_facebook.data is True:
            filename = secure_filename('facebook-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_video', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Facebook')
        if form.is_twitter.data is True:
            filename = secure_filename('twitter-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_video', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Twitter')
        if form.is_tumblr.data is True:
            filename = secure_filename('tumblr-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('main.get_video', filename), tags=tags, caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Tumblr')
        if form.is_reddit.data is True:
            filename = secure_filename('reddit-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=None, video_url=url_for('main.get_video', filename))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Reddit')
        if form.is_youtube.data is True:
            filename = secure_filename('youtube-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_youtube(domain_id=current_user.domain_id, user_id=current_user.id, multimedia_url=url_for('main.get_video', filename), title=str(form.title.data), caption=str(form.caption.data), tags=tagline, category=int(form.category.data))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='YouTube')
        if form.is_linkedin.data is True:
            filename = secure_filename('linkedin-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('main.get_video', filename), link_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='LinkedIn')
        flash('Successfully queued!')
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_video.html', title='New Video Post', form=form)

# UPDATE SHORT TEXT POST
@bp.route('/update/short-text/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_short_text(platform, post_id):
    '''
    - Sentry logs:
        + ENDPOINT: 'main.update_short_text'
        + 403 = permission denied; user doesn't have update permission OR user tried to edit a post in someone else's domain (`status_message` = platform|post_id)
        + 200 = ok; post successfully updated (`status_message` = platform|post_id)
        + 404 = post not found; maybe has been deleted by another user? (`status_message` = platform|post_id)
        + 400 = bad request; platform not found (`status_message`=platform|post_id)
        + If user tries to update another domain's post, `domain_id` is the post's domain so that the targeted domain's admin is notified
    - Loads a pre-populated form so that user can edit an existing post
    - Increments user's `post_counter`
    - Returns to dashboard when finished
    '''
    if current_user.is_update is False:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=403, status_message='Update permission denied.')
        flash("Talk to your domain admin about getting update permissions.")
        return redirect(url_for('main.dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=404, status_message='Facebook|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=404, status_message='Twitter|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=404, status_message='Tumblr|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=404, status_message='Reddit|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=404, status_message='LinkedIn|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))
    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))
    form = ShortTextPostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if platform == 'facebook':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'twitter':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Twitter|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'tumblr':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'reddit':
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'linkedin':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='LinkedIn|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
    return render_template('main/update_short_text.html', title='Update Short Text Post', form=form)

# UPDATE LONG TEXT POST
@bp.route('/update/long-text/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_long_text(platform, post_id):
    '''
    - Sentry logs:
        + ENDPOINT: 'main.update_long_text'
        + 403 = permission denied; user doesn't have update permission OR user tried to edit a post in someone else's domain (`status_message` = platform|post_id)
        + 200 = ok; post successfully updated (`status_message` = platform|post_id)
        + 404 = post not found; maybe has been deleted by another user? (`status_message` = platform|post_id)
        + 400 = bad request; platform not found (`status_message`=platform|post_id)
        + If user tries to update another domain's post, `domain_id` is the post's domain so that the targeted domain's admin is notified
    - Loads a pre-populated form so that user can edit an existing post
    - Increments the `post_count` variable for the user
    - Redirects back to dashboard when finished
    '''
    if current_user.is_update is False:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=403, status_message='Update permission denied.')
        flash("Talk to your domain admin about getting update permissions.")
        return redirect(url_for('main.dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=404, status_message='Facebook|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=404, status_message='Tumblr|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=404, status_message='Reddit|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=404, status_message='LinkedIn|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))
    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))
    form = LongTextPostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        if platform == 'facebook':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'tumblr':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'reddit':
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'linkedin':
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), caption=None, multimedia_url=None, link_url=str(form.link_url.data), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='LinkedIn|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
    return render_template('main/update_long_text.html', title='Update Long Text Post', form=form)

# UPDATE IMAGE POST
@bp.route('/update/image/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_image(platform, post_id):
    '''
    - Sentry logs:
        + ENDPOINT: 'main.update_image'
        + 403 = permission denied; user doesn't have update permission OR user tried to edit a post in someone else's domain (`status_message` = platform|post_id)
        + 200 = ok; post successfully updated (`status_message` = platform|post_id)
        + 404 = post not found; maybe has been deleted by another user? (`status_message` = platform|post_id)
        + 400 = bad request; platform not found (`status_message`=platform|post_id)
        + If user tries to update another domain's post, `domain_id` is the post's domain so that the targeted domain's admin is notified
    - Loads a pre-populated form so that user can edit an existing post
    - Image saved to: "dirname(__file__)/app/static/assets/images"
    - Image file name format: "{platform}-{uuid}.{file type}" (e.g. "facebook-50m3r4nd0m5tr1ng.jpg)
    - Increments the `post_count` variable for the user
    - Redirects back to dashboard when finished
    '''
    if current_user.is_update is False:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=403, status_message='Update permission denied.')
        flash("Talk to your domain admin about getting update permissions.")
        return redirect(url_for('main.dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='Facebook|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='Twitter|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='Tumblr|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='Reddit|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='LinkedIn|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))
    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))
    form = ImagePostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        basedir = os.path.abspath(os.path.dirname(__file__))
        image_name = str(uuid.uuid4())
        f = form.image.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if platform == 'facebook':
            filename = secure_filename('facebook-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_image', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'twitter':
            filename = secure_filename('twitter-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_image', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Twitter|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'tumblr':
            filename = secure_filename('tumblr-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('main.get_image', filename), tags=tags, caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'reddit':
            filename = secure_filename('reddit-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=url_for('main.get_image', filename), video_url=None)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'linkedin':
            filename = secure_filename('linkedin-{}.{}'.format(image_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'images', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('main.get_image', filename), link_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='LinkedIn|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
    return render_template('main/update_image.html', title='Update Image Post', form=form)

# UPDATE VIDEO POST
@bp.route('/update/video/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_video(platform, post_id):
    '''
    - Sentry logs:
        + ENDPOINT: 'main.update_video'
        + 403 = permission denied; user doesn't have update permission OR user tried to edit a post in someone else's domain (`status_message` = platform|post_id)
        + 200 = ok; post successfully updated (`status_message` = platform|post_id)
        + 404 = post not found; maybe has been deleted by another user? (`status_message` = platform|post_id)
        + 400 = bad request; platform not found (`status_message`=platform|post_id)
        + If user tries to update another domain's post, `domain_id` is the post's domain so that the targeted domain's admin is notified
    - Loads a pre-populated form so that user can edit an existing post
    - Video saved to: "dirname(__file__)/app/static/assets/videos"
    - Video file name format: "{platform}-{uuid}.{file type}" (e.g. "facebook-50m3r4nd0m5tr1ng.mp4)
    - Increments the `post_count` variable for the user
    - Redirects back to dashboard when finished
    '''
    if current_user.is_update is False:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=403, status_message='Update permission denied.')
        flash("Talk to your domain admin about getting update permissions.")
        return redirect(url_for('main.dashboard'))
    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='Facebook|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='Twitter|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='Tumblr|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='Reddit|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'youtube':
        post = YoutubePost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='YouTube|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    elif platform == 'linkedin':
        post = LinkedinPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='LinkedIn|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))
    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))
    form = VideoPostForm(obj=post)
    if form.validate_on_submit():
        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()
        basedir = os.path.abspath(os.path.dirname(__file__))
        video_name = str(uuid.uuid4())
        f = form.video.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        if platform == 'facebook':
            filename = secure_filename('facebook-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_facebook(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_video', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'twitter':
            filename = secure_filename('twitter-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_twitter(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=url_for('main.get_video', filename), tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Twitter|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'tumblr':
            filename = secure_filename('tumblr-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
            else:
                tags = None
            make_tumblr(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, link_url=None, multimedia_url=url_for('main.get_video', filename), tags=tags, caption=str(form.caption.data))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'reddit':
            filename = secure_filename('reddit-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            make_reddit(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=None, video_url=url_for('main.get_video', filename))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'youtube':
            filename = secure_filename('youtube-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_youtube(domain_id=current_user.domain_id, user_id=current_user.id, multimedia_url=url_for('main.get_video', filename), title=str(form.title.data), caption=str(form.caption.data), tags=tagline, category=int(form.category.data))
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='YouTube|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
        elif platform == 'linkedin':
            filename = secure_filename('linkedin-{}.{}'.format(video_name, file_type))
            f.save(os.path.join(basedir, 'app', 'static', 'assets', 'videos', filename))
            if form.tags.data is not None:
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                tagline = '#' + tagline
            else:
                tagline = None
            make_linkedin(domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, caption=str(form.caption.data), multimedia_url=url_for('main.get_video', filename), link_url=None, tags=tagline)
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='LinkedIn|{}'.format(int(post_id)))
            flash('Successfully edited!')
            return redirect(url_for('main.dashboard'))
    return render_template('main/update_video.html', title='Update Video Post', form=form)

# DELETE POST
@bp.route('/delete/post/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(platform, post_id):
    '''
    - Sentry logs:
        + ENDPOINT: 'main.delete_post'
        + 403 = permission denied; user doesn't have delete permission OR user tried to delete a post in someone else's domain (`status_message` = platform|post_id)
        + 204 = no content; post successfully deleted (`status_message` = platform|post_id)
        + 400 = bad request; platform not found (`status_message`=platform|post_id)
        + If user tries to delete another domain's post, `domain_id` is the post's domain so that the targeted domain's admin is notified
    - Uses platform and post_id to find post and delete it
    '''
    if current_user.is_delete is True:
        if platform == 'facebook':
            post = FacebookPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Facebook|{}'.format(int(post_id)))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Facebook|{}'.format(int(post_id)))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))
        elif platform == 'twitter':
            post = TwitterPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Twitter|{}'.format(int(post_id)))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Twitter|{}'.format(int(post_id)))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))
        elif platform == 'tumblr':
            post = TumblrPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Tumblr|{}'.format(int(post_id)))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Tumblr|{}'.format(int(post_id)))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))
        elif platform == 'reddit':
            post = RedditPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Reddit|{}'.format(int(post_id)))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Reddit|{}'.format(int(post_id)))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))
        elif platform == 'youtube':
            post = YoutubePost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='YouTube|{}'.format(int(post_id)))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='YouTube|{}'.format(int(post_id)))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))
        elif platform == 'linkedin':
            post = LinkedinPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='LinkedIn|{}'.format(int(post_id)))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='LinkedIn|{}'.format(int(post_id)))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))
        else:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
            flash('ERROR: Malformed request; platform not found.')
            return redirect(url_for('main.dashboard'))
    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Delete permission denied.')
        flash("Talk to your domain admin about getting delete permissions.")
        return redirect(url_for('main.dashboard'))

# DOWNLOAD IMAGE
@bp.route('/get/image/<filename>', methods=['GET'])
def get_image(filename):
    basedir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(os.path.join(basedir, 'app', 'static', 'assets', 'images'), filename, as_attachment=True)

# DOWNLOAD VIDEO
@bp.route('/get/video/<filename>', methods=['GET'])
def get_video(filename):
    basedir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(os.path.join(basedir, 'app', 'static', 'assets', 'videos'), filename, as_attachment=True)

# HELP
@bp.route('/help')
def help():
    return render_template('main/help.html', title='Help')