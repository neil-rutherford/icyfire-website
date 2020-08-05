from flask import render_template, request, url_for, redirect, flash, send_from_directory
from flask_login import current_user
from app import db
from app.promo import bp
from app.models import Sentry, Agent, User
import glob
import os
import datetime
import collections
import random
import requests
import json

def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

@bp.route('/')
def home():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.home', status_code=200, status_message='OK')
    return render_template('promo/home.html', title='Welcome to IcyFire!')

@bp.route('/products')
def products():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.products', status_code=200, status_message='OK')
    return render_template('promo/products.html', title='IcyFire - Products')

@bp.route('/products/make-suggestion')
def make_product_suggestion():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.make_product_suggestion', status_code=200, status_message='OK')
    return redirect('https://docs.google.com/forms/d/e/1FAIpQLSf5qQiL7ZxSWWuFR3cvH_2iDmHKEiJ05WDmpAd2RciVv5MRsQ/viewform?usp=sf_link')

@bp.route('/about')
def about():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.about', status_code=200, status_message='OK')
    return "About page placeholder"
    #return render_template('promo/about.html', title='IcyFire - Our Story')

@bp.route('/pricing')
def pricing():
    try:
        locate = requests.get('http://extreme-ip-lookup.com/json/{}'.format(request.remote_addr))
        region_dict = {
            'Alaska': 'PACIFIC',
            'Hawaii': 'PACIFIC',
            'Washington': 'PACIFIC',
            'Oregon': 'PACIFIC',
            'California': 'PACIFIC',
            'Nevada': 'PACIFIC',
            'Arizona': 'PACIFIC',
            'Idaho': 'FRONTIER',
            'Utah': 'FRONTIER',
            'New Mexico': 'FRONTIER',
            'Montana': 'FRONTIER',
            'Wyoming': 'FRONTIER',
            'Colorado': 'FRONTIER',
            'Kansas': 'FRONTIER',
            'Oklahoma': 'FRONTIER',
            'Texas': 'FRONTIER',
            'North Dakota': 'MIDWEST',
            'South Dakota': 'MIDWEST',
            'Nebraska': 'MIDWEST',
            'Minnesota': 'MIDWEST',
            'Iowa': 'MIDWEST',
            'Missouri': 'MIDWEST',
            'Wisconsin': 'MIDWEST',
            'Illinois': 'MIDWEST',
            'Indiana': 'MIDWEST',
            'Michigan': 'MIDWEST',
            'Ohio': 'MIDWEST',
            'Arkansas': 'SOUTH',
            'Louisiana': 'SOUTH',
            'Mississippi': 'SOUTH',
            'Alabama': 'SOUTH',
            'Georgia': 'SOUTH',
            'Florida': 'SOUTH',
            'South Carolina': 'SOUTH',
            'North Carolina': 'SOUTH',
            'Virginia': 'SOUTH',
            'West Virginia': 'SOUTH',
            'Kentucky': 'SOUTH',
            'Tennessee': 'SOUTH',
            'Maine': 'NORTHEAST',
            'New Hampshire': 'NORTHEAST',
            'Vermont': 'NORTHEAST',
            'Massachusetts': 'NORTHEAST',
            'Connecticut': 'NORTHEAST',
            'Rhode Island': 'NORTHEAST',
            'New York': 'NORTHEAST',
            'New Jersey': 'NORTHEAST',
            'Pennsylvania': 'NORTHEAST',
            'Delaware': 'NORTHEAST',
            'Maryland': 'NORTHEAST',
            'District of Columbia': 'NORTHEAST'
        }
        if locate.status_code == 200:
            data = json.loads(locate.text)
            if data['country'] != 'United States':
                flash("Our product is only available in the United States at the moment. Sorry about that!")
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.pricing', status_code=403, status_message='Not in the US')
                return redirect(url_for('promo.home'))
            else:
                region = region_dict[data['region']]
                agents = Agent.query.filter(Agent.crta_code.split('-')[1] == region).all()
                lucky_agent = agents[random.randint(0, len(agents)-1)]
                make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.pricing', status_code=200, status_message='{}|{}'.format(region, lucky_agent.crta_code))
    except:
        agents = Agent.query.filter().all()
        lucky_agent = agents[random.randint(0, len(agents)-1)]
        make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.pricing', status_code=200, status_message='?|{}'.format(region, lucky_agent.crta_code))
    return render_template('promo/pricing.html', title='IcyFire - Pricing', name='{} {}'.format(lucky_agent.first_name, lucky_agent.last_name), phone_number=lucky_agent.phone_number, email=lucky_agent.email)

@bp.route('/blog')
def blog():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.blog', status_code=200, status_message='OK')
    basedir = os.path.abspath(os.path.dirname(__file__))
    #article_directory = os.path.join(basedir, 'app', 'templates', 'promo', 'articles', '*.html')
    article_directory = './app/templates/promo/articles/*.html'
    article_dict = collections.defaultdict(list)
    for article in glob.glob(article_directory):
        filename = os.path.split(article)[-1]
        title = filename.replace('_', ' ')
        title = title.split('.')[0]
        date = os.path.getmtime(article)
        date = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d')
        article_dict[date].append(title)
        article_dict[date].append(article)
    ordered = collections.OrderedDict(sorted(article_dict.items(), key=lambda t: t[0], reverse=True))
    #return str(article_dict)
    return render_template('promo/blog.html', title='IcyFire - Blog', article_dict=article_dict, ordered=ordered)

@bp.route('/blog/<article_path>&<article_title>')
def article(article_path, article_title):
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.article', status_code=200, status_message='{}'.format(article_title))
    try:
        return render_template('promo/articles/{}'.format(article_path), title='IcyFire - {}'.format(article_title))
    except:
        flash("Sorry, we couldn't find the article you were looking for.")
        return redirect(url_for('promo.blog'))

@bp.route('/landing/<audience>')
def landing(audience):
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.landing', status_code=200, status_message='{}'.format(audience))
    try:
        return render_template('promo/landing/{}.html'.format(audience), title='IcyFire for {}'.format(audience.capitalize()))
    except:
        return redirect(url_for('promo.home'))

@bp.route('/random-image/<image_type>')
def random_image(image_type):
    basedir = os.path.abspath(os.path.dirname(__file__))
    if image_type == 'scenic':
        #scenic_directory = os.path.join(basedir, 'app', 'static', 'scenic_images')
        #scenic_directory = scenic_directory.replace('\\', '/')
        scenic_directory = './app/static/scenic_images/*.*'
        scenic_list = glob.glob(scenic_directory)
        regular_list = []
        for x in scenic_list:
            x = os.path.split(x)
            regular_list.append(x[-1])
        #return str(regular_list)
        #return send_from_directory('./app/static/scenic_images', regular_list[random.randint(0, len(regular_list)-1)])
        #return send_from_directory(os.path.join(basedir, 'app', 'static', 'scenic_images'), '1199px-Chicago_sunrise_1.jpg')
        return redirect(url_for('static', filename='scenic_images/{}'.format(regular_list[random.randint(0, len(regular_list)-1)])))
    elif image_type == 'people':
        #people_directory = os.path.join(basedir, 'app', 'static', 'people_images', '*.*')
        people_directory = './app/static/people_images/*.*'
        people_list = glob.glob(people_directory)
        regular_list = []
        for x in people_list:
            x = os.path.split(x)
            regular_list.append(x[-1])
        return redirect(url_for('static', filename='people_images/{}'.format(regular_list[random.randint(0, len(regular_list)-1)])))
        #return send_from_directory(people_list[random.randint(0, len(people_list)-1)])
    else:
        return render_template('errors/404.html')

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')