from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
import jwt
from time import time
from flask import current_app
import os

'''
API RESOURCES:
    - Facebook: https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow
    - Twitter: https://github.com/bear/python-twitter
    - Tumblr: https://github.com/tumblr/pytumblr
    - Reddit: https://praw.readthedocs.io/en/latest/
    - YouTube: https://github.com/googleapis/google-api-python-client/
    - YouTube tutorial: https://developers.google.com/youtube/v3/guides/uploading_a_video
    - LinkedIn: https://github.com/ozgur/python-linkedin
'''

class Domain(db.Model):
    '''
    Domains are IcyFire customers. Users must belong to a domain.

    [id]                    : int       :   Primary key.
    [domain_name]           : str       :   Name for this domain.
    [sale_id]               : int       :   Foreign key that corresponds to the sale.
    [activation_code]       : str       :   UUID generated when payment is received.
    [expires_on]            : datetime  :   When does the subscription expire? (UTC)
    [stripe_customer_id]    : str       :   What is the customer ID on Stripe?
    [users]                 : rel       :   List of all users linked to this domain. 
    [facebook_posts]        : rel       :   List of all Facebook posts queued for this domain.
    [twitter_posts]         : rel       :   List of all Twitter posts queued for this domain.
    [tumblr_posts]          : rel       :   List of all Tumblr posts queued for this domain.
    [reddit_posts]          : rel       :   List of all Reddit posts queued for this domain.
    [facebook_creds]        : rel       :   List of all Facebook creds that belong to this domain.
    [twitter_creds]         : rel       :   List of all Twitter creds that belong to this domain.
    [tumblr_creds]          : rel       :   List of all Tumblr creds that belong to this domain.
    [reddit_creds]          : rel       :   List of all Reddit creds that belong to this domain.
    '''
    __tablename__ = 'domain'

    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.String(120), index=True, unique=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
    activation_code = db.Column(db.String(300), unique=True)
    expires_on = db.Column(db.DateTime, index=True)
    stripe_customer_id = db.Column(db.String(300), unique=True)
    users = db.relationship('User', backref='group', lazy='dynamic')
    facebook_posts = db.relationship('FacebookPost', backref='author', lazy='dynamic')
    twitter_posts = db.relationship('TwitterPost', backref='author', lazy='dynamic')
    tumblr_posts = db.relationship('TumblrPost', backref='author', lazy='dynamic')
    reddit_posts = db.relationship('RedditPost', backref='author', lazy='dynamic')
    facebook_creds = db.relationship('FacebookCred', backref='owner', lazy='dynamic')
    twitter_creds = db.relationship('TwitterCred', backref='owner', lazy='dynamic')
    tumblr_creds = db.relationship('TumblrCred', backref='owner', lazy='dynamic')
    reddit_creds = db.relationship('RedditCred', backref='owner', lazy='dynamic')

    def __repr__(self):
        return '<Domain {}>'.format(self.domain_name)


class FacebookCred(db.Model):
    '''
    FacebookCreds provide authentication and time information for Facebook accounts.

    [id]            : int :     Primary key.
    [domain_id]     : int :     The domain ID associated with this FacebookCred.
    [time_slots]    : rel :     TimeSlot ID(s) associated with this FacebookCred.
    [alias]         : str :     What is the human readable name for this FacebookCred?
    [page_id]       : str :     What is the Facebook page ID?
    [access_token]  : str :     What is the Facebook access token?
    '''
    __tablename__ = 'facebook_cred'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    time_slots = db.relationship('TimeSlot', backref='facebook_cred', lazy='dynamic')
    alias = db.Column(db.String(50))
    page_id = db.Column(db.String(50))
    access_token = db.Column(db.String(300))

    def __repr__(self):
        return '<FacebookCred {}-{}>'.format(self.domain_id, self.alias)


