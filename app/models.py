from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    twitter_consumer_key = db.Column(db.String(128))
    twitter_consumer_secret = db.Column(db.String(128))
    twitter_access_token_key = db.Column(db.String(128))
    twitter_access_token_secret = db.Column(db.String(128))
    tumblr_consumer_key = db.Column(db.String(128))
    tumblr_consumer_secret = db.Column(db.String(128))
    tumblr_oauth_token = db.Column(db.String(128))
    tumblr_oauth_secret = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_twitter = db.Column(db.Boolean) 
    is_tumblr = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
