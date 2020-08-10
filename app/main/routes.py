from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app
from app import db
from app.models import Sentry, FacebookPost, TwitterPost, TumblrPost, RedditPost, FacebookCred, TwitterCred, TumblrCred, RedditCred, Domain
from app.main.forms import short_text_builder, long_text_builder, image_builder, video_builder
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
import uuid
import json
from app.main import bp
from datetime import datetime, date
import boto3, botocore
import markdown
import markdown.extensions.fenced_code

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

def upload_s3(file, bucket_name, acl='public-read'):
    s3 = boto3.client("s3", aws_access_key_id=current_app.config['AWS_ACCESS_KET'], aws_secret_access_key=current_app.config['AWS_SECRET_KEY'])
    try:
        s3.upload_fileobj(file, bucket_name, file.filename, ExtraArgs={"ACL": acl, "ContentType": file.content_type})
    except Exception as e:
        raise e
    return "{}{}".format(current_app.config["S3_LOCATION"], file.filename)


# Trying client-side upload ;)
#@bp.route('/sign-s3')
#def sign_s3():
    #AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    #AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    #S3_BUCKET = os.environ.get('S3_BUCKET')
    
    #file_name = request.args.get('file-name')
    #file_type = request.args.get('file-type')

    #s3 = boto3.client(
        #'s3',
        #aws_access_key=AWS_ACCESS_KEY,
        #aws_secret_key=AWS_SECRET_KEY)

    #presigned_post = s3.generate_presigned_post(
        #Bucket=S3_BUCKET, 
        #Key=file_name, 
        #Fields={'acl': 'public-read', 'Content-Type': file_type},
        #Conditions=[
            #{'acl': 'public-read'},
            #{'Content-Type': file_type}
        #],
        #ExpiresIn=3600)

    #return json.dumps({
        #'data': presigned_post,
        #'url': 'https://{}.s3.amazonaws.com/{}'.format(S3_BUCKET, file_name)
    #})

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

    times_dict = {1: 'Mondays at', 2: 'Tuesdays at', 3: 'Wednesdays at', 4: 'Thursdays at', 5: 'Fridays at', 6: 'Saturdays at', 7: 'Sundays at'}

    facebook_times = []
    twitter_times = []
    tumblr_times = []
    reddit_times = []

    for cred in facebook_creds:
        slot = TimeSlot.query.filter_by(facebook_cred_id=cred.id).first()
        day_of_week = times_dict[slot.day_of_week]
        facebook_times.append('{} {}'.format(day_of_week, slot.time))

    for cred in twitter_creds:
        slot = TimeSlot.query.filter_by(twitter_cred_id=cred.id).first()
        day_of_week = times_dict[slot.day_of_week]
        twitter_times.append('{} {}'.format(day_of_week, slot.time))

    for cred in tumblr_creds:
        slot = TimeSlot.query.filter_by(tumblr_cred_id=cred.id).first()
        day_of_week = times_dict[slot.day_of_week]
        tumblr_times.append('{} {}'.format(day_of_week, slot.time))

    for cred in reddit_creds:
        slot = TimeSlot.query.filter_by(reddit_cred_id=cred.id).first()
        day_of_week = times_dict[slot.day_of_week]
        reddit_times.append('{} {}'.format(day_of_week, slot.time))

    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.dashboard', status_code=200, status_message='Successful dashboard access.')

    return render_template('main/dashboard.html', title='Dashboard', facebook_creds=facebook_creds, facebook_posts=facebook_posts, facebook_times=facebook_times, twitter_creds=twitter_creds, twitter_posts=twitter_posts, twitter_times=twitter_times, tumblr_creds=tumblr_creds, tumblr_posts=tumblr_posts, tumblr_times=tumblr_times, reddit_creds=reddit_creds, reddit_posts=reddit_posts, reddit_times=reddit_times)