class TwitterCred(db.Model):
    '''
    TwitterCreds provide authentication and time information for Twitter accounts.

    [id]                    : int :     Primary key.
    [domain_id]             : int :     The domain ID associated with this TwitterCred.
    [time_slots]            : rel :     TimeSlot ID(s) associated with this TwitterCred.
    [alias]                 : str :     What is the human readable name for this TwitterCred?
    [consumer_key]          : str :     What is the consumer key?
    [consumer_secret]       : str :     What is the consumer secret?
    [access_token_key]      : str :     What is the access token key?
    [access_token_secret]   : str :     What is the access token secret?
    '''
    __tablename__ = 'twitter_cred'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id')) 
    time_slots = db.relationship('TimeSlot', backref='twitter_cred', lazy='dynamic')
    alias = db.Column(db.String(50))
    consumer_key = db.Column(db.String(300))
    consumer_secret = db.Column(db.String(300))
    access_token_key = db.Column(db.String(300))
    access_token_secret = db.Column(db.String(300))

    def __repr__(self):
        return '<TwitterCred {}-{}>'.format(self.domain_id, self.alias)


class TumblrCred(db.Model):
    '''
    TumblrCreds provide authentication and time information for Tumblr accounts.

    [id]                : int :     Primary key.
    [domain_id]         : int :     The domain ID associated with this TumblrCred.
    [time_slots]        : rel :     TimeSlot ID(s) associated with this TumblrCred.
    [alias]             : str :     What is the human readable name for this TwitterCred?
    [consumer_key]      : str :     What is the consumer key?
    [consumer_secret]   : str :     What is the consumer secret?
    [oauth_token]       : str :     What is the OAuth token?
    [oauth_secret]      : str :     What is the OAuth secret?
    [blog_name]         : str :     What is the name of the blog?
    '''
    __tablename__ = 'tumblr_cred'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id')) 
    time_slots = db.relationship('TimeSlot', backref='tumblr_cred', lazy='dynamic')
    alias = db.Column(db.String(50))
    consumer_key = db.Column(db.String(300))
    consumer_secret = db.Column(db.String(300))
    oauth_token = db.Column(db.String(300))
    oauth_secret = db.Column(db.String(300))
    blog_name = db.Column(db.String(300))

    def __repr__(self):
        return '<TumblrCred {}-{}>'.format(self.domain_id, self.alias)


class RedditCred(db.Model):
    '''
    RedditCreds provide authentication and time information for Reddit accounts.

    [id]                : int :     Primary key.
    [domain_id]         : int :     The domain ID associated with this RedditCred.
    [time_slots]        : rel :     TimeSlot ID(s) associated with this RedditCred.
    [alias]             : str :     What is the human readable name for this RedditCred?
    [client_id]         : str :     What is the client ID?
    [client_secret]     : str :     What is the client secret?
    [user_agent]        : str :     What is the user agent?
    [username]          : str :     What is the username?
    [password]          : str :     What is the password?
    [target_subreddit]  : str :     What subreddit will this post to?
    '''
    __tablename__ = 'reddit_cred'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id')) 
    time_slots = db.relationship('TimeSlot', backref='reddit_cred', lazy='dynamic')
    alias = db.Column(db.String(50))
    client_id = db.Column(db.String(300))
    client_secret = db.Column(db.String(300))
    user_agent = db.Column(db.String(300))
    username = db.Column(db.String(300))
    password = db.Column(db.String(300))
    target_subreddit = db.Column(db.String(300))

    def __repr__(self):
        return '<RedditCred {}-{}>'.format(self.domain_id, self.alias)


class TimeSlot(db.Model):
    '''
    A TimeSlot is a point in UTC time. There are 10,080 TimeSlots in a week.
    A TimeSlot can only be linked to one Cred. For example, if `facebook_cred_id` is not None, then `twitter..`, `tumblr..`, and `reddit..` are None.

    [id]                : int :     Primary key.
    [domain_id]         : int :     The domain ID associated with this TimeSlot.
    [facebook_cred_id]  : int :     The FacebookCred associated with this TimeSlot.
    [twitter_cred_id]   : int :     The TwitterCred associated with this TimeSlot.
    [tumblr_cred_id]    : int :     The TumblrCred associated with this TimeSlot.
    [reddit_cred_id]    : int :     The RedditCred associated with this TimeSlot.
    [server_id]         : int :     The server ID associated with this TimeSlot.
    [day_of_week]       : int :     1 = Monday, 2 = Tuesday, ..., 7 = Sunday
    [time]              : str :     24-hour time with a colon. (e.g. 12:34)
    '''
    __tablename__ = 'time_slot'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    facebook_cred_id = db.Column(db.Integer, db.ForeignKey('facebook_cred.id'))
    twitter_cred_id = db.Column(db.Integer, db.ForeignKey('twitter_cred.id'))
    tumblr_cred_id = db.Column(db.Integer, db.ForeignKey('tumblr_cred.id'))
    reddit_cred_id = db.Column(db.Integer, db.ForeignKey('reddit_cred.id'))
    server_id = db.Column(db.Integer)
    day_of_week = db.Column(db.Integer)
    time = db.Column(db.String(5))

    def __repr__(self):
        return '<TimeSlot {}-{}-{}>'.format(self.server_id, self.day_of_week, self.time)
    

