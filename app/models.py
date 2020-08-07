from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
import jwt
from time import time
from flask import current_app

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

    [id]                    : int  : Primary key.
    [domain_name]           : str  : Name for this domain.
    [sale_id]               : int  : Foreign key that corresponds to the sale.
    [activation_code]       : str  : UUID generated when payment is received.
    [requested_time_slots]  : text : Set-up information for IcyFire server administrators.
    [users]                 : rel  : List of all users linked to this domain. 
    [facebook_posts]        : rel  : List of all Facebook posts queued for this domain.
    [twitter_posts]         : rel  : List of all Twitter posts queued for this domain.
    [tumblr_posts]          : rel  : List of all Tumblr posts queued for this domain.
    [reddit_posts]          : rel  : List of all Reddit posts queued for this domain.
    [youtube_posts]         : rel  : List of all YouTube posts queued for this domain.
    [linkedin_posts]        : rel  : List of all LinkedIn posts queued for this domain.
    [facebook_token]        : str  : Access token for the domain's Facebook account.
    [twitter_token]         : str  : Access token for the domain's Twitter account.
    [twitter_secret]        : str  : Access secret for the domain's Twitter account.
    [tumblr_blog_name]      : str  : Name of domain's blog.
    [tumblr_token]          : str  : Access token for the domain's Tumblr account.
    [tumblr_secret]         : str  : Secret token for the domain's Tumblr account.
    [reddit_subreddit]      : str  : Name of the domain's subreddit. (We don't want to spam subreddits that don't belong to the domain yet.)
    [reddit_username]       : str  : Username for the domain's Reddit account.
    [reddit_password]       : str  : Password for the domain's Reddit account. (TO-DO: Deal with this plaintext password.)
    [youtube_refresh]       : str  : Refresh token for the domain's YouTube account.
    [youtube_access]        : str  : Access token for the domain's YouTube account. (Note: Use the refresh token to generate a new one when this expires.)
    [linkedin_author]       : str  : LinkedIn account's URN (member identifier).
    [linkedin_token]        : str  : User token for the domain's LinkedIn account.
    [linkedin_secret]       : str  : User secret for the domain's LinkedIn account.
    '''
    __tablename__ = 'domain'

    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.String(120), index=True, unique=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
    activation_code = db.Column(db.String(300), unique=True)
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
    __tablename__ = 'facebook_cred'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    time_slots = db.relationship('TimeSlot', backref='facebook_cred', lazy='dynamic')
    alias = db.Column(db.String(50))
    access_token = db.Column(db.String(300))

    def __repr__(self):
        return '<FacebookCred {}-{}>'.format(self.domain_id, self.alias)


class TwitterCred(db.Model):
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

    [id]                : int  : Primary key.
    [email]             : str  : User's email address. Used for logins and communications.
    [password_hash]     : str  : A hashed version of the user's password.
    [domain_id]         : int  : Foreign key. The domain the user belongs to.
    [post_count]        : int  : The number of posts the user has been involved in. Designed with performance evaluation in mind.
    [is_admin]          : bool : Is the user a domain admin?
    [is_create]         : bool : Can the user create new posts? (Default False until admin says otherwise.)
    [is_read]           : bool : Can the user read existing posts? (Default False until admin says otherwise.)
    [is_update]         : bool : Can the user update existing posts? (Default False until admin says otherwise.)
    [is_delete]         : bool : Can the user delete existing posts? (Default False until admin says otherwise.)
    [email_opt_in]      : bool : Is the user subscribed to our marketing emails?
    [icyfire_crta]      : str  : IcyFire Country-Region-Team-Agent code, if applicable.
    '''
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id')) 
    post_count = db.Column(db.Integer)
    is_admin = db.Column(db.Boolean)
    is_create = db.Column(db.Boolean)
    is_read = db.Column(db.Boolean)
    is_update = db.Column(db.Boolean)
    is_delete = db.Column(db.Boolean)
    email_opt_in = db.Column(db.Boolean)
    icyfire_crta = db.Column(db.String(20))

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in}, current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class FacebookPost(db.Model):
    '''
    [id]                : int      : Primary key. 
    [domain_id]         : int      : Foreign key. The domain the post belongs to.
    [user_id]           : int      : Foreign key. The user who last edited the post.
    [post_type]         : int      : 1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime : Date and time when the post was created (UTC).
    [body]              : text     : The body of the post.
    [link_url]          : str      : A URL that links to a resource on the web.
    [multimedia_url]    : str      : A URL that links to a multimedia resource uploaded to the IcyFire website.
    [tags]              : str      : A Python list object with tags to be appended to the post.
    '''
    __tablename__ = 'facebook_post'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    cred_id = db.Column(db.Integer, db.ForeignKey('facebook_cred.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_type = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    body = db.Column(db.Text)
    link_url = db.Column(db.String(300))
    multimedia_url = db.Column(db.String(300))
    tags = db.Column(db.String(300))

    def __repr__(self):
        return '<FacebookPost {}>'.format(self.body)


class TwitterPost(db.Model):
    '''
    [id]                : int      : Primary key.
    [domain_id]         : int      : Foreign key. The domain the post belongs to.
    [user_id]           : int      : Foreign key. The user who last edited the post.
    [post_type]         : int      : 1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime : Date and time when the post was created (UTC).
    [body]              : text     : The body of the post.
    [link_url]          : str      : A URL that links to a resource on the web.
    [multimedia_url]    : str      : A URL that links to a multimedia resource uploaded to the IcyFire website.
    [tags]              : str      : A Python list object with tags to be appended to the post.
    '''
    __tablename__ = 'twitter_post'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    cred_id = db.Column(db.Integer, db.ForeignKey('twitter_cred.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_type = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    body = db.Column(db.String(300)) 
    link_url = db.Column(db.String(300))
    multimedia_url = db.Column(db.String(300))
    tags = db.Column(db.String(300))

    def __repr__(self):
        return '<TwitterPost {}>'.format(self.body)


class TumblrPost(db.Model):
    '''
    [id]                : int      : Primary key.
    [domain_id]         : int      : Foreign key. The domain the post belongs to.
    [user_id]           : int      : Foreign key. The user who last edited the post.
    [post_type]         : int      : 1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime : Date and time when the post was created (UTC).
    [title]             : str      : Post title.
    [body]              : text     : The body of the post.
    [link_url]          : str      : A URL that links to a resource on the web.
    [multimedia_url]    : str      : A URL that links to a multimedia resource uploaded to the IcyFire website.
    [tags]              : str      : A Python list object with tags to be appended to the post.
    [caption]           : str      : Caption to briefly describe an image or video.
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
    [id]                : int      : Primary key.
    [domain_id]         : int      : Foreign key. The domain the post belongs to.
    [user_id]           : int      : Foreign key. The user who last edited the post.
    [post_type]         : int      : 1 = short text, 2 = long text, 3 = image, 4 = video.
    [timestamp]         : datetime : Date and time when the post was created (UTC).
    [title]             : str      : Post title.
    [body]              : text     : The body of the post.
    [link_url]          : str      : A URL that links to a resource on the web.
    [image_url]         : str      : A URL that links to an image resource uploaded to the IcyFire website.
    [video_url]         : str      : A URL that links to a video resource uploaded to the IcyFire website.
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
    link_url = db.Column(db.String(300))
    image_url = db.Column(db.String(300))
    video_url = db.Column(db.String(300))

    def __repr__(self):
        return '<RedditPost {}>'.format(self.body)


#class YoutubePost(db.Model):
    #'''
    #[id]                : int      : Primary key.
    #[domain_id]         : int      : Foreign key. The domain the post belongs to.
    #[user_id]           : int      : Foreign key. The user who last edited the post.
    #[timestamp]         : datetime : Date and time when the post was created (UTC).
    #[multimedia_url]    : str      : A URL that links to a video resource uploaded to the IcyFire website.
    #[title]             : str      : Video title.
    #[caption]           : str      : Video description.
    #[tags]              : str      : Video tags.
    #[category]          : int      : Code for YouTube's internal video classification system.
    #'''
    #__tablename__ = 'youtube_post'

    #id = db.Column(db.Integer, primary_key=True)
    #domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #multimedia_url = db.Column(db.String(300))
    #title = db.Column(db.String(300))
    #caption = db.Column(db.String(300))
    #tags = db.Column(db.String(300))
    #category = db.Column(db.Integer)

    #def __repr__(self):
        #return '<YoutubePost {}>'.format(self.body)


#class LinkedinPost(db.Model):
    #'''
    #[id]                : int      : Primary key.
    #[domain_id]         : int      : Foreign key. The domain the post belongs to.
    #[user_id]           : int      : Foreign key. The user who last edited the post.
    #[post_type]         : int      : 1 = short text, 2 = long text, 3 = image, 4 = video.
    #[timestamp]         : datetime : Date and time when the post was created (UTC).
    #[title]             : str      : Post title.
    #[body]              : text     : Post body.
    #[caption]           : str      : Caption that briefly describes multimedia.
    #[multimedia_url]    : str      : A URL that links to a video resource uploaded to the IcyFire website.
    #[link_url]          : str      : A URL that links to a resource on the web.
    #[tags]              : str      : A list of tags.
    #'''
    #__tablename__ = 'linkedin_post'

    #id = db.Column(db.Integer, primary_key=True)
    #domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #post_type = db.Column(db.Integer)
    #timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #title = db.Column(db.String(300))
    #body = db.Column(db.Text)
    #caption = db.Column(db.String(300))
    #multimedia_url = db.Column(db.String(300))
    #link_url = db.Column(db.String(300))
    #tags = db.Column(db.String(300))

    #def __repr__(self):
        #return '<LinkedinPost {}>'.format(self.body)


class CountryLead(db.Model):
    '''
    Country Leads are responsible for organizing sales strategy at a national level.

    [id]            : int : Primary key.
    [user_id]       : int : Foreign key. The user account associated with this rank.
    [first_name]    : str : Individual's given name.
    [last_name]     : str : Individual's family name.
    [phone_country] : int : Individual's country code (e.g. 1 for USA, 86 for China).
    [phone_number]  : int : Individual's phone number.
    [crta_code]     : str : Country-Region-Team-Agent code. (e.g. USA-0-0-0)
    [region_leads]  : rel : List of Region Leads that report to this individual.
    [sales]         : rel : List of sales that have occurred in this individual's jurisdiction.
    '''
    __tablename__ = 'country_lead'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_country = db.Column(db.Integer) 
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(254), index=True, unique=True)
    crta_code = db.Column(db.String(20))
    region_leads = db.relationship('RegionLead', backref='superior', lazy='dynamic')
    sales = db.relationship('Sale', backref='country_lead', lazy='dynamic')

    def __repr__(self):
        return 'CountryLead {}'.format(self.crta_code)


class RegionLead(db.Model):
    '''
    Region Leads are responsible for organizing sales strategy at a regional level.

    [id]                : int : Primary key.
    [user_id]           : int : Foreign key. The user account associated with this rank.
    [first_name]        : str : Individual's given name.
    [last_name]         : str : Individual's family name.
    [phone_country]     : int : Individual's country code (e.g. 1 for USA, 86 for China).
    [phone_number]      : int : Individual's phone number.
    [crta_code]         : str : Country-Region-Team-Agent code. (e.g. USA-PACIFIC-0-0)
    [country_lead_id]   : int : Foreign key. The Country Lead this individual reports up to.
    [team_leads]        : rel : List of Team Leads that report to this individual.
    [sales]             : rel : List of sales that have occurred in this individual's jurisdiction.
    '''
    __tablename__ = 'region_lead'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_country = db.Column(db.Integer)
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(254), index=True, unique=True)
    crta_code = db.Column(db.String(20))
    country_lead_id = db.Column(db.Integer, db.ForeignKey('country_lead.id'))
    team_leads = db.relationship('TeamLead', backref='superior', lazy='dynamic')
    sales = db.relationship('Sale', backref='region_lead', lazy='dynamic')

    def __repr__(self):
        return 'RegionLead {}'.format(self.crta_code)


class TeamLead(db.Model):
    '''
    Team Leads are responsible for organizing sales operations at a local level.

    [id]                : int : Primary key.
    [user_id]           : int : Foreign key. The user account associated with this rank.
    [first_name]        : str : Individual's given name.
    [last_name]         : str : Individual's family name.
    [phone_country]     : int : Individual's country code (e.g. 1 for USA, 86 for China).
    [phone_number]      : int : Individual's phone number.
    [crta_code]         : str : Country-Region-Team-Agent code. (e.g. USA-PACIFIC-H-0)
    [region_lead_id]    : int : Foreign key. The Region Lead this individual reports up to.
    [agents]            : rel : List of Agents that report to this individual.
    [sales]             : rel : List of sales that have occurred in this individual's jurisdiction.
    '''
    __tablename__ = 'team_lead'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_country = db.Column(db.Integer) 
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(254), index=True, unique=True)
    crta_code = db.Column(db.String(20))
    region_lead_id = db.Column(db.Integer, db.ForeignKey('region_lead.id'))
    agents = db.relationship('Agent', backref='superior', lazy='dynamic')
    sales = db.relationship('Sale', backref='team_lead', lazy='dynamic')

    def __repr__(self):
        return 'TeamLead {}'.format(self.crta_code)


class Agent(db.Model):
    '''
    Agents are responsible for implementing sales operations at a local level.

    [id]            : int : Primary key.
    [user_id]       : int : Foreign key. The user account associated with this rank.
    [first_name]    : str : Individual's given name.
    [last_name]     : str : Individual's family name.
    [phone_country] : int : Individual's country code (e.g. 1 for USA, 86 for China).
    [phone_number]  : int : Individual's phone number.
    [crta_code]     : str : Country-Region-Team-Agent code. (e.g. USA-PACIFIC-H-12)
    [team_lead_id]  : int : Foreign key. The Team Lead this individual reports up to.
    [sales]         : rel : List of sales that have occurred in this individual's jurisdiction.
    '''
    __tablename__ = 'agent'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_country = db.Column(db.Integer)
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(254), index=True, unique=True)
    crta_code = db.Column(db.String(20))
    team_lead_id = db.Column(db.Integer, db.ForeignKey('team_lead.id'))
    sales = db.relationship('Sale', backref='agent', lazy='dynamic')

    def __repr__(self):
        return 'Agent {}'.format(self.crta_code)


