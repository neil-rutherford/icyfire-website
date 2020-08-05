from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Length
from app.models import User, Domain, FacebookCred, TwitterCred, TumblrCred, RedditCred
from flask_login import current_user


def check_facebook(form, field):
    if field.data is True:
        if len(form.body.data) + len(form.tags.data) + len(form.link_url.data) > 63206:
            raise ValidationError("FACEBOOK: Post body length can't be longer than 63,206 characters.")


def check_twitter(form, field):
    if field.data is True:
        if len(form.body.data) > 280:
            raise ValidationError("TWITTER: Post body length can't be longer than 280 characters.")

        elif form.link_url is not None and form.tags is not None and len(form.body.data) + len(form.tags.data) + 23 > 280:
            raise ValidationError('TWITTER: The total length (post body, tags, and link) is longer than 280 characters.')

        elif form.link_url is not None and form.tags is None and len(form.body.data) + 23 > 280:
            raise ValidationError('TWITTER: The total length (post body and URL) is too long. Try shortening the post or getting rid of the link.')

        elif form.link_url is None and form.tags is not None and len(form.body.data) + len(form.tags.data) > 280:
            raise ValidationError('TWITTER: The total length (post body and tags) is too long. Try shortening the post or getting rid of some tags.')


def check_tumblr(form, field):
    if field.data is True:
        if form.title is None:
            raise ValidationError("TUMBLR: Title required for Tumblr posts.")


def check_reddit(form, field):
    if field.data is True:
        if form.title is None:
            raise ValidationError("REDDIT: Title required for Reddit posts.")

        elif len(form.title.data) > 300:
            raise ValidationError("REDDIT: Reddit titles can't be longer than 300 characters.")


def short_text_builder(obj=None):

    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    facebook_creds = FacebookCred.query.filter_by(domain_id=domain.id).all()
    twitter_creds = TwitterCred.query.filter_by(domain_id=domain.id).all()
    tumblr_creds = TumblrCred.query.filter_by(domain_id=domain.id).all()
    reddit_creds = RedditCred.query.filter_by(domain_id=domain.id).all()

    class ShortTextPostForm(FlaskForm):
        pass

    setattr(ShortTextPostForm, 'title', StringField('Title'))
    setattr(ShortTextPostForm, 'body', TextAreaField('Body', validators=[DataRequired()]))
    setattr(ShortTextPostForm, 'tags', StringField('Tags (comma-separated list)'))
    setattr(ShortTextPostForm, 'link_url', StringField('Link URL'))
    
    if len(facebook_creds) > 0:
        for (i, cred) in enumerate(facebook_creds):
            setattr(ShortTextPostForm, 'facebook_{}'.format(i), BooleanField('Post to {}', validators=[check_facebook]).format(cred.alias))

    if len(twitter_creds) > 0:
        for (i, cred) in enumerate(twitter_creds):
            setattr(ShortTextPostForm, 'twitter_{}'.format(i), BooleanField('Post to {}', validators=[check_twitter]).format(cred.alias))

    if len(tumblr_creds) > 0:
        for (i, cred) in enumerate(tumblr_creds):
            setattr(ShortTextPostForm, 'tumblr_{}'.format(i), BooleanField('Post to {}', validators=[check_tumblr]).format(cred.alias))

    if len(reddit_creds) > 0:
        for (i, cred) in enumerate(reddit_creds):
            setattr(ShortTextPostForm, 'reddit_{}'.format(i), BooleanField('Post to {}', validators=[check_reddit]).format(cred.alias))

    setattr(ShortTextPostForm, 'submit', SubmitField('Done'))
    return ShortTextPostForm(obj=obj)


def long_text_builder(obj=None):

    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    facebook_creds = FacebookCred.query.filter_by(domain_id=domain.id).all()
    tumblr_creds = TumblrCred.query.filter_by(domain_id=domain.id).all()
    reddit_creds = RedditCred.query.filter_by(domain_id=domain.id).all()

    class LongTextPostForm(FlaskForm):
        pass

    setattr(LongTextPostForm, 'title', StringField('Title'))
    setattr(LongTextPostForm, 'body', TextAreaField('Body', validators=[DataRequired()]))
    setattr(LongTextPostForm, 'tags', StringField('Tags (comma-separated list)'))

    if len(facebook_creds) > 0:
        for (i, cred) in enumerate(facebook_creds):
            setattr(LongTextPostForm, 'facebook_{}'.format(i), BooleanField('Post to {}', validators=[check_facebook]).format(cred.alias))

    if len(tumblr_creds) > 0:
        for (i, cred) in enumerate(tumblr_creds):
            setattr(LongTextPostForm, 'tumblr_{}'.format(i), BooleanField('Post to {}', validators=[check_tumblr]).format(cred.alias))

    if len(reddit_creds) > 0:
        for (i, cred) in enumerate(reddit_creds):
            setattr(LongTextPostForm, 'reddit_{}'.format(i), BooleanField('Post to {}', validators=[check_reddit]).format(cred.alias))

    setattr(LongTextPostForm, 'submit', SubmitField('Done'))
    return LongTextPostForm(obj=obj)


