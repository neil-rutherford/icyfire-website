from flask import render_template, request, url_for, redirect, flash, send_from_directory, jsonify
from flask_login import current_user, login_user
from app import db
from app.promo import bp
from app.models import Sentry, User, Lead, Partner
from app.promo.forms import LeadForm
import glob
import os
import datetime
import collections
import random
import requests
import json
import pdfrw
from app.main.transfer import TransferData
from dotenv import load_dotenv

load_dotenv('.env')

def make_sentry(user_id, domain_id, ip_address, endpoint, status_code, status_message, flag=False):
    activity = Sentry(ip_address=ip_address, user_id=user_id, endpoint=endpoint, status_code=status_code, status_message=status_message, domain_id=domain_id, flag=flag)
    db.session.add(activity)
    db.session.commit()

@bp.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@bp.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

#-----------------------------------------------------------------------------------
# INFORMATION PAGES

# Works, 2020-08-16
@bp.route('/')
def home():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.home', status_code=200, status_message='OK')
    return render_template('promo/new_home.html', title='Welcome to IcyFire!')

# Works, 2020-08-16
@bp.route('/product')
def product():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.product', status_code=200, status_message='OK')
    return render_template('promo/product.html', title='IcyFire Social Media Scheduler')

# Works, 2020-08-16
@bp.route('/help-others')
def help_others():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.help_others', status_code=200, status_message='OK')
    return render_template('promo/help_others.html', title='Help Others: How IcyFire provides value to our customers')

# Works, 2020-08-16
@bp.route('/what-if')
def what_if():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.what_if', status_code=200, status_message='OK')
    return render_template('promo/what_if.html', title='What If: How IcyFire innovates')

# Works, 2020-08-16
@bp.route('/do-good')
def do_good():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.do_good', status_code=200, status_message='OK')
    return render_template('promo/do_good.html', title='Do Good: How IcyFire leads by example')

# Works, 2020-08-16
@bp.route('/contact-us')
def contact_us():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.contact_us', status_code=200, status_message='OK')
    return render_template('promo/contact_us.html', title='Contact us')

# Works, 2020-08-16
@bp.route('/product/competition-weigh-in')
def competition():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.competition', status_code=200, status_message='OK')
    return render_template('promo/competition.html', title='Competition weigh-in')

# Works, 2020-08-18
@bp.route('/careers')
def careers():
    flash("Thank you for your interest, but IcyFire doesn't have any career openings at the moment.")
    return redirect(url_for('promo.home'))
    #return send_from_directory('static/agreements', 'agent_jd.pdf')

@bp.route('/about')
def about():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.about', status_code=200, status_message='OK')
    return render_template('promo/about.html', title='About IcyFire')

@bp.route('/blog')
def blog():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.blog', status_code=200, status_message='OK')
    basedir = os.path.abspath(os.path.dirname(__file__))
    article_directory = './app/templates/promo/articles/*.html'
    article_dict = collections.defaultdict(list)
    for article in glob.glob(article_directory):
        filename = os.path.split(article)[-1]
        title = filename.replace('_', ' ')
        title = title.split('.')[0]
        date = os.path.getmtime(article)
        date = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d')
        article_dict[date].append(title)
        article_dict[date].append(filename)
    ordered = collections.OrderedDict(sorted(article_dict.items(), key=lambda t: t[0], reverse=True))
    return render_template('promo/blog.html', title='Blog', article_dict=article_dict, ordered=ordered)

@bp.route('/blog/<article_path>&<article_title>')
def article(article_path, article_title):
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.article', status_code=200, status_message='{}'.format(article_title))
    try:
        return render_template('promo/articles/{}'.format(article_path), title='{}'.format(article_title))
    except:
        flash("Sorry, we couldn't find the article you were looking for.")
        return redirect(url_for('promo.blog'))

@bp.route('/landing/<audience>')
def landing(audience):
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.landing', status_code=200, status_message='{}'.format(audience))
    try:
        title_dict = {
            'church': 'Learn how IcyFire can help your church.', 
            'church_congregant': "Learn more about IcyFire's referral program.",
            'church_administrator': "How to be a guiding light in the digital age.",
            'death_care': "A year's worth of content for free."}
        return render_template('promo/landing/{}.html'.format(audience), title='{}'.format(title_dict[audience]))
    except:
        return redirect(url_for('promo.home'))

