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


class ShortTextForm(FlaskForm):
    title = StringField('Title')
    body = TextAreaField('Body', validators=[DataRequired()])
    tags = StringField('Tags (comma-separated list)')
    link_url = StringField('Link URL')
    submit = SubmitField('Done')


class LongTextForm(FlaskForm):
    title = StringField('Title')
    body = TextAreaField('Body', validators=[DataRequired()])
    tags = StringField('Tags (comma-separated list)')
    link_url = StringField('Link URL')
    submit = SubmitField('Done')


class ImageForm(FlaskForm):
    title = StringField('Title')
    image = FileField('Image file (.png, .jpg, .jpeg)', validators=[FileRequired(), FileAllowed(['png', 'jpg', 'jpeg'], 'Image files only!')])
    caption = TextAreaField('Caption')
    tags = StringField('Tags (comma-separated list)')
    link_url = StringField('Link URL')
    submit = SubmitField('Done')

class EditImageForm(FlaskForm):
    title = StringField('Title')
    image = FileField('New image file (.png, .jpg, .jpeg)', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Image files only!')])
    caption = TextAreaField('Caption')
    tags = StringField('Tags (comma-separated list)')
    link_url = StringField('Link URL')
    submit = SubmitField('Done')


class VideoForm(FlaskForm):
    title = StringField('Title')
    video = FileField('Video file (.avi, .flv, .wmv, .mov, .mp4)', validators=[FileRequired(), FileAllowed(['avi', 'flv', 'wmv', 'mov', 'mp4'], 'Video files only!')])
    caption = TextAreaField('Caption')
    tags = StringField('Tags (comma-separated list)')
    link_url = StringField('Link URL')
    submit = SubmitField('Done')

class EditVideoForm(FlaskForm):
    title = StringField('Title')
    video = FileField('New video file (.avi, .flv, .wmv, .mov, .mp4)', validators=[FileAllowed(['avi', 'flv', 'wmv', 'mov', 'mp4'], 'Video files only!')])
    caption = TextAreaField('Caption')
    tags = StringField('Tags (comma-separated list)')
    link_url = StringField('Link URL')
    submit = SubmitField('Done')

class TestForm(FlaskForm):
    image = FileField('New image file (.png, .jpg, .jpeg)', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Image files only!')])
    submit = SubmitField('Go')