class User(UserMixin, db.Model):
    '''
    Users belong to a domain. Users can log in and create, read, edit, and delete posts. Admins control the permissions of other users.
    UPDATED AS OF 2020-09-21:
    - Replaced `icyfire_crta` with `partner_id`
    - Added `is_verified` variable
    - Added `get_verify_email` method
    - Added `verify_verify_email_token` method

    [id]                : int  :    Primary key.
    [partner_id]        : int  :    IcyFire Partner ID, if applicable.
    [email]             : str  :    User's email address. Used for logins and communications.
    [password_hash]     : str  :    A hashed version of the user's password.
    [domain_id]         : int  :    Foreign key. The domain the user belongs to.
    [post_count]        : int  :    The number of posts the user has been involved in. Designed with performance evaluation in mind.
    [is_admin]          : bool :    Is the user a domain admin?
    [is_create]         : bool :    Can the user create new posts? (Default False until admin says otherwise.)
    [is_read]           : bool :    Can the user read existing posts? (Default False until admin says otherwise.)
    [is_update]         : bool :    Can the user update existing posts? (Default False until admin says otherwise.)
    [is_delete]         : bool :    Can the user delete existing posts? (Default False until admin says otherwise.)
    [is_verified]       : bool :    Has the user verified their email address? (Default False until they click the link we sent them.)
    [email_opt_in]      : bool :    Is the user subscribed to our marketing emails?
    '''
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'))
    email = db.Column(db.String(254), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id')) 
    post_count = db.Column(db.Integer)
    is_admin = db.Column(db.Boolean)
    is_create = db.Column(db.Boolean)
    is_read = db.Column(db.Boolean)
    is_update = db.Column(db.Boolean)
    is_delete = db.Column(db.Boolean)
    is_verified = db.Column(db.Boolean)
    email_opt_in = db.Column(db.Boolean)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in}, os.environ['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    
    def get_verify_email(self, expires_in=600):
        return jwt.encode({'verify_email': self.email, 'exp': time() + expires_in}, os.environ['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.filter_by(id=id).first()
    
    @staticmethod
    def verify_verify_email_token(token):
        try:
            email = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=['HS256'])['verify_email']
        except:
            return
        return User.query.filter_by(email=email).first()


class FacebookPost(db.Model):
    '''
    [id]                : int      :    Primary key. 
    [domain_id]         : int      :    Foreign key. The domain the post belongs to.
    [cred_id]           : int      :    Foreign key. The FacebookCred associated with the post.
    [user_id]           : int      :    Foreign key. The user who last edited the post.
    [post_type]         : int      :    1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime :    Date and time when the post was created (UTC).
    [body]              : text     :    Text body for text posts.
    [caption]           : str      :    Text body for multimedia posts.
    [link_url]          : str      :    A URL that links to a resource on the web.
    [multimedia_url]    : str      :    A URL that links to a multimedia resource uploaded to the IcyFire website.
    [tags]              : str      :    A comma-separated list (', ') with tags to be appended to the post.
    '''
    __tablename__ = 'facebook_post'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    cred_id = db.Column(db.Integer, db.ForeignKey('facebook_cred.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_type = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    body = db.Column(db.Text)
    caption = db.Column(db.String(300))
    link_url = db.Column(db.String(300))
    multimedia_url = db.Column(db.String(300))
    tags = db.Column(db.String(300))

    def __repr__(self):
        return '<FacebookPost {}>'.format(self.body)


class TwitterPost(db.Model):
    '''
    [id]                : int      :    Primary key.
    [domain_id]         : int      :    Foreign key. The domain the post belongs to.
    [cred_id]           : int      :    Foreign key. The TwitterCred associated with the post.
    [user_id]           : int      :    Foreign key. The user who last edited the post.
    [post_type]         : int      :    1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime :    Date and time when the post was created (UTC).
    [body]              : text     :    The body of a text post.
    [caption]           : str      :    The body of a multimedia post.
    [link_url]          : str      :    A URL that links to a resource on the web.
    [multimedia_url]    : str      :    A URL that links to a multimedia resource uploaded to the IcyFire website.
    [tags]              : str      :    A comma-separated list (', ') with tags to be appended to the post.
    '''
    __tablename__ = 'twitter_post'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    cred_id = db.Column(db.Integer, db.ForeignKey('twitter_cred.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_type = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    body = db.Column(db.String(300))
    caption = db.Column(db.String(300))
    link_url = db.Column(db.String(300))
    multimedia_url = db.Column(db.String(300))
    tags = db.Column(db.String(300))

    def __repr__(self):
        return '<TwitterPost {}>'.format(self.body)


class TumblrPost(db.Model):
    '''
    [id]                : int      :    Primary key.
    [domain_id]         : int      :    Foreign key. The domain the post belongs to.
    [cred_id]           : int      :    Foreign key. The TumblrCred associated with the post.
    [user_id]           : int      :    Foreign key. The user who last edited the post.
    [post_type]         : int      :    1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime :    Date and time when the post was created (UTC).
    [title]             : str      :    Post title.
    [body]              : text     :    The body of a text post.
    [link_url]          : str      :    A URL that links to a resource on the web.
    [multimedia_url]    : str      :    A URL that links to a multimedia resource uploaded to the IcyFire website.
    [tags]              : str      :    A comma-separated list (', ') with tags to be appended to the post.
    [caption]           : str      :    Caption to briefly describe an image or video.
    '''
    __tablename__ = 'tumblr_post'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    cred_id = db.Column(db.Integer, db.ForeignKey('tumblr_cred.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_type = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    title = db.Column(db.String(300))
    body = db.Column(db.Text)
    tags = db.Column(db.String(300))
    link_url = db.Column(db.String(300))
    multimedia_url = db.Column(db.String(300))
    caption = db.Column(db.String(300))

    def __repr__(self):
        return '<TumblrPost {}>'.format(self.body)


class RedditPost(db.Model):
    '''
    UPDATED AS OF 2020-09-22: Replaced `image_url` and `video_url` with `multimedia_url`.

    [id]                : int      :    Primary key.
    [domain_id]         : int      :    Foreign key. The domain the post belongs to.
    [cred_id]           : int      :    Foreign key. The RedditCred associated with the post.
    [user_id]           : int      :    Foreign key. The user who last edited the post.
    [post_type]         : int      :    1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime :    Date and time when the post was created (UTC).
    [title]             : str      :    Post title.
    [body]              : text     :    The body of a text post.
    [caption]           : str      :    The body of a multimedia post.
    [link_url]          : str      :    A URL that links to a resource on the web.
    [multimedia_url]    : str      :    A URL that links to a multimedia resource uploaded to the IcyFire website.
    '''
    __tablename__ = 'reddit_post'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    cred_id = db.Column(db.Integer, db.ForeignKey('reddit_cred.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_type = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    title = db.Column(db.String(300))
    body = db.Column(db.Text)
    caption = db.Column(db.String(300))
    link_url = db.Column(db.String(300))
    multimedia_url = db.Column(db.String(300))

    def __repr__(self):
        return '<RedditPost {}>'.format(self.body)


# class CountryLead(db.Model):
#     '''
#     Country Leads are responsible for organizing sales strategy at a national level.
#     !DEPRACATED AS OF 2020-09-21!

#     [id]            : int : Primary key.
#     [user_id]       : int : Foreign key. The user account associated with this rank.
#     [first_name]    : str : Individual's given name.
#     [last_name]     : str : Individual's family name.
#     [phone_country] : int : Individual's country code (e.g. 1 for USA, 86 for China).
#     [phone_number]  : str : Individual's phone number.
#     [crta_code]     : str : Country-Region-Team-Agent code. (e.g. USA-0-0-0)
#     [region_leads]  : rel : List of Region Leads that report to this individual.
#     [sales]         : rel : List of sales that have occurred in this individual's jurisdiction.
#     '''
#     __tablename__ = 'country_lead'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     first_name = db.Column(db.String(50))
#     last_name = db.Column(db.String(50))
#     phone_country = db.Column(db.Integer) 
#     phone_number = db.Column(db.String(15))
#     email = db.Column(db.String(254), index=True, unique=True)
#     crta_code = db.Column(db.String(20))
#     region_leads = db.relationship('RegionLead', backref='superior', lazy='dynamic')
#     sales = db.relationship('Sale', backref='country_lead', lazy='dynamic')

#     def __repr__(self):
#         return 'CountryLead {}'.format(self.crta_code)


# class RegionLead(db.Model):
#     '''
#     Region Leads are responsible for organizing sales strategy at a regional level.
#     !DEPRACATED AS OF 2020-09-21!

#     [id]                : int : Primary key.
#     [user_id]           : int : Foreign key. The user account associated with this rank.
#     [first_name]        : str : Individual's given name.
#     [last_name]         : str : Individual's family name.
#     [phone_country]     : int : Individual's country code (e.g. 1 for USA, 86 for China).
#     [phone_number]      : str : Individual's phone number.
#     [crta_code]         : str : Country-Region-Team-Agent code. (e.g. USA-PACIFIC-0-0)
#     [country_lead_id]   : int : Foreign key. The Country Lead this individual reports up to.
#     [team_leads]        : rel : List of Team Leads that report to this individual.
#     [sales]             : rel : List of sales that have occurred in this individual's jurisdiction.
#     '''
#     __tablename__ = 'region_lead'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     first_name = db.Column(db.String(50))
#     last_name = db.Column(db.String(50))
#     phone_country = db.Column(db.Integer)
#     phone_number = db.Column(db.String(15))
#     email = db.Column(db.String(254), index=True, unique=True)
#     crta_code = db.Column(db.String(20))
#     country_lead_id = db.Column(db.Integer, db.ForeignKey('country_lead.id'))
#     team_leads = db.relationship('TeamLead', backref='superior', lazy='dynamic')
#     sales = db.relationship('Sale', backref='region_lead', lazy='dynamic')

#     def __repr__(self):
#         return 'RegionLead {}'.format(self.crta_code)


# class TeamLead(db.Model):
#     '''
#     Team Leads are responsible for organizing sales operations at a local level.
#     !DEPRACATED AS OF 2020-09-21!

#     [id]                : int : Primary key.
#     [user_id]           : int : Foreign key. The user account associated with this rank.
#     [first_name]        : str : Individual's given name.
#     [last_name]         : str : Individual's family name.
#     [phone_country]     : int : Individual's country code (e.g. 1 for USA, 86 for China).
#     [phone_number]      : str : Individual's phone number.
#     [crta_code]         : str : Country-Region-Team-Agent code. (e.g. USA-PACIFIC-H-0)
#     [region_lead_id]    : int : Foreign key. The Region Lead this individual reports up to.
#     [agents]            : rel : List of Agents that report to this individual.
#     [sales]             : rel : List of sales that have occurred in this individual's jurisdiction.
#     '''
#     __tablename__ = 'team_lead'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     first_name = db.Column(db.String(50))
#     last_name = db.Column(db.String(50))
#     phone_country = db.Column(db.Integer) 
#     phone_number = db.Column(db.String(15))
#     email = db.Column(db.String(254), index=True, unique=True)
#     crta_code = db.Column(db.String(20))
#     region_lead_id = db.Column(db.Integer, db.ForeignKey('region_lead.id'))
#     agents = db.relationship('Agent', backref='superior', lazy='dynamic')
#     sales = db.relationship('Sale', backref='team_lead', lazy='dynamic')

#     def __repr__(self):
#         return 'TeamLead {}'.format(self.crta_code)


# class Agent(db.Model):
#     '''
#     Agents are responsible for implementing sales operations at a local level.
#     !DEPRACATED AS OF 2020-09-21!

#     [id]            : int : Primary key.
#     [user_id]       : int : Foreign key. The user account associated with this rank.
#     [first_name]    : str : Individual's given name.
#     [last_name]     : str : Individual's family name.
#     [phone_country] : int : Individual's country code (e.g. 1 for USA, 86 for China).
#     [phone_number]  : str : Individual's phone number.
#     [crta_code]     : str : Country-Region-Team-Agent code. (e.g. USA-PACIFIC-H-12)
#     [team_lead_id]  : int : Foreign key. The Team Lead this individual reports up to.
#     [sales]         : rel : List of sales that have occurred in this individual's jurisdiction.
#     '''
#     __tablename__ = 'agent'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     first_name = db.Column(db.String(50))
#     last_name = db.Column(db.String(50))
#     phone_country = db.Column(db.Integer)
#     phone_number = db.Column(db.String(15))
#     email = db.Column(db.String(254), index=True, unique=True)
#     crta_code = db.Column(db.String(20))
#     team_lead_id = db.Column(db.Integer, db.ForeignKey('team_lead.id'))
#     sales = db.relationship('Sale', backref='agent', lazy='dynamic')

#     def __repr__(self):
#         return 'Agent {}'.format(self.crta_code)


class Sale(db.Model):
    '''
    A sale is a transaction where a company buys one of our products.
    UPDATED AS OF 2020-09-21: 
    - `agent_id`, `team_lead_id`, `region_lead_id`, and `country_lead_id` replaced with `partner_id`. 
    - Added `product_id` variable.

    [id]                    : int      :    Primary key.
    [partner_id]            : int      :    Foreign key. The Partner associated with this sale.
    [timestamp]             : datetime :    Date and time this sale occurred, in UTC.
    [client_name]           : str      :    Company name.
    [client_street_address] : str      :    Company's street address. 
    [client_city]           : str      :    City where the company is located, or equivalent.
    [client_state]          : str      :    State where the company is located, or equivalent.
    [client_country]        : str      :    Country where the company is located, or equivalent.
    [client_zip]            : str      :    Company's postal code, or equivalent.
    [client_phone_country]  : int      :    Contact's country code (e.g. 1 for USA, 86 for China).
    [client_phone_number]   : str      :    Contact's phone number.
    [client_email]          : str      :    Contact's email address.
    [product_id]            : str      :    A unique product identifier.
    [unit_price]            : float    :    Price per unit sold (USD).
    [quantity]              : int      :    How many units were sold?
    [subtotal]              : float    :    [unit_price] * [quantity]
    [sales_tax]             : float    :    If applicable, [subtotal] * state sales tax rate
    [total]                 : float    :    [subtotal] + [sales_tax]
    [receipt_url]           : str      :    A link to download the receipt for this particular sale.
    '''
    __tablename__='sale'

    id = db.Column(db.Integer, primary_key=True)
    #agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    #team_lead_id = db.Column(db.Integer, db.ForeignKey('team_lead.id'))
    #region_lead_id = db.Column(db.Integer, db.ForeignKey('region_lead.id'))
    #country_lead_id = db.Column(db.Integer, db.ForeignKey('country_lead.id'))
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    client_name = db.Column(db.String(100))
    client_street_address = db.Column(db.String(100))
    client_city = db.Column(db.String(60))
    client_state = db.Column(db.String(50))
    client_country = db.Column(db.String(55))
    client_zip = db.Column(db.String(15))
    client_phone_country = db.Column(db.Integer)
    client_phone_number = db.Column(db.String(15))
    client_email = db.Column(db.String(254))
    product_id = db.Column(db.String(20))
    unit_price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    subtotal = db.Column(db.Float)
    sales_tax = db.Column(db.Float)
    total = db.Column(db.Float)
    receipt_url = db.Column(db.String(300))
    payment_reference = db.Column(db.String(100))

    def __repr__(self):
        return 'Sale {}'.format(self.timestamp)


class Sentry(db.Model):
    '''
    Sentry is a security system that logs successful access attempts. Sentry data is available to domain admins.

    [id]                : int      :    Primary key.
    [timestamp]         : datetime :    Date and time this occurred, in UTC.
    [ip_address]        : str      :    IP address the request came from.
    [user_id]           : int      :    Foreign key. The user account associated with this incident.
    [domain_id]         : int      :    Foreign key. The domain associated with this incident.
    [endpoint]          : str      :    What resource did the individual access?
    [status_code]       : int      :    HTTP status code.
    [status_message]    : str      :    More details about what happened.
    [flag]              : bool     :    Has this been reported to the IcyFire CISO for review?
    '''
    __tablename__='sentry'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    ip_address = db.Column(db.String(15))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    endpoint = db.Column(db.String(254))
    status_code = db.Column(db.Integer)
    status_message = db.Column(db.String(100))
    flag = db.Column(db.Boolean)

    def __repr__(self):
        return 'Sentry {}'.format(self.timestamp)


class Lead(db.Model):
    '''
    A Lead is an individual who has requested more information about our company or services.
    UPDATED AS OF 2020-09-21: 
    - `agent_id` changed to `partner_id`. 
    - `phone_number` changed from int to str for postgres.

    [id]                    : int       :   Primary key.
    [timestamp]             : datetime  :   Date and time this occurred, in UTC.
    [ip_address]            : str       :   What is the Lead's IP address?
    [partner_id]            : int       :   Foreign key. Which Partner has been assigned to this Lead?
    [is_contacted]          : bool      :   Has this Lead been contacted yet?
    [first_name]            : str       :   Individual's given name.
    [last_name]             : str       :   Individual's family name.
    [company_name]          : str       :   What company does this individual work for / is this individual representing?
    [job_title]             : str       :   What is the individual's job title? (Are they a decision maker?)
    [number_of_employees]   : int       :   How many employees does the company have? (1: 1 employee, 2: 2-10 employees, 3: 11-50, 4: 51-250, 5: 251-500, 6: 501-1,000, 7: 1,001-5,000, 8: 5,001-10,000, 9: 10,000+)
    [time_zone]             : int       :   What time zone is the Lead in? (1: Eastern, 2: Central, 3: Mountain, 4: Pacific, 5: Alaska, 6: Hawaii-Aleutian, 7: Other)
    [phone_number]          : str       :   What is the Lead's phone number? (Assuming a US number.)
    [email]                 : str       :   What is the Lead's business email?
    [contact_preference]    : int       :   How does the Lead want to be contacted? (0: No preference, 1: Email, 2: Phone call)
    [time_preference]       : int       :   When does the Lead want to be contacted? (0: No preference, 1: 8:00-9:30am, 2: 9:30-11:00am, 3: 11:00am-1:00pm, 4: 1:00-3:00pm, 5: 3:00-5:00pm)
    [email_opt_in]          : bool      :   Has this individual opted-in to marketing emails?
    '''
    __tablename__='lead'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'))
    is_contacted = db.Column(db.Boolean)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    company_name = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    number_of_employees = db.Column(db.Integer)
    time_zone = db.Column(db.Integer)
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100))
    contact_preference = db.Column(db.Integer)
    time_preference = db.Column(db.Integer)
    email_opt_in = db.Column(db.Boolean)

    def __repr__(self):
        return 'Lead {}'.format(self.email)


class Partner(db.Model):
    '''
    A Partner is an individual who contributes to operations at IcyFire.
    NEW AS OF 2020-09-21: Agent, Team Lead, Region Lead, and Country Lead entities depracated. Partner entity is the replacement.

    [id]            : int :     Primary key.
    [first_name]    : str :     What is the Partner's first name?
    [last_name]     : str :     What is the Partner's surname?
    [phone_number]  : str :     What is the Partner's phone number? (Assuming US number.)
    [email]         : str :     What is the Partner's email address?
    [leads]         : rel :     List of leads that the Partner is responsible for contacting.
    [sales]         : rel :     List of sales that the Partner is responsible for signing.
    '''
    __tablename__ = 'partner'

    id = db.Column(db.Integer, primary_key=True)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100))
    leads = db.relationship('Lead', backref='contact', lazy='dynamic')
    sales = db.relationship('Sale', backref='representative', lazy='dynamic')

    def __repr__(self):
        return 'Partner {} {}'.format(self.first_name, self.last_name)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
