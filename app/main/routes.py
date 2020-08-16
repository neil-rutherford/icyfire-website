from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app
from app import db
from app.models import Sentry, FacebookPost, TwitterPost, TumblrPost, RedditPost, FacebookCred, TwitterCred, TumblrCred, RedditCred, Domain, TimeSlot
from app.main.forms import ShortTextForm, LongTextForm, ImageForm, VideoForm, EditImageForm, EditVideoForm, TestForm
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
import uuid
import json
from app.main import bp
from datetime import datetime, date
import markdown
import markdown.extensions.fenced_code
from app.main.transfer import TransferData
from dotenv import load_dotenv
import dropbox

load_dotenv('.env')

# HELPER FUNCTIONS
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

def make_facebook(cred_id, domain_id, user_id, post_type, body, link_url, multimedia_url, tags):
    post = FacebookPost(cred_id=cred_id, domain_id=domain_id, user_id=user_id, post_type=post_type, body=body, link_url=link_url, multimedia_url=multimedia_url, tags=tags)
    db.session.add(post)
    db.session.commit()

def make_twitter(cred_id, domain_id, user_id, post_type, body, link_url, multimedia_url, tags):
    post = TwitterPost(cred_id=cred_id, domain_id=domain_id, user_id=user_id, post_type=post_type, body=body, link_url=link_url, multimedia_url=multimedia_url, tags=tags)
    db.session.add(post)
    db.session.commit()

def make_tumblr(cred_id, domain_id, user_id, post_type, title, body, link_url, multimedia_url, tags, caption):
    post = TumblrPost(cred_id=cred_id, domain_id=domain_id, user_id=user_id, post_type=post_type, title=title, body=body, link_url=link_url, multimedia_url=multimedia_url, tags=tags, caption=caption)
    db.session.add(post)
    db.session.commit()

def make_reddit(cred_id, domain_id, user_id, post_type, title, body, link_url, image_url, video_url):
    post = RedditPost(cred_id=cred_id, domain_id=domain_id, user_id=user_id, post_type=post_type, title=title, body=body, link_url=link_url, image_url=image_url, video_url=video_url)
    db.session.add(post)
    db.session.commit()

# Works, 2020-08-15
@bp.route('/download-multimedia/<file_name>')
def download_multimedia(file_name):
    if not os.path.exists('./app/static/resources/{}'.format(file_name)):
        dbx = dropbox.Dropbox(os.environ['DROPBOX_ACCESS_KEY'])
        with open(f"./app/static/resources/{file_name}", 'wb') as f:
            metadata, res = dbx.files_download(path='/multimedia/{}'.format(file_name))
            f.write(res.content)
    return send_from_directory('static/resources', "{}".format(file_name))

# Works, 2020-08-15
def delete_multimedia(file_name):
    if os.path.exists('./app/static/resources/{}'.format(file_name)):
        os.remove('./app/static/resources/{}'.format(file_name))
    dbx = dropbox.Dropbox(os.environ['DROPBOX_ACCESS_KEY'])
    dbx.files_delete_v2(path='/multimedia/{}'.format(file_name))

