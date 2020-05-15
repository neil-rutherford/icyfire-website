from app import app, db
from app.models import Domain, User, FacebookPost, TwitterPost, TumblrPost, RedditPost, YoutubePost, LinkedinPost, Ewok, Sentry

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Domain': Domain, 'FacebookPost': FacebookPost, 'TwitterPost': TwitterPost, 'TumblrPost': TumblrPost, 'RedditPost': RedditPost, 'YoutubePost': YoutubePost, 'LinkedinPost': LinkedinPost, 'Ewok': Ewok, 'Sentry': Sentry}
