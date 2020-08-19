import os
from os.path import join, dirname
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '2ec476c50a43963a551a8d73515f959d8d703216d24ba7821cca6431c8fbe8aba2ff0b6f0b26f4a76db2a244398c4f00f48f3c4d623a41dc52d210a34e0fbe78'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(S3_BUCKET)
    ADMINS = ['neilrutherford@icy-fire.com']
    TRAP_HTTP_EXCEPTIONS = True
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')