# Works, 2020-08-14
# DASHBOARD
@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():

    if current_user.icyfire_crta is not None:
        return redirect(url_for('sales.dashboard'))
    
    if current_user.is_read is False:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.dashboard', status_code=403, status_message='Read permission denied.')
        return render_template('main/dashboard_defense.html', title="Insufficient permissions")

    domain = Domain.query.filter_by(id=current_user.domain_id).first()

    facebook_creds = FacebookCred.query.filter_by(domain_id=domain.id).all()
    twitter_creds = TwitterCred.query.filter_by(domain_id=domain.id).all()
    tumblr_creds = TumblrCred.query.filter_by(domain_id=domain.id).all()
    reddit_creds = RedditCred.query.filter_by(domain_id=domain.id).all()

    facebook_posts = FacebookPost.query.filter_by(domain_id=domain.id).order_by(FacebookPost.timestamp.asc()).all()
    twitter_posts = TwitterPost.query.filter_by(domain_id=domain.id).order_by(TwitterPost.timestamp.asc()).all()
    tumblr_posts = TumblrPost.query.filter_by(domain_id=domain.id).order_by(TumblrPost.timestamp.asc()).all()
    reddit_posts = RedditPost.query.filter_by(domain_id=domain.id).order_by(RedditPost.timestamp.asc()).all()

    facebook_times = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.facebook_cred_id != None).all()
    twitter_times = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.twitter_cred_id != None).all()
    tumblr_times = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.tumblr_cred_id != None).all()
    reddit_times = TimeSlot.query.filter(TimeSlot.domain_id == domain.id, TimeSlot.reddit_cred_id != None).all()

    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.dashboard', status_code=200, status_message='Successful dashboard access.')

    return render_template('main/dashboard.html', title='Dashboard', facebook_creds=facebook_creds, facebook_posts=facebook_posts, facebook_times=facebook_times, twitter_creds=twitter_creds, twitter_posts=twitter_posts, twitter_times=twitter_times, tumblr_creds=tumblr_creds, tumblr_posts=tumblr_posts, tumblr_times=tumblr_times, reddit_creds=reddit_creds, reddit_posts=reddit_posts, reddit_times=reddit_times)

@bp.route('/view/post/<platform>/<post_id>')
@login_required
def view_post(platform, post_id):

    if current_user.is_read is False:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.view_post', status_code=403, status_message='Read permission denied.')
        return render_template('main/dashboard_defense.html', title="Insufficient permissions")

    if platform == 'facebook':
        post = FacebookPost.query.filter_by(id=post_id).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.view_post', status_code=404, status_message='Facebook|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))

    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=post_id).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.view_post', status_code=404, status_message='Twitter|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))

    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=post_id).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.view_post', status_code=404, status_message='Tumblr|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))

    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=post_id).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.view_post', status_code=404, status_message='Reddit|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.view_post', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))

    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.view_post', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))
    
    return render_template('main/view_post.html', title='View Post', post=post, platform=platform, post_id=post_id)

# Works, 2020-08-15
# CHOOSE QUEUES
@bp.route('/pre/<post_type>/choose-queues', methods=['GET', 'POST'])
@login_required
def choose_queues(post_type):
        
    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
    twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
    tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
    reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

    if post_type == 'short_text':
        if request.method == 'POST':
            queue_list = []
            for x in request.form:
                queue_list.append(x)
            if len(queue_list) == 0:
                flash("ERROR: Please select at least one queue.")
                return redirect(url_for('main.choose_queues', post_type='short_text'))
            queue_list = '/'.join(queue_list)
            return redirect(url_for('main.create_short_text', queue_list=queue_list))
        return render_template('main/landing_short_text.html', title='Choose your queues', facebook_creds=facebook_creds, twitter_creds=twitter_creds, tumblr_creds=tumblr_creds, reddit_creds=reddit_creds)
    
    elif post_type == 'long_text':
        if request.method == 'POST':
            queue_list = []
            for x in request.form:
                queue_list.append(x)
            if len(queue_list) == 0:
                flash("ERROR: Please select at least one queue.")
                return redirect(url_for('main.choose_queues', post_type='long_text'))
            queue_list = '/'.join(queue_list)
            return redirect(url_for('main.create_long_text', queue_list=queue_list))
        return render_template('main/landing_long_text.html', title='Choose your queues', facebook_creds=facebook_creds, twitter_creds=twitter_creds, tumblr_creds=tumblr_creds, reddit_creds=reddit_creds)
    
    elif post_type == 'image':
        if request.method == 'POST':
            queue_list = []
            for x in request.form:
                queue_list.append(x)
            if len(queue_list) == 0:
                flash("ERROR: Please select at least one queue.")
                return redirect(url_for('main.choose_queues', post_type='image'))
            queue_list = '/'.join(queue_list)
            return redirect(url_for('main.create_image', queue_list=queue_list))
        return render_template('main/landing_image.html', title='Choose your queues', facebook_creds=facebook_creds, twitter_creds=twitter_creds, tumblr_creds=tumblr_creds, reddit_creds=reddit_creds)
    
    elif post_type == 'video':
        if request.method == 'POST':
            queue_list = []
            for x in request.form:
                queue_list.append(x)
            if len(queue_list) == 0:
                flash("ERROR: Please select at least one queue.")
                return redirect(url_for('main.choose_queues', post_type='video'))
            queue_list = '/'.join(queue_list)
            return redirect(url_for('main.create_video', queue_list=queue_list))
        return render_template('main/landing_video.html', title='Choose your queues', facebook_creds=facebook_creds, twitter_creds=twitter_creds, tumblr_creds=tumblr_creds, reddit_creds=reddit_creds)
    
    else:
        flash("ERROR: That post type doesn't exist. Make sure your post type is one of the following: 'short_text', 'long_text', 'image', or 'video'.")
        return redirect(url_for('main.dashboard'))