def image_builder(obj=None):

    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    facebook_creds = FacebookCred.query.filter_by(domain_id=domain.id).all()
    twitter_creds = TwitterCred.query.filter_by(domain_id=domain.id).all()
    tumblr_creds = TumblrCred.query.filter_by(domain_id=domain.id).all()
    reddit_creds = RedditCred.query.filter_by(domain_id=domain.id).all()

    class ImagePostForm(FlaskForm):
        pass

    setattr(ImagePostForm, 'title', StringField('Title'))
    setattr(ImagePostForm, 'image', FileField('Image file (.png, .jpg, .jpeg)', validators=[FileRequired(), FileAllowed(['png', 'jpg', 'jpeg'], 'Image files only!')]))
    setattr(ImagePostForm, 'caption', StringField('Caption'))
    setattr(ImagePostForm, 'tags', StringField('Tags (comma-separated list)'))

    if len(facebook_creds) > 0:
        for (i, cred) in enumerate(facebook_creds):
            setattr(ImagePostForm, 'facebook_{}'.format(i), BooleanField('Post to {}', validators=[check_facebook]).format(cred.alias))

    if len(twitter_creds) > 0:
        for (i, cred) in enumerate(twitter_creds):
            setattr(ImagePostForm, 'twitter_{}'.format(i), BooleanField('Post to {}', validators=[check_twitter]).format(cred.alias))

    if len(tumblr_creds) > 0:
        for (i, cred) in enumerate(tumblr_creds):
            setattr(ImagePostForm, 'tumblr_{}'.format(i), BooleanField('Post to {}', validators=[check_tumblr]).format(cred.alias))

    if len(reddit_creds) > 0:
        for (i, cred) in enumerate(reddit_creds):
            setattr(ImagePostForm, 'reddit_{}'.format(i), BooleanField('Post to {}', validators=[check_reddit]).format(cred.alias))

    setattr(ImagePostForm, 'submit', SubmitField('Done'))
    return ImagePostForm(obj=obj)


def video_builder(obj=None):

    domain = Domain.query.filter_by(id=current_user.domain_id).first()
    facebook_creds = FacebookCred.query.filter_by(domain_id=domain.id).all()
    twitter_creds = TwitterCred.query.filter_by(domain_id=domain.id).all()
    tumblr_creds = TumblrCred.query.filter_by(domain_id=domain.id).all()
    reddit_creds = RedditCred.query.filter_by(domain_id=domain.id).all()

    class VideoPostForm(FlaskForm):
        pass

    setattr(VideoPostForm, 'title', StringField('Title'))
    setattr(VideoPostForm, 'caption', StringField('Caption'))
    setattr(VideoPostForm, 'video', FileField('Video file (.avi, .flv, .wmv, .mov, .mp4)', validators=[DataRequired(), FileAllowed(['avi', 'flv', 'wmv', 'mov', 'mp4'], 'Video files only!')]))
    setattr(VideoPostForm, 'tags', StringField('Tags (comma-separated list)'))

    if len(facebook_creds) > 0:
        for (i, cred) in enumerate(facebook_creds):
            setattr(VideoPostForm, 'facebook_{}'.format(i), BooleanField('Post to {} (4 hour limit)', validators=[check_facebook]).format(cred.alias))

    if len(twitter_creds) > 0:
        for (i, cred) in enumerate(twitter_creds):
            setattr(VideoPostForm, 'twitter_{}'.format(i), BooleanField('Post to {} (2 minute 20 second limit)', validators=[check_twitter]).format(cred.alias))

    if len(tumblr_creds) > 0:
        for (i, cred) in enumerate(tumblr_creds):
            setattr(VideoPostForm, 'tumblr_{}'.format(i), BooleanField('Post to {} (5 minute limit)', validators=[check_tumblr]).format(cred.alias))

    if len(reddit_creds) > 0:
        for (i, cred) in enumerate(reddit_creds):
            setattr(VideoPostForm, 'reddit_{}'.format(i), BooleanField('Post to {} (15 minute limit)', validators=[check_reddit]).format(cred.alias))

    setattr(VideoPostForm, 'submit', SubmitField('Done'))
    return VideoPostForm(obj=obj)