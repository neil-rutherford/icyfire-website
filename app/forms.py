from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User, Domain
from flask_login import current_user


def password_check(form, field):
    '''
    Custom validator that checks to see if two passwords are equal.
    '''
    if form.password.data != form.verify_password.data:
        raise ValidationError('Passwords must match.')

def image_file_check(form, field):
    '''
    Custom validator that checks for image files.
    '''
    allowed_extensions = ['png', 'jpg', 'jpeg']
    filetype = str(form.image.data).split('.')[-1:]
    for extension in filetype:
        if str(extension).lower() not in allowed_extensions:
            raise ValidationError('Sorry, only PNG, JPG, and JPEG files are allowed.')

def video_file_check(form, field):
    '''
    Custom validator that checks for video files.
    '''
    allowed_extensions = ['avi', 'flv', 'wmv', 'mov', 'mp4']
    filetype = str(form.video.data).split('.')[-1:]
    for extension in filetype:
        if str(extension).lower() not in allowed_extensions:
            raise ValidationError('Sorry, only AVI, FLV, WMV, MOV, and MP4 files are allowed.')

def icyfire_email_check(form, field):
    '''
    Custom validator that raises a ValidationError if an email address does not belong to the "@icy-fire.com" domain.
    '''
    domain = str(field.data).split('@')[-1:]
    for domain in domain:
        if domain != 'icy-fire.com':
            raise ValidationError('Please use an IcyFire email address.')

def phone_check(form, field):
    '''
    Custom validator that raises a ValidationError if there are non-numeric characters.
    '''
    numbers = ['0','1','2','3','4','5','6','7','8','9']
    for character in str(field.data):
        if character == '-':
            raise ValidationError("We're expecting something like 1112223333, not 111-222-3333.")
        elif character not in numbers:
            raise ValidationError('Numbers only, please.')


class LoginForm(FlaskForm):
    '''
    Login form that takes email and password.
    '''
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')