# Works, 2020-08-15
# CREATE SHORT TEXT
@bp.route('/create/short-text/<path:queue_list>', methods=['GET', 'POST'])
@login_required
def create_short_text(queue_list):

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    facebook_creds = []
    twitter_creds = []
    tumblr_creds = []
    reddit_creds = []

    queue_list = queue_list.split('/')

    for x in queue_list:
        var = str(x).split('_')
        if var[0] == 'facebook':
            facebook_creds.append(FacebookCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'twitter':
            twitter_creds.append(TwitterCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'tumblr':
            tumblr_creds.append(TumblrCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'reddit':
            reddit_creds.append(RedditCred.query.filter_by(id=int(var[1])).first())

    form = ShortTextForm()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        if len(facebook_creds) != 0:
            for x in facebook_creds:
                post = FacebookPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 1
                post.body = form.body.data
                post.multimedia_url = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    tags = str(form.tags.data).split(', ')
                    tagline = ' #'.join(tags)
                    post.tags = '#' + tagline
                else:
                    post.tags = None
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Facebook|{}|{}'.format(x.id, post.id), flag=False)
            
        if len(twitter_creds) != 0:
            for x in twitter_creds:
                post = TwitterPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 1
                post.body = form.body.data
                post.multimedia_url = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    tags = str(form.tags.data).split(', ')
                    tagline = ' #'.join(tags)
                    post.tags = '#' + tagline
                else:
                    post.tags = None
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Twitter|{}|{}'.format(x.id, post.id), flag=False)

        if len(tumblr_creds) != 0:
            for x in tumblr_creds:
                post = TumblrPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 1
                post.title = form.title.data
                post.body = form.body.data
                post.multimedia_url = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    post.tags = str(form.tags.data).split(', ')
                else:
                    post.tags = None
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Tumblr|{}|{}'.format(x.id, post.id), flag=False)
        
        if len(reddit_creds) != 0:
            for x in reddit_creds:
                post = RedditPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 1
                post.title = form.title.data
                post.body = form.body.data
                post.image_url = None
                post.video_url = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Reddit|{}|{}'.format(x.id, post.id), flag=False)

        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_short_text.html', title='New short text post', form=form, queues=len(queue_list))

# Works, 2020-08-15
# CREATE LONG TEXT
@bp.route('/create/long-text/<path:queue_list>', methods=['GET', 'POST'])
@login_required
def create_long_text(queue_list):

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    facebook_creds = []
    twitter_creds = []
    tumblr_creds = []
    reddit_creds = []

    queue_list = queue_list.split('/')

    for x in queue_list:
        var = str(x).split('_')
        if var[0] == 'facebook':
            facebook_creds.append(FacebookCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'twitter':
            twitter_creds.append(TwitterCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'tumblr':
            tumblr_creds.append(TumblrCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'reddit':
            reddit_creds.append(RedditCred.query.filter_by(id=int(var[1])).first())
    
    form = LongTextForm()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        if len(facebook_creds) != 0:
            for x in facebook_creds:
                post = FacebookPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 2
                post.body = form.body.data
                post.multimedia_url = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    tags = str(form.tags.data).split(', ')
                    tagline = ' #'.join(tags)
                    post.tags = '#' + tagline
                else:
                    post.tags = None
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Facebook|{}|{}'.format(x.id, post.id))

        if len(tumblr_creds) != 0:
            for x in tumblr_creds:
                post = TumblrPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 2
                post.title = form.title.data
                post.body = form.body.data
                post.multimedia_url = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    post.tags = str(form.tags.data).split(', ')
                else:
                    post.tags = None
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Tumblr|{}|{}'.format(x.id, post.id))
        
        if len(reddit_creds) != 0:
            for x in reddit_creds:
                post = RedditPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 2
                post.title = form.title.data
                post.body = form.body.data
                post.image_url = None
                post.video_url = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Reddit|{}|{}'.format(x.id, post.id))

        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_long_text.html', title='New long text post', form=form, queues=len(queue_list))

# Works, 2020-08-15
# CREATE IMAGE POST
@bp.route('/create/image/<path:queue_list>', methods=['GET', 'POST'])
@login_required
def create_image(queue_list):

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    facebook_creds = []
    twitter_creds = []
    tumblr_creds = []
    reddit_creds = []

    queue_list = queue_list.split('/')

    for x in queue_list:
        var = str(x).split('_')
        if var[0] == 'facebook':
            facebook_creds.append(FacebookCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'twitter':
            twitter_creds.append(TwitterCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'tumblr':
            tumblr_creds.append(TumblrCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'reddit':
            reddit_creds.append(RedditCred.query.filter_by(id=int(var[1])).first())

    form = ImageForm()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        f = form.image.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x

        if len(facebook_creds) != 0:
            for x in facebook_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = FacebookPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 3
                if form.caption.data != '':
                    post.caption = form.caption.data
                    post.body = None
                else:
                    post.caption = None
                    post.body = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    tags = str(form.tags.data).split(', ')
                    tagline = ' #'.join(tags)
                    post.tags = '#' + tagline
                else:
                    post.tags = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                os.remove('./app/static/resources/{}'.format(file_name))
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Facebook|{}|{}'.format(x.id, post.id))
        
        if len(twitter_creds) != 0:
            for x in twitter_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = TwitterPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 3
                if form.caption.data != '':
                    post.caption = form.caption.data
                    post.body = None
                else:
                    post.caption = None
                    post.body = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    tags = str(form.tags.data).split(', ')
                    tagline = ' #'.join(tags)
                    post.tags = '#' + tagline
                else:
                    post.tags = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Twitter|{}|{}'.format(x.id, post.id))

        if len(tumblr_creds) != 0:
            for x in tumblr_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = TumblrPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 3
                post.title = form.title.data
                post.body = None
                if form.caption.data != '':
                    post.caption = form.caption.data
                else:
                    post.caption = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    post.tags = str(form.tags.data).split(', ')
                else:
                    post.tags = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Tumblr|{}|{}'.format(x.id, post.id))

        if len(reddit_creds) != 0:
            for x in reddit_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = RedditPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 3
                post.title = form.title.data
                if form.caption.data != '':
                    post.body = None
                    post.caption = form.caption.data
                else:
                    post.body = None
                    post.caption = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.image_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Reddit|{}|{}'.format(x.id, post.id))
        
        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/create_image.html', title='New Image Post', form=form, queues=len(queue_list))

# Works, 2020-08-15
# CREATE VIDEO POST
@bp.route('/create/video/<path:queue_list>', methods=['GET', 'POST'])
@login_required
def create_video(queue_list):

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    facebook_creds = []
    twitter_creds = []
    tumblr_creds = []
    reddit_creds = []

    queue_list = queue_list.split('/')

    for x in queue_list:
        var = str(x).split('_')
        if var[0] == 'facebook':
            facebook_creds.append(FacebookCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'twitter':
            twitter_creds.append(TwitterCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'tumblr':
            tumblr_creds.append(TumblrCred.query.filter_by(id=int(var[1])).first())
        elif var[0] == 'reddit':
            reddit_creds.append(RedditCred.query.filter_by(id=int(var[1])).first())

    form = VideoForm()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        f = form.video.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x

        if len(facebook_creds) != 0:
            for x in facebook_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = FacebookPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 4
                if form.caption.data != '':
                    post.body = None
                    post.caption = form.caption.data
                else:
                    post.body = None
                    post.caption = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    tags = str(form.tags.data).split(', ')
                    tagline = ' #'.join(tags)
                    post.tags = '#' + tagline
                else:
                    post.tags = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Facebook|{}|{}'.format(x.id, post.id))

        if len(twitter_creds) != 0:
            for x in twitter_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = TwitterPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 4
                if form.caption.data != '':
                    post.caption = form.caption.data
                    post.body = None
                else:
                    post.body = None
                    post.caption = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    tags = str(form.tags.data).split(', ')
                    tagline = ' #'.join(tags)
                    post.tags = '#' + tagline
                else:
                    post.tags = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Twitter|{}|{}'.format(x.id, post.id))

        if len(tumblr_creds) != 0:
            for x in tumblr_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = TumblrPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 4
                post.title = form.title.data
                post.body = None
                if form.caption.data != '':
                    post.caption = form.caption.data
                else:
                    post.caption = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                if form.tags.data != '':
                    post.tags = str(form.tags.data).split(', ')
                else:
                    post.tags = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Tumblr|{}|{}'.format(x.id, post.id))

        if len(reddit_creds) != 0:
            for x in reddit_creds:
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                post = RedditPost(domain_id=current_user.domain_id)
                post.cred_id = x.id
                post.user_id = current_user.id
                post.post_type = 4
                post.title = form.title.data
                if form.caption.data != '':
                    post.caption = form.caption.data
                    post.body = None
                else:
                    post.body = None
                    post.caption = None
                if form.link_url.data != '':
                    post.link_url = form.link_url.data
                else:
                    post.link_url = None
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.video_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
                db.session.add(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Reddit|{}|{}'.format(x.id, post.id))
        
        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/create_video.html', title='New Video Post', form=form, queues=len(queue_list))

# Works, 2020-08-15
# UPDATE SHORT TEXT
@bp.route('/update/short-text/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_short_text(platform, post_id):

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

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))

    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))

    form = ShortTextForm(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        if platform == 'facebook':
            post.user_id = current_user.id
            post.body = form.body.data
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                post.tags = '#' + tagline
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Facebook|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'twitter':
            post.user_id = current_user.id
            post.body = form.body.data
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                post.tags = '#' + tagline
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Twitter|{}|{}'.format(post.cred_id, post.id))
        
        elif platform == 'tumblr':
            post.user_id = current_user.id
            post.title = form.title.data
            post.body = form.body.data
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                post.tags = str(form.tags.data).split(', ')
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Tumblr|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'reddit':
            post.user_id = current_user.id
            post.title = form.title.data
            post.body = form.body.data
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Reddit|{}|{}'.format(post.cred_id, post.id))

        flash('Successfully updated!')
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_short_text.html', title='Update Short Text Post', form=form)

# Works, 2020-08-15
# UPDATE LONG POST
@bp.route('/update/long-text/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_long_text(platform, post_id):

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

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))

    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))

    form = LongTextForm(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        if platform == 'facebook':
            post.user_id = current_user.id
            post.body = form.body.data
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                post.tags = '#' + tagline
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Facebook|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'tumblr':
            post.user_id = current_user.id
            post.title = form.title.data
            post.body = form.body.data
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                post.tags = str(form.tags.data).split(', ')
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Tumblr|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'reddit':
            post.user_id = current_user.id
            post.title = form.title.data
            post.body = form.body.data
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Reddit|{}|{}'.format(post.cred_id, post.id))

        flash("Successfully updated!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_long_text.html', title='Update Long Text Post', form=form)

# Works, 2020-08-15
# UPDATE IMAGE
@bp.route('/update/image/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_image(platform, post_id):

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
        else:
            image_url = post.multimedia_url

    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='Twitter|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
        else:
            image_url = post.multimedia_url

    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='Tumblr|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
        else:
            image_url = post.multimedia_url

    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=404, status_message='Reddit|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
        else:
            image_url = post.image_url

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))

    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))

    form = EditImageForm(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        f = form.image.data
        if f.filename != '':
            file_list = str(f.filename).split('.')[-1:]
            for x in file_list:
                file_type = x
        else:
            f = None

        if platform == 'facebook':
            if f is not None:
                file_name = str(image_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            if form.caption.data != '':
                post.caption = form.caption.data
                post.body = None
            else:
                post.caption = None
                post.body = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                post.tags = '#' + tagline
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Facebook|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'twitter':
            if f is not None:
                file_name = str(image_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            if form.caption.data != '':
                post.caption = form.caption.data
                post.body = None
            else:
                post.caption = None
                post.body = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                post.tags = '#' + tagline
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Twitter|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'tumblr':
            if f is not None:
                file_name = str(image_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            post.title = form.title.data
            post.body = None
            if form.caption.data != '':
                post.caption = form.caption.data
            else:
                post.caption = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                post.tags = str(form.tags.data).split(', ')
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Tumblr|{}|{}'.format(post.cred_id, post.id))
        
        elif platform == 'reddit':
            if f is not None:
                file_name = str(image_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.image_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            post.title = form.title.data
            if form.caption.data != '':
                post.body = None
                post.caption = form.caption.data
            else:
                post.body = None
                post.caption = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Reddit|{}|{}'.format(post.cred_id, post.id))
        
        flash("Successfully updated!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_image.html', title='Update Image Post', form=form, image_url=image_url)

# Should work...
# UPDATE VIDEO POST
@bp.route('/update/video/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def update_video(platform, post_id):

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
        else:
            video_url = post.multimedia_url

    elif platform == 'twitter':
        post = TwitterPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='Twitter|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
        else:
            video_url = post.multimedia_url

    elif platform == 'tumblr':
        post = TumblrPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='Tumblr|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
        else:
            video_url = post.multimedia_url

    elif platform == 'reddit':
        post = RedditPost.query.filter_by(id=int(post_id)).first()
        if post is None:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=404, status_message='Reddit|{}'.format(int(post_id)))
            flash("ERROR: Post not found. Are you sure it hasn't already been deleted?")
            return redirect(url_for('main.dashboard'))
        else:
            video_url = post.video_url

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))

    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))

    form = EditVideoForm(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        f = form.video.data
        if f.filename != '':
            file_list = str(f.filename).split('.')[-1:]
            for x in file_list:
                file_type = x
        else:
            f = None

        if platform == 'facebook':
            if f is not None:
                file_name = str(video_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            if form.caption.data != '':
                post.caption = form.caption.data
                post.body = None
            else:
                post.caption = None
                post.body = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                post.tags = '#' + tagline
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Facebook|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'twitter':
            if f is not None:
                file_name = str(video_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            if form.caption.data != '':
                post.caption = form.caption.data
                post.body = None
            else:
                post.caption = None
                post.body = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                tags = str(form.tags.data).split(', ')
                tagline = ' #'.join(tags)
                post.tags = '#' + tagline
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Twitter|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'tumblr':
            if f is not None:
                file_name = str(video_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.multimedia_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            post.title = form.title.data
            post.body = None
            if form.caption.data != '':
                post.caption = form.caption.data
            else:
                post.caption = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            if form.tags.data != '':
                post.tags = str(form.tags.data).split(', ')
            else:
                post.tags = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Tumblr|{}|{}'.format(post.cred_id, post.id))

        elif platform == 'reddit':
            if f is not None:
                file_name = str(video_url).split('/')[-1:]
                for x in file_name:
                    file_name = x
                delete_multimedia(file_name)
                file_name = str(uuid.uuid4()) + '.' + file_type
                f.save(f'./app/static/resources/{file_name}')
                transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
                file_from = './app/static/resources/{}'.format(file_name)
                file_to = '/multimedia/{}'.format(file_name)
                transfer_data.upload_file(file_from, file_to)
                post.video_url = url_for('main.download_multimedia', file_name=file_name)
                os.remove('./app/static/resources/{}'.format(file_name))
            post.user_id = current_user.id
            post.title = form.title.data
            if form.caption.data != '':
                post.body = None
                post.caption = form.caption.data
            else:
                post.body = None
                post.caption = None
            if form.link_url.data != '':
                post.link_url = form.link_url.data
            else:
                post.link_url = None
            db.session.add(post)
            db.session.commit()
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Reddit|{}|{}'.format(post.cred_id, post.id))
        
        flash("Successfully updated!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_video.html', title='Update Video Post', form=form)

# Should work...
# DELETE POST
@bp.route('/delete/post/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(platform, post_id):

    if current_user.is_delete is True:

        if platform == 'facebook':
            post = FacebookPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                if post.multimedia_url is not None:
                    file_name = str(post.multimedia_url).split('/')[-1:]
                    for x in file_name:
                        file_name = x
                    delete_multimedia(file_name)
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Facebook|{}|{}'.format(post.cred_id, post.id))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Facebook|{}|{}'.format(post.cred_id, post.id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))

        elif platform == 'twitter':
            post = TwitterPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                if post.multimedia_url is not None:
                    file_name = str(post.multimedia_url).split('/')[-1:]
                    for x in file_name:
                        file_name = x
                    delete_multimedia(file_name)
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Twitter|{}|{}'.format(post.cred_id, post.id))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Twitter|{}|{}'.format(post.cred_id, post.id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))

        elif platform == 'tumblr':
            post = TumblrPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                if post.multimedia_url is not None:
                    file_name = str(post.multimedia_url).split('/')[-1:]
                    for x in file_name:
                        file_name = x
                    delete_multimedia(file_name)
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Tumblr|{}|{}'.format(post.cred_id, post.id))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Tumblr|{}|{}'.format(post.cred_id, post.id))
                flash("ERROR: That post doesn't belong to your domain.")
                return redirect(url_for('main.dashboard'))

        elif platform == 'reddit':
            post = RedditPost.query.filter_by(id=int(post_id)).first()
            if post.domain_id == current_user.domain_id:
                if post.image_url is not None:
                    file_name = str(post.image_url).split('/')[-1:]
                    for x in file_name:
                        file_name = x
                    delete_multimedia(file_name)
                if post.video_url is not None:
                    file_name = str(post.video_url).split('/')[-1:]
                    for x in file_name:
                        file_name = x
                    delete_multimedia(file_name)
                db.session.delete(post)
                db.session.commit()
                make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=204, status_message='Reddit|{}|{}'.format(post.cred_id, post.id))
                flash('Successfully deleted!')
                return redirect(url_for('main.dashboard'))
            else:
                make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Reddit|{}|{}'.format(post.cred_id, post.id))
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

# Works, 2020-08-15
# HELP
@bp.route('/help')
def help():
    return render_template('help/help.html', title='Help Topics')

# Works, 2020-08-15
@bp.route('/help/<topic>')
def help_topic(topic):
    try:
        with open("./docs/{}.md".format(topic), "r") as help_file:
            md_template_string = markdown.markdown(help_file.read(), extensions=["fenced_code"])
            return md_template_string
    except:
        flash("Sorry, we couldn't find that help topic.")
        return(redirect(url_for('main.help')))