# CREATE SHORT TEXT
@bp.route('/create/short-text', methods=['GET', 'POST'])
@login_required
def create_short_text():

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    form = short_text_builder()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Facebook')
                '''.format(x))

        if len(twitter_creds) > 0:
            for x in range(0, len(twitter_creds)-1):
                exec('''
                if form.twitter_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_twitter(cred_id=twitter_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Twitter')
                '''.format(x))
        
        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(cred_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Tumblr')
                '''.format(x))
        
        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_short_text', status_code=200, status_message='Reddit')
                '''.format(x))

        flash('Successfully queued!')
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_short_text.html', title='New Short Text Post', form=form)


# CREATE LONG TEXT
@bp.route('/create/long-text', methods=['GET', 'POST'])
@login_required
def create_long_text():

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    form = long_text_builder()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Facebook')
                '''.format(x))
        
        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    if forms.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(cred_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Tumblr')
                '''.format(x))
        
        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_long_text', status_code=200, status_message='Reddit')
                '''.format(x))
        
        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))
    
    return render_template('main/create_long_text.html', title='New Long Text Post', form=form)


# CREATE IMAGE POST
@bp.route('/create/image', methods=['GET', 'POST'])
@login_required
def create_image():

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    form = image_builder()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        f = form.image.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        
        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('facebook-' + image_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Facebook')
                '''.format(x))
            
        if len(twitter_creds) > 0:
            for x in range(0, len(twitter_creds)-1):
                exec('''
                if form.twitter_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('twitter-' + image_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_twitter(cred_id=twitter_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Twitter')
                '''.format(x))

        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('tumblr-' + image_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(client_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tags, caption=str(form.caption.data))
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Tumblr')
                '''.format(x))
        
        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('reddit-' + image_name + '.' + file_type)
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), video_url=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_image', status_code=200, status_message='Reddit')
                '''.format(x))
        
        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/create_image.html', title='New Image Post', form=form)


# CREATE VIDEO POST
@bp.route('/create/video', methods=['GET', 'POST'])
@login_required
def create_video():

    if current_user.is_create is False:
        flash("Talk to your domain admin about getting create permissions.")
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=403, status_message='Create permission denied.')
        return redirect(url_for('main.dashboard'))

    form = video_builder()

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        f = form.video.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x

        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('facebook-' + video_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Facebook')
                '''.format(x))

        if len(twitter_creds) > 0:
            for x in range(0, len(twitter_creds)-1):
                exec('''
                if form.twitter_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('twitter-' + video_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_twitter(cred_id=twitter_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Twitter')
                '''.format(x))
        
        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('tumblr-' + video_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(cred_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tags, caption=str(form.caption.data))
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Tumblr')
                '''.format(x))

        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('reddit-' + video_name + '.' + file_type)
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=None, video_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'))
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.create_video', status_code=200, status_message='Reddit')
                '''.format(x))
        
        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))
    
    return render_template('main/create_video.html', title='New Video Post', form=form)


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

    form = short_text_builder(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
                '''.format(x))

        if len(twitter_creds) > 0:
            for x in range(0, len(twitter_creds)-1):
                exec('''
                if form.twitter_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_twitter(cred_id=twitter_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Twitter|{}'.format(int(post_id)))
                '''.format(x))
        
        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(cred_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
                '''.format(x))
        
        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=1, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_short_text', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
                '''.format(x))

        flash('Successfully updated!')
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_short_text.html', title='Update Short Text Post', form=form)


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

    form = long_text_builder(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
                '''.format(x))
        
        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    if forms.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(cred_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), multimedia_url=None, tags=tags, caption=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
                '''.format(x))
        
        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=2, title=str(form.title.data), body=str(form.body.data), link_url=str(form.link_url.data), image_url=None, video_url=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_long_text', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
                '''.format(x))
        
        flash("Successfully updated!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_long_text.html', title='Update Long Text Post', form=form)


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

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))

    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))

    form = image_builder(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        f = form.image.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x
        
        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('facebook-' + image_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
                '''.format(x))
            
        if len(twitter_creds) > 0:
            for x in range(0, len(twitter_creds)-1):
                exec('''
                if form.twitter_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('twitter-' + image_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_twitter(cred_id=twitter_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Twitter|{}'.format(int(post_id)))
                '''.format(x))

        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('tumblr-' + image_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(client_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=None, link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tags, caption=str(form.caption.data))
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
                '''.format(x))
        
        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    image_name = str(uuid.uuid4())
                    f.filename = secure_filename('reddit-' + image_name + '.' + file_type)
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=3, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), video_url=None)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_image', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
                '''.format(x))
        
        flash("Successfully queued!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_image.html', title='Update Image Post', form=form)


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

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash('ERROR: Malformed request; platform not found.')
        return redirect(url_for('main.dashboard'))

    if post.domain_id != current_user.domain_id:
        make_sentry(user_id=current_user.id, domain_id=post.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=403, status_message='{}|{}'.format(str(platform), int(post_id)))
        flash("ERROR: That post isn't part of your domain.")
        return redirect(url_for('main.dashboard'))

    form = video_builder(obj=post)

    if form.validate_on_submit():

        current_user.post_count += 1
        db.session.add(current_user)
        db.session.commit()

        facebook_creds = FacebookCred.query.filter_by(domain_id=current_user.domain_id).all()
        twitter_creds = TwitterCred.query.filter_by(domain_id=current_user.domain_id).all()
        tumblr_creds = TumblrCred.query.filter_by(domain_id=current_user.domain_id).all()
        reddit_creds = RedditCred.query.filter_by(domain_id=current_user.domain_id).all()

        f = form.video.data
        file_list = str(f.filename).split('.')[-1:]
        for x in file_list:
            file_type = x

        if len(facebook_creds) > 0:
            for x in range(0, len(facebook_creds)-1):
                exec('''
                if form.facebook_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('facebook-' + video_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_facebook(cred_id=facebook_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Facebook|{}'.format(int(post_id)))
                '''.format(x))

        if len(twitter_creds) > 0:
            for x in range(0, len(twitter_creds)-1):
                exec('''
                if form.twitter_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('twitter-' + video_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                        tagline = ' #'.join(tags)
                        tagline = '#' + tagline
                    else:
                        tagline = None
                    make_twitter(cred_id=twitter_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, body=str(form.caption.data), link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tagline)
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Twitter|{}'.format(int(post_id)))
                '''.format(x))
        
        if len(tumblr_creds) > 0:
            for x in range(0, len(tumblr_creds)-1):
                exec('''
                if form.tumblr_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('tumblr-' + video_name + '.' + file_type)
                    if form.tags.data is not None:
                        tags = str(form.tags.data).split(', ')
                    else:
                        tags = None
                    make_tumblr(cred_id=tumblr_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=None, link_url=None, multimedia_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'), tags=tags, caption=str(form.caption.data))
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Tumblr|{}'.format(int(post_id)))
                '''.format(x))

        if len(reddit_creds) > 0:
            for x in range(0, len(reddit_creds)-1):
                exec('''
                if form.reddit_{}.data is True:
                    video_name = str(uuid.uuid4())
                    f.filename = secure_filename('reddit-' + video_name + '.' + file_type)
                    make_reddit(cred_id=reddit_creds[{}].id, domain_id=current_user.domain_id, user_id=current_user.id, post_type=4, title=str(form.title.data), body=str(form.caption.data), link_url=None, image_url=None, video_url=upload_s3(file=f, bucket_name=current_app.config["S3_BUCKET_NAME"], acl='public-read'))
                    make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.update_video', status_code=200, status_message='Reddit|{}'.format(int(post_id)))
                '''.format(x))
        
        flash("Successfully updated!")
        return redirect(url_for('main.dashboard'))

    return render_template('main/update_video.html', title='Update Video Post', form=form)

# DELETE POST
@bp.route('/delete/post/<platform>/<post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(platform, post_id):

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

        else:
            make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=400, status_message='{}|{}'.format(str(platform), int(post_id)))
            flash('ERROR: Malformed request; platform not found.')
            return redirect(url_for('main.dashboard'))

    else:
        make_sentry(user_id=current_user.id, domain_id=current_user.domain_id, ip_address=request.remote_addr, endpoint='main.delete_post', status_code=403, status_message='Delete permission denied.')
        flash("Talk to your domain admin about getting delete permissions.")
        return redirect(url_for('main.dashboard'))


# HELP
@bp.route('/help')
def help():
    return render_template('help/help.html', title='Help Topics')

@bp.route('/help/<topic>')
def help_topic(topic):
    try:
        with open("./docs/{}.md".format(topic), "r") as help_file:
            md_template_string = markdown.markdown(help_file.read(), extensions=["fenced_code"])
            return md_template_string
    except:
        flash("Sorry, we couldn't find that help topic.")
        return(redirect(url_for('main.help')))