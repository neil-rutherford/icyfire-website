from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from app.models import FacebookPost, TwitterPost, TumblrPost, RedditPost, Sentry, TimeSlot, FacebookCred, TwitterCred, TumblrCred, RedditCred
from app import db
from app.api import bp

# HELPER FUNCTION
def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

def make_error(endpoint, status, error_details, code):
    return jsonify(endpoint=endpoint, status=status, error_details=error_details, utc_timestamp=datetime.utcnow(), ip_address=request.remote_addr), code


# READ API
# TESTED: GOOD FUNCTIONALITY
@bp.route('/api/_r/<timeslot_id>/auth=<read_token>&<cred_token>&<server_id>')
def read(timeslot_id, read_token, cred_token, server_id):

    if read_token == os.environ['READ_TOKEN'] and cred_token == os.environ['CRED_TOKEN'] and server_id is not None:

        timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()

        if timeslot is None:
            make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read', status_code=400, status_message='{}|{}'.format(timeslot_id, server_id))
            return make_error(endpoint='api/_r', status='400 Bad Request', error_details='ERROR: Malformed request; timeslot not found.', code=400)
        
        domain_id = timeslot.domain_id

        if timeslot.facebook_cred_id is not None:
            cred = FacebookCred.query.filter_by(id=timeslot.facebook_cred_id).first()
            post = FacebookPost.query.filter_by(cred_id=cred.id).order_by(FacebookPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='facebook|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_r/facebook', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='facebook|{}|{}'.format(cred.id, server_id))
                return jsonify(platform='facebook', access_token=cred.access_token, post_type=post.post_type, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags), 200

        elif timeslot.twitter_cred_id is not None:
            cred = TwitterCred.query.filter_by(id=timeslot.twitter_cred_id).first()
            post = TwitterPost.query.filter_by(cred_id=cred.id).order_by(TwitterPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='twitter|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_r/twitter', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='twitter|{}|{}'.format(cred.id, server_id))
                return jsonify(platform='twitter', consumer_key=cred.consumer_key, consumer_secret=cred.consumer_secret, access_token_key=cred.access_token_key, access_token_secret=cred.access_token_secret, post_type=post.post_type, body=post.body, link_url=post.link_url, multimedia_url=post.multimedia_url, tags=post.tags), 200

        elif timeslot.tumblr_cred_id is not None:
            cred = TumblrCred.query.filter_by(id=timeslot.tumblr_cred_id).first()
            post = TumblrPost.query.filter_by(cred_id=cred.id).order_by(TumblrPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='tumblr|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_r/tumblr', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=200, status_message='tumblr|{}|{}'.format(cred.id, server_id))
                return jsonify(platform='tumblr', consumer_key=cred.consumer_key, consumer_secret=cred.consumer_secret, oauth_token=cred.oauth_token, oauth_secret=cred.oauth_secret, blog_name=cred.blog_name, post_type=post.post_type, title=post.title, body=post.body, tags=post.tags, link_url=post.link_url, multimedia_url=post.multimedia_url, caption=post.caption)

        elif timeslot.reddit_cred_id is not None:
            cred = RedditCred.query.filter_by(id=timeslot.reddit_cred_id).first()
            post = RedditPost.query.filter_by(cred_id=cred.id).order_by(RedditPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.read', status_code=404, status_message='reddit|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_r/reddit', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                return jsonify(platform='reddit', client_id=cred.client_id, client_secret=cred.client_secret, user_agent=cred.user_agent, username=cred.username, password=cred.password, post_type=post.post_type, title=post.title, body=post.body, link_url=post.link_url, image_url=post.image_url, video_url=post.video_url)
        
        else:
            make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read', status_code=218, status_message='{}'.format(server_id))
            return make_error(endpoint='api/_r', status='218 This Is Fine', error_details='INFO: Timeslot is empty.', code=218)

    else:
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read', status_code=403, status_message='{}|{}|{}'.format(read_token, cred_token, server_id))
        return make_error(endpoint='api/_r', status='403 Forbidden', error_details='ERROR: Authentication token(s) incorrect.', code=403)


# DELETE API
# TESTED: GOOD FUNCTIONALITY
@bp.route('/api/_d/<timeslot_id>/auth=<read_token>&<delete_token>&<server_id>')
def delete(timeslot_id, read_token, delete_token, server_id):

    if read_token == os.environ['READ_TOKEN'] and delete_token == os.environ['DELETE_TOKEN'] and server_id is not None:
        
        timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()

        if timeslot is None:
            make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.delete', status_code=400, status_message='{}|{}'.format(timeslot_id, server_id))
            return make_error(endpoint='api/_d', status='400 Bad Request', error_details='ERROR: Malformed request; timeslot not found.', code=400)
        
        domain_id = timeslot.domain_id

        if timeslot.facebook_cred_id is not None:
            cred = FacebookCred.query.filter_by(id=timeslot.facebook_cred_id).first()
            post = FacebookPost.query.filter_by(cred_id=cred.id).order_by(FacebookPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='facebook|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_d/facebook', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='facebook|{}|{}'.format(cred.id, server_id))
                db.session.delete(post)
                db.session.commit()
                return make_error(endpoint='api/_d/facebook', status='204 No Content', error_details='SUCCESS: Post deleted.', code=204)
        
        elif timeslot.twitter_cred_id is not None:
            cred = TwitterCred.query.filter_by(id=timeslot.twitter_cred_id).first()
            post = TwitterPost.query.filter_by(cred_id=cred.id).order_by(TwitterPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='twitter|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_d/twitter', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='twitter|{}|{}'.format(cred.id, server_id))
                db.session.delete(post)
                db.session.commit()
                return make_error(endpoint='api/_d/twitter', status='204 No Content', error_details='SUCCESS: Post deleted.', code=204)
        
        elif timeslot.tumblr_cred_id is not None:
            cred = TumblrCred.query.filter_by(id=timeslot.tumblr_cred_id).first()
            post = TumblrPost.query.filter_by(cred_id=cred.id).order_by(TumblrPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='tumblr|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_d/tumblr', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='tumblr|{}|{}'.format(cred.id, server_id))
                db.session.delete(post)
                db.session.commit()
                return make_error(endpoint='api/_d/tumblr', status='204 No Content', error_details='SUCCESS: Post deleted.', code=204)
        
        elif timeslot.reddit_cred_id is not None:
            cred = RedditCred.query.filter_by(id=timeslot.reddit_cred_id).first()
            post = RedditPost.query.filter_by(cred_id=cred.id).order_by(RedditPost.timestamp.asc()).first()

            if post is None:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=404, status_message='reddit|{}|{}'.format(cred.id, server_id))
                return make_error(endpoint='api/_d/reddit', status='404 Not Found', error_details='ERROR: Queue is empty.', code=404)
            else:
                make_sentry(user_id=None, domain_id=int(domain_id), ip_address=request.remote_addr, endpoint='api.delete', status_code=204, status_message='reddit|{}|{}'.format(cred.id, server_id))
                db.session.delete(post)
                db.session.commit()
                return make_error(endpoint='api/_d/reddit', status='204 No Content', error_details='SUCCESS: Post deleted.', code=204)
        
        else:
            make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.delete', status_code=218, status_message='{}'.format(server_id))
            return make_error(endpoint='api/_d', status='218 This Is Fine', error_details='INFO: Timeslot is empty.', code=218)

    else:
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.delete', status_code=403, status_message='{}|{}|{}'.format(read_token, delete_token, server_id))
        return make_error(endpoint='api/_d', status='403 Forbidden', error_details='ERROR: Authentication token(s) incorrect.', code=403)


