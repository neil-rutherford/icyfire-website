from app import create_app, db
from app.models import Domain, User, FacebookPost, TwitterPost, TumblrPost, RedditPost, YoutubePost, LinkedinPost, Sentry, CountryLead, RegionLead, TeamLead, Agent

app = create_app()
#cli.register(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Domain': Domain, 'FacebookPost': FacebookPost, 'TwitterPost': TwitterPost, 'TumblrPost': TumblrPost, 'RedditPost': RedditPost, 'YoutubePost': YoutubePost, 'LinkedinPost': LinkedinPost, 'Sentry': Sentry, 'CountryLead': CountryLead, 'RegionLead': RegionLead, 'TeamLead': TeamLead, 'Agent': Agent}
