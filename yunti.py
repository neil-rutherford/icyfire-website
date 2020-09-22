from app import create_app, db
from app.models import Domain, User, FacebookPost, FacebookCred, TwitterPost, TwitterCred, TumblrPost, TumblrCred, RedditPost, RedditCred, TimeSlot, Sentry, Partner #CountryLead, RegionLead, TeamLead, Agent

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Domain': Domain, 'FacebookPost': FacebookPost, 'FacebookCred': FacebookCred, 'TwitterPost': TwitterPost, 'TwitterCred': TwitterCred, 'TumblrPost': TumblrPost, 'TumblrCred': TumblrCred, 'RedditPost': RedditPost, 'RedditCred': RedditCred, 'TimeSlot': TimeSlot, 'Sentry': Sentry, 'Partner': Partner} #'CountryLead': CountryLead, 'RegionLead': RegionLead, 'TeamLead': TeamLead, 'Agent': Agent}