# SECURITY API
# TESTED: GOOD FUNCTIONALITY
@bp.route('/api/_rs/auth=<read_token>&<security_token>/query=<argument>:<data>')
def read_sentry(read_token, security_token, argument, data):

    if read_token == os.environ['READ_TOKEN'] and security_token == os.environ['SECURITY_TOKEN']:

        if argument == 'sentry_id':
            try:
                data = int(data)
                results = [Sentry.query.filter_by(id=data).first()]
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='sentry_id|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='sentry_id|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'timestamp':
            try:
                data = int(data)
                limit = datetime.utcnow() - timedelta(days=data)
                results = Sentry.query.filter(Sentry.timestamp >= limit).all()
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='timestamp|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='timestamp|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'ip_address':
            try:
                data = str(data)
                results = Sentry.query.filter_by(ip_address=data).all()
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='ip_address|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='ip_address|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'user_id':
            try:
                data = int(data)
                results = Sentry.query.filter_by(user_id=data).all()
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='user_id|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='user_id|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'domain_id':
            try:
                data = int(data)
                results = Sentry.query.filter_by(domain_id=data).all()
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='domain_id|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='domain_id|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'endpoint':
            try:
                data = str(data)
                results = Sentry.query.filter_by(endpoint=data).all()
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='endpoint|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='endpoint|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'endpoint_prefix':
            try:
                data = str(data)
                everything = Sentry.query.all()
                json_list = []
                for thing in everything:
                    if thing.endpoint.split('.')[0] == data:
                        json_dict = {'id': thing.id, 'timestamp': thing.timestamp, 'ip_address': thing.ip_address, 'user_id': thing.user_id, 'domain_id': thing.domain_id, 'endpoint': thing.endpoint, 'status_code': thing.status_code, 'status_message': thing.status_message, 'flag': thing.flag}
                        json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='endpoint_prefix|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='endpoint_prefix|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'status_code':
            try:
                data = int(data)
                results = Sentry.query.filter_by(status_code=data).all()
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='status_code|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='status_code|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        elif argument == 'flag':
            try:
                data = str(data)
                results = Sentry.query.filter_by(flag=data).all()
                json_list = []
                for result in results:
                    json_dict = {'id': result.id, 'timestamp': result.timestamp, 'ip_address': result.ip_address, 'user_id': result.user_id, 'domain_id': result.domain_id, 'endpoint': result.endpoint, 'status_code': result.status_code, 'status_message': result.status_message, 'flag': result.flag}
                    json_list.append(json_dict)
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=200, status_message='flag|{}'.format(data))
                return jsonify(json_list), 200
            except:
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=404, status_message='flag|{}'.format(data))
                return make_error(endpoint='api/_rs', status='404 Data Not Found', error_details='ERROR: No results found.', code=404)

        else:
            make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=400, status_message='{}'.format(argument))
            return make_error(endpoint='api/_rs', status='400 Bad Request', error_details='ERROR: Malformed request; argument not found.', code=400)

    else:
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='api.read_sentry', status_code=403, status_message='{}|{}'.format(read_token, security_token))
        return make_error(endpoint='api/_rs', status='403 Forbidden', error_details='ERROR: Authentication token(s) incorrect.', code=403)