class DomainRegistrationForm(FlaskForm):
    '''
    New admins set up their new domain here. 
    Activation codes are generated and emailed to companies when they pay for the service.
    '''
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password (8 characters minimum)', validators=[DataRequired(), Length(min=8)])
    verify_password = PasswordField('Verify password', validators=[DataRequired(), password_check])
    domain_name = StringField('Choose a name for your domain', validators=[DataRequired(), Length(max=120)])
    activation_code = StringField('Activation code', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        '''
        If an account already exists with that email address, this check raises a ValidationError.
        '''
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_activation_code(self, activation_code):
        '''
        If the activation code they entered is not valid, this check raises a ValidationError.
        '''
        domain = Domain.query.filter_by(activation_code=activation_code.data).first()
        if domain is None:
            raise ValidationError('Activation code incorrect. Please try again or contact your agent for assistance.')
    
    def validate_domain_name(self, domain_name):
        '''
        If the domain name they chose is not unique, this check raises a ValidationError.
        '''
        domain = Domain.query.filter_by(domain_name=domain_name.data).first()
        if domain is not None:
            raise ValidationError('Please choose a different domain name.')


class UserRegistrationForm(FlaskForm):
    '''
    Normal users link to an existing domain here.
    '''
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password (8 characters minimum)', validators=[DataRequired(), Length(min=8)])
    verify_password = PasswordField('Verify password', validators=[DataRequired(), password_check])
    domain_name = StringField('Domain name')
    submit = SubmitField('Register')

    def validate_email(self, email):
        '''
        If an account already exists with that email address, this check raises a ValidationError.
        '''
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_domain_name(self, domain_name):
        '''
        If the domain name they entered doesn't exist, this check raises a ValidationError.
        '''
        domain = Domain.query.filter_by(domain_name=domain_name.data).first()
        if domain is None:
            raise ValidationError("That domain doesn't exist. Please try again or contact your administrator for assistance.")


class ContractorRegistrationForm(FlaskForm):
    icyfire_region = SelectField('What state are you in?', choices=[
        ('00', 'Not applicable. I am the Country Lead.'),
        ('SOUTH', 'Alabama'),
        ('PACIFIC', 'Alaska'),
        ('PACIFIC', 'Arizona'),
        ('SOUTH', 'Arkansas'),
        ('PACIFIC', 'California'),
        ('FRONTIER', 'Colorado'),
        ('NORTHEAST', 'Connecticut'),
        ('NORTHEAST', 'Delaware'),
        ('NORTHEAST', 'District of Columbia'),
        ('SOUTH', 'Florida'),
        ('SOUTH', 'Georgia'),
        ('PACIFIC', 'Hawaii'),
        ('FRONTIER', 'Idaho'),
        ('MIDWEST', 'Illinois'),
        ('MIDWEST', 'Indiana'),
        ('MIDWEST', 'Iowa'),
        ('FRONTIER', 'Kansas'),
        ('SOUTH', 'Kentucky'),
        ('SOUTH', 'Louisiana'),
        ('NORTHEAST', 'Maine'),
        ('NORTHEAST', 'Maryland'),
        ('NORTHEAST', 'Massachusetts'),
        ('MIDWEST', 'Michigan'),
        ('MIDWEST', 'Minnesota'),
        ('SOUTH', 'Mississippi'),
        ('MIDWEST', 'Missouri'),
        ('FRONTIER', 'Montana'),
        ('FRONTIER', 'Nebraska'),
        ('PACIFIC', 'Nevada'),
        ('NORTHEAST', 'New Hampshire'),
        ('NORTHEAST', 'New Jersey'),
        ('FRONTIER', 'New Mexico'),
        ('NORTHEAST', 'New York'),
        ('SOUTH', 'North Carolina'),
        ('MIDWEST', 'North Dakota'),
        ('MIDWEST', 'Ohio'),
        ('FRONTIER', 'Oklahoma'),
        ('PACIFIC', 'Oregon'),
        ('NORTHEAST', 'Pennsylvania'),
        ('NORTHEAST', 'Rhode Island'),
        ('SOUTH', 'South Carolina'),
        ('MIDWEST', 'South Dakota'),
        ('SOUTH', 'Tennessee'),
        ('FRONTIER', 'Texas'),
        ('FRONTIER', 'Utah'),
        ('NORTHEAST', 'Vermont'),
        ('SOUTH', 'Virginia'),
        ('PACIFIC', 'Washington'),
        ('SOUTH', 'West Virginia'),
        ('MIDWEST', 'Wisconsin'),
        ('FRONTIER', 'Wyoming')], validators=[DataRequired()])

    icyfire_team = SelectField('What is the name of your team?', choices=[
        ('00', 'Not applicable. I am a Region Lead.'),
        ('ALPHA', 'Team Alpha'),
        ('BRAVO', 'Team Bravo'),
        ('CHARLIE', 'Team Charlie'),
        ('DELTA', 'Team Delta'),
        ('ECHO', 'Team Echo'),
        ('FOXTROT', 'Team Foxtrot'),
        ('GOLF', 'Team Golf'),
        ('HOTEL', 'Team Hotel'),
        ('INDIGO', 'Team Indigo'),
        ('JULIET', 'Team Juliet')], validators=[DataRequired()])

    icyfire_agent = SelectField("What is your agent number?", choices=[
        ('00', 'Not applicable. I am a Team Lead.'),
        ('01', '1'),
        ('02', '2'),
        ('03', '3'),
        ('04', '4'),
        ('05', '5'),
        ('06', '6'),
        ('07', '7'),
        ('08', '8'),
        ('09', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('15', '15')], validators=[DataRequired()])

    first_name = StringField('First name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last name', validators=[DataRequired(), Length(max=50)])
    phone_number = StringField('Phone number', validators=[DataRequired(), Length(min=10, max=10), phone_check])
    email = StringField('IcyFire email', validators=[DataRequired(), Email(), Length(max=120), icyfire_email_check])
    password = PasswordField('Password (8 characters minimum)', validators=[DataRequired(), Length(min=8)])
    verify_password = PasswordField('Verify password', validators=[DataRequired(), password_check])
    submit = SubmitField('Register')

    def validate_email(self, email):
        '''
        If an account already exists with that email address, this check raises a ValidationError.
        '''
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
    
    def validate_crta(self, icyfire_region, icyfire_team, icyfire_agent):
        '''
        If an account already exists with that CRTA code, this check raises a ValidationError.
        '''
        crta = 'USA-' + icyfire_region.data + '-' + icyfire_team.data + '-' + icyfire_agent.data
        icyfire_crta = User.query.filter_by(icyfire_crta=crta).first()
        if icyfire_crta is not None:
            raise ValidationError('A user already exists with that CRTA code. Please contact your administrator.')


class ShortTextPostForm(FlaskForm):
    '''
    A form for creating and editing short text posts.
    [title]                 : Optional title for Tumblr and Reddit.
    [body]                  : Post body.
    [tags]                  : Optional tags in a comma-separated list. Converted to hashtags on Facebook, Twitter and LinkedIn, and tags on Tumblr.
    [link_url]              : Optional URL to an external resource.
    [is_facebook]           : Post to Facebook?
    [is_twitter]            : Post to Twitter?
    [is_tumblr]             : Post to Tumblr?
    [is_reddit]             : Post to Reddit?
    [is_linkedin]           : Post as a LinkedIn status?
    '''
    title = StringField('Title')
    body = TextAreaField('Body', validators=[DataRequired()])
    tags = StringField('Tags (comma-separated list)')
    link_url = StringField('Link URL')
    is_facebook = BooleanField('Post to Facebook (limit: 63,206 characters)')
    is_twitter = BooleanField('Post to Twitter (limit: 280 characters)')
    is_tumblr = BooleanField('Post to Tumblr')
    is_reddit = BooleanField('Post to Reddit (title limit: 300 characters)')
    is_linkedin = BooleanField('Post to LinkedIn (limit: 700 characters)')
    submit = SubmitField('Done')

    def check_facebook(self, body, tags, link_url, is_facebook):
        '''
        If `is_facebook` is True, this checks that...
            - ...Facebook OAuth information is not blank.
            - ...the overall length of the post is not more than 63,206 characters.
        '''
        if is_facebook is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            facebook_token = domain.facebook_token
            if facebook_token is None:
                raise ValidationError('FACEBOOK: Please make sure your account is authenticated before trying to post.')
            elif len(body.data) + len(tags.data) + len(link_url.data) > 63206:
                raise ValidationError("FACEBOOK: Post body length can't be longer than 63,206 characters.")

    def check_twitter(self, body, link_url, tags, is_twitter):
        '''
        If `is_twitter` is True, this checks that...
            - ...Twitter OAuth information is not blank.
            - ...the total length of the post (body + tags + URL) is not over 280 characters.
        '''
        if is_twitter is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            twitter_token = domain.twitter_token
            twitter_secret = domain.twitter_secret
            if twitter_token is None or twitter_secret is None:
                raise ValidationError('TWIITER: Please make sure your account is authenticated before trying to post.')
            elif len(body.data) > 280:
                raise ValidationError("TWITTER: Post body length can't be longer than 280 characters.")
            elif link_url is not None and tags is not None and len(body.data) + len(tags.data) + 23 > 280:
                raise ValidationError('TWITTER: The total length (post body, tags, and link) is longer than 280 characters.')
            elif link_url is not None and tags is None and len(body.data) + 23 > 280:
                raise ValidationError('TWITTER: The total length (post body and URL) is too long. Try shortening the post or getting rid of the link.')
            elif link_url is None and tags is not None and len(body.data) + len(tags.data) > 280:
                raise ValidationError('TWITTER: The total length (post body and tags) is too long. Try shortening the post or getting rid of some tags.')
    
    def check_tumblr(self, is_tumblr):
        '''
        If `is_tumblr` is True, this checks that the Tumblr OAuth information is not blank.
        '''
        if is_tumblr is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            tumblr_token = domain.tumblr_token
            tumblr_secret = domain.tumblr_token
            tumblr_blog_name = domain.tumblr_blog_name
            if tumblr_token is None or tumblr_secret is None or tumblr_blog_name is None:
                raise ValidationError('TUMBLR: Please make sure your account is authenticated before trying to post.')
    
    def check_reddit(self, title, is_reddit, link_url, body):
        '''
        If `is_reddit` is True, this checks that...
            - ...Reddit OAuth information is not blank.
            - ...the title is not longer than 300 characters.
        '''
        if is_reddit is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            reddit_username = domain.reddit_username
            reddit_password = domain.reddit_password
            reddit_subreddit = domain.reddit_subreddit
            if reddit_username is None or reddit_password is None or reddit_subreddit is None:
                raise ValidationError('REDDIT: Please make sure your account is authenticated before trying to post.')
            elif len(title.data) > 300:
                raise ValidationError("REDDIT: Titles can't be longer than 300 characters.")
    
    def check_linkedin_status(self, is_linkedin_status, body, link_url):
        '''
        If `is_linkedin_status` is True, this checks that...
            - ...LinkedIn OAuth information is not blank.
            - ...the post (body + tags + URL) is not more than 700 characters.
        '''
        if is_linkedin_status is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            linkedin_author = domain.linkedin_author
            linkedin_token = domain.linkedin_token
            linkedin_secret = domain.linkedin_secret
            if linkedin_author is None or linkedin_token is None or linkedin_secret is None:
                raise ValidationError('LINKEDIN: Please make sure your account is authenticated before trying to post.')
            elif len(body.data) > 700:
                raise ValidationError("LINKEDIN: Posts can't be longer than 700 characters.")
            elif link_url is not None and len(body.data) + len(link_url.data) > 700:
                raise ValidationError("LINKEDIN: The total length (body and URL) is too long. Try shortening the post or getting rid of the link.")


class LongTextPostForm(FlaskForm):
    '''
    A form for creating and editing long articles.
    [title]                 : Optional title for Tumblr, Reddit, and LinkedIn.
    [body]                  : Post body.
    [tags]                  : Optional tags in a comma-separated list. Converted to hashtags on Facebook, Twitter and LinkedIn, and tags on Tumblr.
    [is_facebook]           : Post to Facebook?
    [is_tumblr]             : Post to Tumblr?
    [is_reddit]             : Post to Reddit?
    [is_linkedin]           : Post as a LinkedIn article?
    '''
    title = StringField('Title')
    body = TextAreaField('Body', validators=[DataRequired()])
    tags = StringField('Tags (comma-separated list)')
    is_facebook = BooleanField('Post to Facebook (limit: 63,206 characters)')
    is_tumblr = BooleanField('Post to Tumblr')
    is_reddit = BooleanField('Post to Reddit (title limit: 300 characters)')
    is_linkedin = BooleanField('Post to LinkedIn (limit: 120,000 characters)')
    submit = SubmitField('Done')

    def check_facebook(self, body, is_facebook, tags):
        '''
        If `is_facebook` is True, this checks that...
            - ...Facebook OAuth information is not blank.
            - ...the total post length is not longer than 63,206 characters.
        '''
        if is_facebook is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            facebook_token = domain.facebook_token
            if facebook_token is None:
                raise ValidationError('FACEBOOK: Please make sure your account is authenticated before trying to post.')
            elif len(body.data) + len(tags.data) > 63206:
                raise ValidationError("FACEBOOK: Post length can't be longer than 63,206 characters.")
    
    def check_tumblr(self, is_tumblr):
        '''
        If `is_tumblr` is True, this checks that the Tumblr OAuth information is not blank.
        '''
        if is_tumblr is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            tumblr_token = domain.tumblr_token
            tumblr_secret = domain.tumblr_token
            tumblr_blog_name = domain.tumblr_blog_name
            if tumblr_token is None or tumblr_secret is None or tumblr_blog_name is None:
                raise ValidationError('TUMBLR: Please make sure your account is authenticated before trying to post.')

    def check_reddit(self, title, is_reddit):
        '''
        If `is_reddit` is True, this checks that...
            - ...Reddit OAuth information is not blank.
            - ...the title isn't longer than 300 characters.
        '''
        if is_reddit is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            reddit_username = domain.reddit_username
            reddit_password = domain.reddit_password
            reddit_subreddit = domain.reddit_subreddit
            if reddit_username is None or reddit_password is None or reddit_subreddit is None:
                raise ValidationError('REDDIT: Please make sure your account is authenticated before trying to post.')
            elif len(title.data) > 300:
                raise ValidationError("REDDIT: Titles can't be longer than 300 characters.")

    def check_linkedin_article(self, is_linkedin_article, body, tags):
        '''
        If `is_linkedin_article` is True, this checks that...
            - ...LinkedIn OAuth information is not blank.
            - ...the total length of the article (body + tags) is not longer than 120,000 characters.
        '''
        if is_linkedin_article is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            linkedin_author = domain.linkedin_author
            linkedin_token = domain.linkedin_token
            linkedin_secret = domain.linkedin_secret
            if linkedin_author is None or linkedin_token is None or linkedin_secret is None:
                raise ValidationError('LINKEDIN: Please make sure your account is authenticated before trying to post.')
            elif len(body.data) + len(tags.data) > 120000:
                raise ValidationError("LINKEDIN: Posts can't be longer than 120,000 characters.")


class ImagePostForm(FlaskForm):
    '''
    A form for creating and editing image posts.
    [title]         : Optional title for Tumblr and Reddit.
    [image]         : Image file upload (png, jpg, jpeg).
    [caption]       : Optional caption or description for the image.
    [tags]          : Optional tags in a comma-separated list. Converted to hashtags on Facebook, Twitter and LinkedIn, and tags on Tumblr.
    [is_facebook]   : Post to Facebook?
    [is_twitter]    : Post to Twitter?
    [is_tumblr]     : Post to Tumblr?
    [is_reddit]     : Post to Reddit?
    [is_linkedin]   : Post to LinkedIn?
    '''
    title = StringField('Title')
    image = FileField('Image file (.png, .jpg, .jpeg)', validators=[FileRequired(), FileAllowed(['png', 'jpg', 'jpeg'], 'Image files only!')])
    caption = StringField('Caption')
    tags = StringField('Tags (comma-separated list)')
    is_facebook = BooleanField('Post to Facebook (limit: 63,206 characters)')
    is_twitter = BooleanField('Post to Twitter (limit: 280 characters)')
    is_tumblr = BooleanField('Post to Tumblr')
    is_reddit = BooleanField('Post to Reddit')
    is_linkedin = BooleanField('Post to LinkedIn (limit: 700 characters)')
    submit = SubmitField('Done')

    def check_facebook(self, caption, is_facebook):
        '''
        If `is_facebook` is True, then this checks that...
            - ...Facebook OAuth information is not blank.
            - ...the post (caption + tags) is not longer than 63,206 characters.
        '''
        if is_facebook is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            facebook_token = domain.facebook_token
            if facebook_token is None:
                raise ValidationError('FACEBOOK: Please make sure your account is authenticated before trying to post.')
            elif len(caption.data) + len(tags.data) > 63206:
                raise ValidationError("FACEBOOK: Captions can't be longer than 63,206 characters.")

    def check_twitter(self, caption, tags, is_twitter):
        '''
        If `is_twitter` is True, then this checks that...
            - ...Twitter OAuth information is not blank.
            - ...the post (caption + tags) is not longer than 280 characters.
        '''
        if is_twitter is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            twitter_token = domain.twitter_token
            twitter_secret = domain.twitter_secret
            if twitter_token is None or twitter_secret is None:
                raise ValidationError('TWIITER: Please make sure your account is authenticated before trying to post.')
            elif len(caption.data) + len(tags.data) > 280:
                raise ValidationError("TWITTER: Caption can't be longer than 280 characters.")

    def check_tumblr(self, is_tumblr):
        '''
        If `is_tumblr` is True, then this checks that the Tumblr OAuth information is not blank.
        '''
        if is_tumblr is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            tumblr_token = domain.tumblr_token
            tumblr_secret = domain.tumblr_token
            tumblr_blog_name = domain.tumblr_blog_name
            if tumblr_token is None or tumblr_secret is None or tumblr_blog_name is None:
                raise ValidationError('TUMBLR: Please make sure your account is authenticated before trying to post.')

    def check_reddit(self, title, is_reddit):
        '''
        If `is_reddit` is True, then this checks that...
            - ...Reddit OAuth information is not blank.
            - ...the title is not longer than 300 characters.
        '''
        if is_reddit is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            reddit_username = domain.reddit_username
            reddit_password = domain.reddit_password
            reddit_subreddit = domain.reddit_subreddit
            if reddit_username is None or reddit_password is None or reddit_subreddit is None:
                raise ValidationError('REDDIT: Please make sure your account is authenticated before trying to post.')
            elif len(title.data) > 300:
                raise ValidationError("REDDIT: Titles can't be longer than 300 characters.")

    def check_linkedin(self, is_linkedin, caption, tags):
        '''
        If `is_linkedin` is True, then this checks that...
            - ...LinkedIn OAuth information is not blank.
            - ...the post (caption + tags) is not longer than 700 characters.
        '''
        if is_linkedin_article is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            linkedin_author = domain.linkedin_author
            linkedin_token = domain.linkedin_token
            linkedin_secret = domain.linkedin_secret
            if linkedin_author is None or linkedin_token is None or linkedin_secret is None:
                raise ValidationError('LINKEDIN: Please make sure your account is authenticated before trying to post.')
            elif len(caption.data) + len(tags.data) > 700:
                raise ValidationError("LINKEDIN: Captions can't be longer than 700 characters.")


class VideoPostForm(FlaskForm):
    '''
    A form for creating and editing video posts.
    [title]         : Optional title for Tumblr, Reddit, and YouTube.
    [caption]       : Optional description of the video.
    [video]         : Video file upload (avi, flv, wmv, mov, mp4).
    [tags]          : Optional tags in a comma-separated list. Converted to hashtags on Facebook, Twitter and LinkedIn, and tags on Tumblr.
    [category]      : Video category (required for YouTube).
    [is_facebook]   : Post to Facebook?
    [is_twitter]    : Post to Twitter?
    [is_tumblr]     : Post to Tumblr?
    [is_reddit]     : Post to Reddit?
    [is_youtube]    : Post to YouTube?
    [is_linkedin]   : Post to LinkedIn?
    '''
    title = StringField('Title')
    caption = StringField('Caption')
    video = FileField('Video file (.avi, .flv, .wmv, .mov, .mp4)', validators=[DataRequired(), FileAllowed(['avi', 'flv', 'wmv', 'mov', 'mp4'], 'Video files only!')])
    tags = StringField('Tags (comma-separated list)')
    category = SelectField('YouTube category', choices=[
        ('0', 'Not uploading to YouTube'),
        ('1', 'Film & Animation'),
        ('2', 'Autos & Vehicles'),
        ('10', 'Music'),
        ('15', 'Pets & Animals'),
        ('17', 'Sports'),
        ('18', 'Short Movies'),
        ('19', 'Travel & Events'),
        ('20', 'Gaming'),
        ('21', 'Videoblogging'),
        ('22', 'People & Blogs'),
        ('23', 'Comedy'),
        ('24', 'Entertainment'),
        ('25', 'News & Politics'),
        ('26', 'Howto & Style'),
        ('27', 'Education'),
        ('28', 'Science & Technology'),
        ('29', 'Nonprofits & Activism'),
        ('30', 'Movies'),
        ('31', 'Anime/Animation'),
        ('32', 'Action/Adventure'),
        ('33', 'Classics'),
        ('34', 'Comedy'),
        ('35', 'Documentary'),
        ('36', 'Drama'),
        ('37', 'Family'),
        ('38', 'Foreign'),
        ('39', 'Horror'),
        ('40', 'Sci-Fi/Fantasy'),
        ('41', 'Thriller'),
        ('42', 'Shorts'),
        ('43', 'Shows'),
        ('44', 'Trailers')], 
        validators=[DataRequired()])
    is_facebook = BooleanField('Post to Facebook (4h time limit)')
    is_twitter = BooleanField('Post to Twitter (2m 20s time limit)')
    is_tumblr = BooleanField('Post to Tumblr (5m time limit)')
    is_reddit = BooleanField('Post to Reddit (15m time limit)')
    is_youtube = BooleanField('Post to YouTube (15m for non-verified accounts, 12h for verified accounts')
    is_linkedin = BooleanField('Post to LinkedIn (10m time limit)')
    submit = SubmitField('Done')

    def check_facebook(self, is_facebook, caption, tags):
        '''
        If `is_facebook` is True, then this checks that...
            - ...Facebook OAuth information is not blank.
            - ...the post (caption + tags) length doesn't exceed 63,206 characters.
        '''
        if is_facebook is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            facebook_token = domain.facebook_token
            if facebook_token is None:
                raise ValidationError('FACEBOOK: Please make sure your account is authenticated before trying to post.')
            elif len(caption.data) + len(tags.data) > 63206:
                raise ValidationError("FACEBOOK: Captions can't be longer than 63,206 characters.")

    def check_twitter(self, is_twitter, caption, tags):
        '''
        If `is_twitter` is True, then this checks that...
            - ...Twitter OAuth information is not blank.
            - ...the post (caption + tags) length doesn't exceed 280 characters.
        '''
        if is_twitter is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            twitter_token = domain.twitter_token
            twitter_secret = domain.twitter_secret
            if twitter_token is None or twitter_secret is None:
                raise ValidationError('TWITTER: Please make sure your account is authenticated before trying to post.')
            elif len(caption.data) + len(tags.data) > 280:
                raise ValidationError("TWITTER: Caption and tags can't exceed 280 characters.")

    def check_tumblr(self, is_tumblr):
        '''
        If `is_tumblr` is True, then this checks that Tumblr OAuth information is not blank.
        '''
        if is_tumblr is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            tumblr_blog_name = domain.tumblr_blog_name
            tumblr_token = domain.tumblr_token
            tumblr_secret = domain.tumblr_secret
            if tumblr_blog_name is None or tumblr_token is None or tumblr_secret is None:
                raise ValidationError('TUMBLR: Please make sure your account is authenticated before trying to post.')

    def check_reddit(self, is_reddit, title):
        '''
        If `is_reddit` is True, then this checks that...
            - ...Reddit OAuth information is not blank.
            - ...the title isn't longer than 300 characters.
        '''
        if is_reddit is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            reddit_subreddit = domain.reddit_subreddit
            reddit_username = domain.reddit_username
            reddit_password = domain.reddit_password
            if reddit_username is None or reddit_password is None or reddit_secret is None:
                raise ValidationError('REDDIT: Please make sure your account is authenticated before trying to post.')
            elif len(title.data) > 300:
                raise ValidationError("REDDIT: Titles can't be more than 300 characters long.")

    def check_youtube(self, is_youtube, title, category, caption):
        '''
        If `is_youtube` is True, then this checks that...
            - ...YouTube OAuth information is not blank.
            - ...the title is not longer than 70 characters.
            - ...the caption (description) is not longer than 1,000 characters.
            - ...the category field is not blank.
        '''
        if is_youtube is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            youtube_refresh = domain.youtube_refresh
            youtube_access = domain.youtube_access
            if youtube_refresh is None or youtube_access is None:
                raise ValidationError('YOUTUBE: Please make sure your account is authenticated before trying to post.')
            elif len(title.data) > 70:
                raise ValidationError("YOUTUBE: Titles can't be more than 70 characters long.")
            elif len(caption.data) > 1000:
                raise ValidationError("YOUTUBE: Caption can't be more than 1,000 characters long.")
            elif category.data == '0':
                raise ValidationError("YOUTUBE: Please specify a category.")

    def check_linkedin(self, is_linkedin, caption):
        '''
        If `is_linkedin` is True, this checks that...
            - ...LinkedIn OAuth information is not blank.
            - ...the caption is not longer than 700 characters.
        '''
        if is_linkedin is True:
            domain = Domain.query.filter_by(id=current_user.domain_id).first()
            linkedin_token = domain.linkedin_token
            linkedin_secret = domain.linkedin_secret
            if linkedin_token is None or linkedin_secret is None:
                raise ValidationError('LINKEDIN: Please make sure your account is authenticated before trying to post.')
            elif len(caption.data) > 700:
                raise ValidationError("LINKEDIN: Caption can't be more than 700 characters long.")

class SaleForm(FlaskForm):
    client_name = StringField('Client name', validators=[DataRequired(), Length(max=100)])
    client_street_address = StringField('Street address', validators=[DataRequired(), Length(max=100)])
    client_city = StringField('City', validators=[DataRequired(), Length(max=60)])
    client_state = SelectField('State', choices=[
        ('Alabama','Alabama'),
        ('Alaska', 'Alaska'),
        ('Arizona', 'Arizona'),
        ('Arkansas', 'Arkansas'),
        ('California', 'California'),
        ('Colorado', 'Colorado'),
        ('Connecticut', 'Connecticut'),
        ('District of Columbia', 'District of Columbia'),
        ('Delaware', 'Delaware'),
        ('Florida', 'Florida'),
        ('Georgia', 'Georgia'),
        ('Hawaii', 'Hawaii'),
        ('Idaho', 'Idaho'),
        ('Illinois', 'Illinois'),
        ('Indiana', 'Indiana'),
        ('Iowa', 'Iowa'),
        ('Kansas', 'Kansas'),
        ('Kentucky', 'Kentucky'),
        ('Louisiana', 'Louisiana'),
        ('Maine', 'Maine'),
        ('Maryland', 'Maryland'),
        ('Massachusetts', 'Massachusetts'),
        ('Michigan', 'Michigan'),
        ('Minnesota', 'Minnesota'),
        ('Mississippi', 'Mississippi'),
        ('Missouri', 'Missouri'),
        ('Nebraska', 'Nebraska'),
        ('Nevada', 'Nevada'),
        ('New Jersey', 'New Jersey'),
        ('New Mexico', 'New Mexico'),
        ('New York', 'New York'),
        ('North Carolina', 'North Carolina'),
        ('North Dakota', 'North Dakota'),
        ('Ohio', 'Ohio'),
        ('Oklahoma', 'Oklahoma'),
        ('Pennsylvania', 'Pennsylvania'),
        ('Rhode Island', 'Rhode Island'),
        ('South Carolina', 'South Carolina'),
        ('South Dakota', 'South Dakota'),
        ('Tennessee', 'Tennessee'),
        ('Texas', 'Texas'),
        ('Utah', 'Utah'),
        ('Vermont', 'Vermont'),
        ('Virginia', 'Virginia'),
        ('Washington', 'Washington'),
        ('West Virginia', 'West Virginia'),
        ('Wisconsin', 'Wisconsin'),
        ('Wyoming', 'Wyoming')
    ],
    validators=[DataRequired(), Length(max=50)])
    client_zip = StringField('ZIP code', validators=[DataRequired(), Length(max=15)])
    client_phone_number = StringField('Contact phone number', validators=[DataRequired(), Length(min=10, max=10), phone_check])
    client_email = StringField('Contact email', validators=[DataRequired(), Email(), Length(max=120)])
    quantity = StringField('Quantity sold', validators=[DataRequired(), phone_check])
    submit = SubmitField('Submit')

class GenerateIcaForm(FlaskForm):
    contractor_type = SelectField('Contractor type', choices=[
        ('agent', 'Agent'),
        ('team_lead', 'Team lead'),
        ('region_lead', 'Region lead')
    ], validators=[DataRequired()])
    first_name = StringField('First name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last name', validators=[DataRequired(), Length(max=50)])
    street_address = StringField('Mailing address', validators=[DataRequired(), Length(max=35)])
    city = StringField('City', validators=[DataRequired(), Length(max=35)])
    state = StringField('State', validators=[DataRequired(), Length(max=15)])
    zip_code = StringField('ZIP code', validators=[DataRequired(), Length(max=9)])
    submit = SubmitField('Generate ICA')