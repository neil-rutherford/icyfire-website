from flask import request, jsonify
from datetime import datetime
from app.models import FacebookPost, TwitterPost, TumblrPost, RedditPost, YoutubePost, LinkedinPost, Sentry
from app import db
from app.api import bp

# HELPER FUNCTION
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id)
    db.session.add(activity)
    db.session.commit()

# READ API
@bp.route('/api/_r/<domain_id>/<platform>/auth=<read_token>', methods=['GET'])
def read(domain_id, platform, read_token):
    '''
    - Sentry logs:
        + 200 = accessed post (`status_message` = platform)
        + 404 = queue is empty; can't load the next post (`status_message` = platform)
        + 400 = bad request; can't find that platform (`status_message` = platform)
        + 403 = wrong read token (`status_message` = read token)
    - Assuming read token is valid, this uses the `domain_id` and `platform` arguments to build a list of posts in ascending time order (oldest first)
    - First post in queue is returned as a JSON object
    '''
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if str(read_token) == app.config['READ_TOKEN']:
        if str(platform) == 'facebook':
            post = FacebookPost.query.filter_by(domain_id=int(domain_id)).order_by(FacebookPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='facebook')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='Queue is empty.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='facebook')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags), 200
        elif str(platform) == 'twitter':
            post = TwitterPost.query.filter_by(domain_id=int(domain_id)).order_by(TwitterPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='twitter')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='Queue is empty.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='twitter')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags), 200
        elif str(platform) == 'tumblr':
            post = TumblrPost.query.filter_by(domain_id=int(domain_id)).order_by(TumblrPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='tumblr')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='Queue is empty.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='tumblr')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, title=post.title, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags, caption=post.caption), 200
        elif str(platform) == 'reddit':
            post = RedditPost.query.filter_by(domain_id=int(domain_id)).order_by(RedditPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='reddit')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='Queue is empty.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='reddit')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, title=post.title, body=post.body, link_url=post.link_url, image_url=post.image_url, video_url=post.video_url), 200
        elif str(platform) == 'youtube':
            post = YoutubePost.query.filter_by(domain_id=int(domain_id)).order_by(YoutubePost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='youtube')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='Queue is empty.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='youtube')
                return jsonify(timestamp=post.timestamp, multimedia_url=post.multimedia_url, title=post.title, caption=post.caption, tags=post.tags, category=post.category), 200
        elif str(platform) == 'linkedin':
            post = LinkedinPost.query.filter_by(domain_id=int(domain_id)).order_by(LinkedinPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='linkedin')
                return jsonify(endpoint='api/_r', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='Queue is empty.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='linkedin')
                return jsonify(post_type=post.post_type, timestamp=post.timestamp, title=post.title, body=post.body, caption=post.caption, multimedia_url=post.multimedia_url, link_url=post.link_url, tags=post.tags), 200
        else:
            make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=400, status_message='{}'.format(str(platform)))
            return jsonify(endpoint='api/_r', status='400 Bad Request', utc_timestamp=timestamp, ip_address=ip_address, error_details='Malformed request; platform not found.'), 400
    else:
        make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read'.format(platform), status_code=403, status_message='{}'.format(str(read_token)))
        return jsonify(endpoint='api/_r', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403

# DELETE API
@bp.route('/api/_d/<domain_id>/<platform>/auth=<read_token>&<delete_token>', methods=['GET'])
def delete(domain_id, platform, read_token, delete_token):
    '''
    - Sentry logs:
        + 204 = post deleted successfully (`status_message` = platform)
        + 404 = queue is empty; can't delete the next post (`status_message` = platform)
        + 400 = bad request; can't find that platform (`status_message` = platform)
        + 403 = permission denied; wrong read OR delete token (`status_message` = read|delete)
    - Since deleting is more sensitive than reading, two tokens are needed for this endpoint (read token AND delete token), which are both stored in config
    - Assuming both tokens are valid, this uses the `domain_id` and `platform` arguments to build a list of posts in ascending time order (oldest first)
    - First post in queue is deleted
    - This is intended to be used like: api.read => api.permission => publish post => api.delete => time.sleep(until next wake) => api.read => ...
    '''
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if str(read_token) == app.config['READ_TOKEN'] and str(delete_token) == app.config['DELETE_TOKEN']:
        if str(platform) == 'facebook':
            post = FacebookPost.query.filter_by(domain_id=int(domain_id)).order_by(FacebookPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='facebook')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='facebook')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'twitter':
            post = TwitterPost.query.filter_by(domain_id=int(domain_id)).order_by(TwitterPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='twitter')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='twitter')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'tumblr':
            post = TumblrPost.query.filter_by(domain_id=int(domain_id)).order_by(TumblrPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='tumblr')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='tumblr')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'reddit':
            post = RedditPost.query.filter_by(domain_id=int(domain_id)).order_by(RedditPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='reddit')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='reddit')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'youtube':
            post = YoutubePost.query.filter_by(domain_id=int(domain_id)).order_by(YoutubePost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='youtube')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='youtube')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        elif str(platform) == 'linkedin':
            post = LinkedinPost.query.filter_by(domain_id=int(domain_id)).order_by(LinkedinPost.timestamp.asc()).first()
            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='linkedin')
                return jsonify(endpoint='api/_d', status='404 Not Found', utc_timestamp=timestamp, ip_address=ip_address, error_details='No such post.'), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='linkedin')
                db.session.delete(post)
                db.session.commit()
                return jsonify(endpoint='api/_d', status='204 No Content', utc_timestamp=timestamp, ip_address=ip_address), 204
        else:
            make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=400, status_message='{}'.format(str(platform)))
            return jsonify(endpoint='api/_d', status='400 Bad Request', utc_timestamp=timestamp, ip_address=ip_address, error_details='Malformed request; platform not found.'), 400
    else:
        make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=403, status_message='{}|{}'.format(str(read_token), str(delete_token)))
        return jsonify(endpoint='api/_d', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403

# PERMISSION API
@bp.route('/api/_p/<domain_id>/<platform>/auth=<read_token>&<delete_token>&<permission_token>', methods=['GET'])
def permission(domain_id, platform, read_token, delete_token, permission_token):
    '''
    - Sentry logs:
        + 200 = ok; creds in json format (`status_message` = platform)
        + 400 = bad request; can't find that platform (`status_message` = platform)
        + 403 = permission denied; one or more tokens is incorrect (`status_message` = read|delete|permission)
        + 404 = not found; permissions don't exist?
    - Since permissions are the most sensitive, three tokens are needed for this endpoint (read token AND delete token AND permission token), which are all stored in config
    - Assuming all tokens are valid, this uses the `domain_id` and `platform` arguments to access the creds for that platform
    - Creds are returned as a JSON object
    - This is intended to be used like: api.read => api.permission => publish post => api.delete => time.sleep(until next wake) => api.read => ...
    '''
    timestamp = datetime.utcnow()
    ip_address = request.remote_addr
    if str(read_token) == app.config['READ_TOKEN'] and str(delete_token) == app.config['DELETE_TOKEN'] and str(permission_token) == app.config['PERMISSION_TOKEN']:
        domain = Domain.query.filter_by(id=int(domain_id)).first()
        if str(platform) == 'facebook':
            facebook_token = domain.facebook_token
            if facebook_token is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=404, status_message='facebook')
                return jsonify(endpoint='/api/_p/facebook', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=200, status_message='facebook')
                return jsonify(facebook_token=facebook_token), 200
        elif str(platform) == 'twitter':
            twitter_token = domain.twitter_token
            twitter_secret = domain.twitter_secret
            if twitter_token is None or twitter_secret is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=404, status_message='twitter')
                return jsonify(endpoint='/api/_p/twitter', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api/_p/{}/twitter'.format(domain_id), status_code=200, status_message='twitter')
                return jsonify(twitter_token=twitter_token, twitter_secret=twitter_secret), 200
        elif str(platform) == 'tumblr':
            tumblr_blog_name = domain.tumblr_blog_name
            tumblr_token = domain.tumblr_token
            tumblr_secret = domain.tumblr_secret
            if tumblr_blog_name is None or tumblr_token is None or tumblr_secret is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=404, status_message='tumblr')
                return jsonify(endpoint='/api/_p/tumblr', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=200, status_message='tumblr')
                return jsonify(tumblr_blog_name=tumblr_blog_name, tumblr_token=tumblr_token, tumblr_secret=tumblr_secret), 200
        elif str(platform) == 'reddit':
            reddit_subreddit = domain.reddit_subreddit
            reddit_username = domain.reddit_username
            reddit_password = domain.reddit_password
            if reddit_subreddit is None or reddit_username is None or reddit_password is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=404, status_message='reddit')
                return jsonify(endpoint='/api/_p/reddit', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=200, status_message='reddit')
                return jsonify(reddit_subreddit=reddit_subreddit, reddit_username=reddit_username, reddit_password=reddit_password), 200
        elif str(platform) == 'youtube':
            youtube_refresh = domain.youtube_refresh
            youtube_access = domain.youtube_access
            if youtube_refresh is None or youtube_access is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=404, status_message='youtube')
                return jsonify(endpoint='/api/_p/youtube', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=200, status_message='youtube')
                return jsonify(youtube_refresh=youtube_refresh, youtube_access=youtube_access), 200
        elif str(platform) == 'linkedin':
            linkedin_author = domain.linkedin_author
            linkedin_token = domain.linkedin_token
            linkedin_secret = domain.linkedin_secret
            if linkedin_author is None or linkedin_token is None or linkedin_secret is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=404, status_message='linkedin')
                return jsonify(endpoint='/api/_p/linkedin', status='404 Credential Not Found', utc_timestamp=timestamp, ip_address=ip_address), 404
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=200, status_message='linkedin')
                return jsonify(linkedin_author=linkedin_author, linkedin_token=linkedin_token, linkedin_secret=linkedin_secret), 200
        else:
            make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=400, status_message='{}'.format(str(platform)))
            return jsonify(endpoint='api/_d', status='400 Bad Request', utc_timestamp=timestamp, ip_address=ip_address, error_details='Malformed request; platform not found.'), 400
    else:
        make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.permission', status_code=403, status_message='{}/{}/{}'.format(str(read_token), str(delete_token), str(permission_token)))
        return jsonify(endpoint='api/_p', status='403 Forbidden', utc_timestamp=timestamp, ip_address=ip_address, error_details="You don't have permission to do that."), 403