class Sale(db.Model):
    '''
    A sale is a transaction where a company buys our product.

    [id]                    : int      : Primary key.
    [agent_id]              : int      : Foreign key. The Agent account associated with this sale.
    [team_lead_id]          : int      : Foreign key. The Team Lead account associated with this sale.
    [region_lead_id]        : int      : Foreign key. The Region Lead account associated with this sale.
    [country_lead_id]       : int      : Foreign key. The Country Lead account associated with this sale.
    [timestamp]             : datetime : Date and time this sale occurred, in UTC.
    [client_name]           : str      : Company name.
    [client_street_address] : str      : Company's street address. 
    [client_city]           : str      : City where the company is located, or equivalent.
    [client_state]          : str      : State where the company is located, or equivalent.
    [client_country]        : str      : Country where the company is located, or equivalent.
    [client_zip]            : str      : Company's postal code, or equivalent.
    [client_phone_country]  : int      : Contact's country code (e.g. 1 for USA, 86 for China).
    [client_phone_number]   : int      : Contact's phone number.
    [client_email]          : str      : Contact's email address.
    [unit_price]            : float    : Price per unit sold (USD).
    [quantity]              : int      : How many units were sold?
    [subtotal]              : float    : [unit_price] * [quantity]
    [sales_tax]             : float    : If applicable, [subtotal] * state sales tax rate
    [total]                 : float    : [subtotal] + [sales_tax]
    [receipt_url]           : str      : A link to download the receipt for this particular sale.
    '''
    __tablename__='sale'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    team_lead_id = db.Column(db.Integer, db.ForeignKey('team_lead.id'))
    region_lead_id = db.Column(db.Integer, db.ForeignKey('region_lead.id'))
    country_lead_id = db.Column(db.Integer, db.ForeignKey('country_lead.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    client_name = db.Column(db.String(100))
    client_street_address = db.Column(db.String(100))
    client_city = db.Column(db.String(60))
    client_state = db.Column(db.String(50))
    client_country = db.Column(db.String(55))
    client_zip = db.Column(db.String(15))
    client_phone_country = db.Column(db.Integer)
    client_phone_number = db.Column(db.Integer)
    client_email = db.Column(db.String(254))
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

    [id]                : int      : Primary key.
    [timestamp]         : datetime : Date and time this occurred, in UTC.
    [ip_address]        : str      : IP address the request came from.
    [user_id]           : int      : Foreign key. The user account associated with this incident.
    [domain_id]         : int      : Foreign key. The domain associated with this incident.
    [endpoint]          : str      : What resource did the individual access?
    [status_code]       : int      : HTTP status code.
    [status_message]    : str      : More details about what happened.
    [flag]              : bool     : Has this been reported to the IcyFire CISO for review?
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

    [id]                    : int       : Primary key.
    [timestamp]             : datetime  : Date and time this occurred, in UTC.
    [ip_address]            : str       : What is the Lead's IP address?
    [agent_id]              : rel       : Foreign key. Which Agent has been assigned to this Lead?
    [is_contacted]          : bool      : Has this Lead been contacted yet?
    [first_name]            : str       : Individual's given name.
    [last_name]             : str       : Individual's family name.
    [company_name]          : str       : What company does this individual work for / is this individual representing?
    [job_title]             : str       : What is the individual's job title? (Are they a decision maker?)
    [number_of_employees]   : int       : How many employees does the company have? (1: 1 employee, 2: 2-10 employees, 3: 11-50, 4: 51-250, 5: 251-500, 6: 501-1,000, 7: 1,001-5,000, 8: 5,001-10,000, 9: 10,000+)
    [time_zone]             : int       : What time zone is the Lead in? (1: Eastern, 2: Central, 3: Mountain, 4: Pacific, 5: Alaska, 6: Hawaii-Aleutian, 7: Other)
    [phone_number]          : int       : What is the Lead's phone number? (Assuming a US number. If they are not in the US, they have been instructed to contact us by email.)
    [email]                 : str       : What is the Lead's business email?
    [contact_preference]    : int       : How does the Lead want to be contacted? (0: No preference, 1: Email, 2: Phone call)
    [time_preference]       : int       : When does the Lead want to be contacted? (0: No preference, 1: 8:00-9:30am, 2: 9:30-11:00am, 3: 11:00am-1:00pm, 4: 1:00-3:00pm, 5: 3:00-5:00pm)
    [email_opt_in]          : bool      : Has this individual opted-in to marketing emails?
    '''
    __tablename__='lead'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    is_contacted = db.Column(db.Boolean)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    company_name = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    number_of_employees = db.Column(db.Integer)
    time_zone = db.Column(db.Integer)
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(100))
    contact_preference = db.Column(db.Integer)
    time_preference = db.Column(db.Integer)
    email_opt_in = db.Column(db.Boolean)

    def __repr__(self):
        return 'Lead {}'.format(self.email)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
