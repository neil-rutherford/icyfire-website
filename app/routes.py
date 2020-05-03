from flask import render_template, flash, redirect, url_for, request, jsonify, Response
from app import app, db
from app.forms import LoginForm, RegistrationForm, PostForm
from app.models import User, Post
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import logging
from datetime import datetime


@app.route('/')
def main_page():
    return "Main page!"

@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=str(form.body.data), author=current_user, is_twitter=bool(form.is_twitter.data), is_tumblr=bool(form.is_tumblr.data))
        db.session.add(post)
        db.session.commit()
        flash('Success! Post queued.')
        return redirect(url_for('index'))
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.id.desc()).all()
    return render_template('index.html', title='Home', posts=posts, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password!')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Log In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=str(form.email.data))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations! You are now registered.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/delete/<post_id>')
@login_required
def delete(post_id):
    post = Post.query.filter_by(id=int(post_id)).first()
    if post is None:
        flash("Error: Post not found. Are you sure it hasn't already been deleted?")
        return redirect(url_for('index'))
    elif post.user_id != current_user.id:
        flash("Error: You don't have permission to delete that. Are you sure that post is yours to delete?")
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash("Success! Post deleted.")
    return redirect(url_for('index'))


@app.route('/help')
def help():
    return render_template('help.html', title='Help')


@app.route('/edit/<post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post = Post.query.filter_by(id=int(post_id)).first()
    if post is None:
        flash("Error: Post not found. Are you sure it hasn't already been deleted?")
        return redirect(url_for('index'))
    elif post.user_id != current_user.id:
        flash("Error: You don't have permission to edit that. Are you sure that post is yours to edit?")
        return redirect(url_for('index'))
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.body = str(form.body.data)
        post.is_twitter = bool(form.is_twitter.data)
        post.is_tumblr = bool(form.is_tumblr.data)
        db.session.commit()
        flash("Success! Post edited.")
        return redirect(url_for('index'))
    return render_template('edit.html', title='Edit Post', form=form)


@app.route('/api/_r/<read_token>&<email>', methods=['GET'])
def api_read(read_token, email):
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if read_token == 'read_test':
        user = User.query.filter_by(email=str(email)).first()
        if user is None:
            logging.warning('[ENDPOINT: api/_r, STATUS: 422 No Such User, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
            return jsonify(endpoint='api/_r', status='422 Unprocessable Entity', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such user.'), 422
        else:
            post = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.asc()).first()
            if post is None:
                logging.warning('[ENDPOINT: api/_r, STATUS: 404 No Such Post, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                logging.info('[ENDPOINT: api/_r, STATUS: 200 OK, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                return jsonify(body=post.body, is_twitter=post.is_twitter, is_tumblr=post.is_tumblr), 200
    else:
        logging.warning('[ENDPOINT: api/_r, STATUS: 403 Forbidden, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
        return jsonify(endpoint='api/_r', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403


@app.route('/api/_d/<read_token>&<delete_token>&<email>', methods=['GET', 'POST'])
def api_delete(read_token, delete_token, email):
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if delete_token == 'delete_test' and read_token == 'read_test':
        user = User.query.filter_by(email=str(email)).first()
        if user is None:
            logging.warning('[ENDPOINT: api/_d, STATUS: 422 No Such User, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
            return jsonify(endpoint='api/_d', status='422 Unprocessable Entity', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such user.'), 422
        else:
            post = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.asc()).first()
            if post is None:
                logging.warning('[ENDPOINT: api/_d, STATUS: 404 No Such Post, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                db.session.delete(post)
                db.session.commit()
                logging.info('[ENDPOINT: api/_d, STATUS: 204 No Content, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
    else:
        logging.warning('[ENDPOINT: api/_d, STATUS: 403 Forbidden, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
        return jsonify(endpoint='api/_d', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403


@app.route('/api/_p/<platform>/<read_token>&<delete_token>&<permission_token>&<email>', methods=['GET'])
def api_permission(platform, read_token, delete_token, permission_token, email):
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if read_token == 'read_test' and delete_token == 'delete_test' and permission_token == 'permission_test':
        user = User.query.filter_by(email=str(email)).first()
        if user is None:
            logging.warning('[ENDPOINT: api/_p, STATUS: 422 No Such User, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
            return jsonify(endpoint='api/_p', status='422 Unprocessable Entity', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such user.'), 422
        else:
            if platform == 'twitter':
                twitter_consumer_key = user.twitter_consumer_key
                twitter_consumer_secret = user.twitter_consumer_secret
                twitter_access_token_key = user.twitter_access_token_key
                twitter_access_token_secret = user.twitter_access_token_secret
                if twitter_consumer_key is None or twitter_consumer_secret is None or twitter_access_token_key is None or twitter_access_token_secret is None:
                    logging.warning('[ENDPOINT: api/_p/twitter, STATUS: 404 No Such Credentials, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                    return jsonify(endpoint='api/_p/twitter', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such credentials.'), 404
                else:
                    logging.info('[ENDPOINT: api/_p/twitter, STATUS: 200 OK, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                    return jsonify(consumer_key=twitter_consumer_key, consumer_secret=twitter_consumer_secret, access_token_key=twitter_access_token_key, access_token_secret=twitter_access_token_secret), 200
            elif platform == 'tumblr':
                tumblr_consumer_key = user.tumblr_consumer_key
                tumblr_consumer_secret = user.tumblr_consumer_key
                tumblr_oauth_token = user.tumblr_oauth_token
                tumblr_oauth_secret = user.tumblr_oauth_secret
                if tumblr_consumer_key is None or tumblr_consumer_secret is None or tumblr_oauth_token is None or tumblr_oauth_secret is None:
                    logging.warning('[ENDPOINT: api/_p/tumblr, STATUS: 404 No Such Credentials, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                    return jsonify(endpoint='api/_p/tumblr', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such credentials.'), 404
                else:
                    logging.info('[ENDPOINT: api/_p/tumblr, STATUS: 200 OK, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                    return jsonify(consumer_key=tumblr_consumer_key, consumer_secret=tumblr_consumer_secret, oauth_token=tumblr_oauth_token, oauth_secret=tumblr_oauth_secret), 200
            else:
                logging.warning('[ENDPOINT: api/_p, STATUS: 400 Bad Request, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
                return jsonify(endpoint='api/_p', status='400 Bad Request', utc_timestamp=timestamp, ip_address=ip_address, error_details='Malformed request; platform needs to be specified.'), 400
    else:
        logging.warning('[ENDPOINT: api/_p, STATUS: 403 Forbidden, UTC_TIMESTAMP: {}, IP_ADDRESS: {}]'.format(timestamp, ip_address))
        return jsonify(endpoint='api/_p', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403