@bp.route('/random-image/<image_type>')
def random_image(image_type):
    basedir = os.path.abspath(os.path.dirname(__file__))
    if image_type == 'scenic':
        scenic_directory = './app/static/scenic_images/*.*'
        scenic_list = glob.glob(scenic_directory)
        regular_list = []
        for x in scenic_list:
            x = os.path.split(x)
            regular_list.append(x[-1])
        return redirect(url_for('static', filename='scenic_images/{}'.format(regular_list[random.randint(0, len(regular_list)-1)])))
    elif image_type == 'people':
        people_directory = './app/static/people_images/*.*'
        people_list = glob.glob(people_directory)
        regular_list = []
        for x in people_list:
            x = os.path.split(x)
            regular_list.append(x[-1])
        return redirect(url_for('static', filename='people_images/{}'.format(regular_list[random.randint(0, len(regular_list)-1)])))
    else:
        return render_template('errors/404.html')

#-----------------------------------------------------------------------------------
# ACTION PAGES

@bp.route('/claim/<resource>', methods=['GET', 'POST'])
def claim(resource):
    form = LeadForm()
    if form.validate_on_submit():
        if resource == 'death_care':

            lead = Lead(ip_address=request.remote_addr)
            lead.parter_id = 1
            lead.is_contacted = False
            lead.first_name = form.first_name.data
            lead.last_name = form.last_name.data
            lead.company_name = form.company_name.data
            lead.job_title = form.job_title.data
            lead.number_of_employees = form.number_of_employees.data
            lead.time_zone = form.time_zone.data
            lead.phone_number = str(form.phone_number.data)
            lead.email = form.email.data
            lead.contact_preference = form.contact_preference.data
            lead.time_preference = form.time_preference.data
            lead.email_opt_in = form.email_opt_in.data
            db.session.add(lead)
            db.session.commit()
            return redirect(url_for('promo.download', filename='death_care.pdf'))
        else:
            return render_template('errors/404.html')
    return render_template('promo/claim.html', title='Claim your free download!', form=form)

@bp.route('/download/<filename>')
def download(filename):
    try:
        return send_from_directory('static/resources', filename)
    except:
        return render_template('errors/404.html')
    

# Works, 2020-08-16
@bp.route('/contact-sales', methods=['GET', 'POST'])
def contact_sales():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.contact_sales', status_code=200, status_message='OK')
    form = LeadForm()
    if form.validate_on_submit():

        partners = Partner.query.filter_by().all()
        x = random.randint(0, len(partners)-1)
        lucky_partner = partners[x]

        lead = Lead(ip_address=request.remote_addr)
        lead.partner_id = 1
        lead.is_contacted = False
        lead.first_name = form.first_name.data
        lead.last_name = form.last_name.data
        lead.company_name = form.company_name.data
        lead.job_title = form.job_title.data
        lead.number_of_employees = form.number_of_employees.data
        lead.time_zone = form.time_zone.data
        lead.phone_number = form.phone_number.data
        lead.email = form.email.data
        lead.contact_preference = form.contact_preference.data
        lead.time_preference = form.time_preference.data
        lead.email_opt_in = form.email_opt_in.data
        db.session.add(lead)
        db.session.commit()
        flash("Thanks for your interest! We'll reach out to you shortly.")
        return redirect(url_for('promo.home'))
    return render_template('promo/contact_sales.html', title='Contact sales', form=form)

# Works, 2020-08-18
@bp.route('/product/make-suggestion')
def make_product_suggestion():
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.make_product_suggestion', status_code=200, status_message='OK')
    return redirect('https://docs.google.com/forms/d/e/1FAIpQLSf5qQiL7ZxSWWuFR3cvH_2iDmHKEiJ05WDmpAd2RciVv5MRsQ/viewform?usp=sf_link')

# Needs to be set up!
@bp.route('/product/demo')
def product_demo():
    demo = User.query.filter_by(email='demo@icy-fire.com').first()
    if demo is None:
        flash("Sorry, the demo isn't available at this time.")
        return redirect(url_for('promo.product'))
    login_user(demo)
    flash("Welcome to the IcyFire product demo! This is a live environment, and these queues are connected to live accounts. Have a look around. You only have Read permission, so you can't create, update, or delete.")
    return redirect(url_for('main.dashboard'))

# Pricing info, "get started" link redirects to "payment.us_new_landing"
@bp.route('/pricing')
def pricing(): 
    make_sentry(user_id=None, domain_id=None, ip_address=request.remote_addr, endpoint='promo.pricing', status_code=200, status_message='OK')
    return render_template('promo/pricing.html', title='Pricing')