from app.meta import bp
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app
from app import db
from app.models import *
from app.meta.forms import DomainForm, UserForm, SaleForm, LeadForm, PartnerForm #CountryLeadForm, RegionLeadForm, TeamLeadForm, AgentForm, SaleForm, LeadForm 
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import datetime

# TODO: Double check user, sale, domain!

authorized = ['neilrutherford@icy-fire.com']

# Tested 2020-08-08
@bp.route('/meta/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    return render_template('meta/dashboard.html', title='Meta dashboard')

# Tested 2020-08-08
@bp.route('/meta/read/<model>')
@login_required
def read(model):
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    if model == 'domain':
        results = Domain.query.filter_by().order_by(Domain.id.asc()).all()
        return render_template('meta/results.html', title='Search results', model=model, results=results)
    elif model == 'user':
        results = User.query.filter_by().order_by(User.id.asc()).all()
        return render_template('meta/results.html', title='Search results', model=model, results=results)
    elif model == 'partner':
        results = Partner.query.filter_by().order_by(Partner.id.asc()).all()
        return render_template('meta/results.html', title='Search results', model=model, results=results)
    # elif model == 'country_lead':
    #     results = CountryLead.query.filter_by().order_by(CountryLead.id.asc()).all()
    #     return render_template('meta/results.html', title='Search results', model=model, results=results)
    # elif model == 'region_lead':
    #     results = RegionLead.query.filter_by().order_by(RegionLead.id.asc()).all()
    #     return render_template('meta/results.html', title='Search results', model=model, results=results)
    # elif model == 'team_lead':
    #     results = TeamLead.query.filter_by().order_by(TeamLead.id.asc()).all()
    #     return render_template('meta/results.html', title='Search results', model=model, results=results)
    # elif model == 'agent':
    #     results = Agent.query.filter_by().order_by(Agent.id.asc()).all()
    #     return render_template('meta/results.html', title='Search results', model=model, results=results)
    elif model == 'sale':
        results = Sale.query.filter_by().order_by(Sale.id.asc()).all()
        return render_template('meta/results.html', title='Search results', model=model, results=results)
    elif model == 'lead':
        results = Lead.query.filter_by().order_by(Lead.id.asc()).all()
        return render_template('meta/results.html', title='Search results', model=model, results=results)
    elif model == 'timeslot':
        results = TimeSlot.query.filter_by().all()
        return render_template('meta/results.html', title='Search results', model=model, results=results)
    else:
        flash("Couldn't understand that model.")
        return redirect(url_for('meta.dashboard'))

# Works, 2020-08-08
@bp.route('/meta/create/domain', methods=['GET', 'POST'])
@login_required
def create_domain():
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    available_sales = Sale.query.filter_by().all()
    groups_list=[(i.id, i.timestamp) for i in available_sales]
    form = DomainForm()
    form.sale_id.choices = groups_list
    if form.validate_on_submit():
        domain = Domain(domain_name = form.domain_name.data)
        domain.sale_id = form.sale_id.data
        domain.activation_code = form.activation_code.data
        domain.stripe_customer_id = form.stripe_customer_id.data
        domain.expires_on = datetime.datetime.utcnow() + datetime.timedelta(days=31)
        db.session.add(domain)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='New domain', form=form)

# Works, 2020-08-08
@bp.route('/meta/create/user', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    available_domains = Domain.query.filter_by().all()
    available_partners = Partner.query.filter_by().all()
    groups_list=[(i.id, i.domain_name) for i in available_domains]
    partner_list = [(i.id, i.last_name) for i in available_partners]
    partner_list.insert(0, (0, "This user is not a partner."))
    form = UserForm()
    form.domain_id.choices = groups_list
    form.parter_id.choices = partner_list
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password = form.password.data
        user.domain_id = form.domain_id.data
        user.post_count = 0
        user.is_admin = bool(form.is_admin.data)
        user.is_create = bool(form.is_create.data)
        user.is_read = bool(form.is_read.data)
        user.is_update = bool(form.is_update.data)
        user.is_delete = bool(form.is_delete.data)
        user.is_verified = bool(form.is_verified.data)
        user.email_opt_in = bool(form.email_opt_in.data)
        if form.partner_id.data == 0:
            user.partner_id = None
        else:
            user.partner_id = form.partner_id.data
        # if form.icyfire_crta.data == '':
        #     user.icyfire_crta = None
        # else:
        #     user.icyfire_crta = form.icyfire_crta.data
        db.session.add(user)
        db.session.commit()
        flash("Success!")
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='New user', form=form)


@bp.route('/meta/create/partner', methods=['GET', 'POST'])
@login_required
def create_partner():
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    form = PartnerForm()
    if form.validate_on_submit():
        partner = Partner(first_name=form.first_name.data)
        partner.last_name = form.last_name.data
        partner.phone_number = form.phone_number.data
        partner.email = form.email.data
        db.session.add(partner)
        db.session.commit()
        flash("Success!")
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='New partner', form=form)


# Works, 2020-08-08
# @bp.route('/meta/create/country-lead', methods=['GET', 'POST'])
# @login_required
# def create_country_lead():
#     if current_user.email not in authorized:
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = CountryLeadForm()
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl = CountryLead(user_id=form.user_id.data)
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='New country lead', form=form)

# # Works, 2020-08-08
# @bp.route('/meta/create/region-lead', methods=['GET', 'POST'])
# @login_required
# def create_region_lead():
#     if current_user.email not in authorized:
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = RegionLeadForm()
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl = RegionLead(user_id=form.user_id.data)
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         country_lead = CountryLead.query.filter_by(crta_code=form.country_lead_id.data).first()
#         cl.country_lead_id = country_lead.id
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='New region lead', form=form)

# # Works, 2020-08-08
# @bp.route('/meta/create/team-lead', methods=['GET', 'POST'])
# @login_required
# def create_team_lead():
#     if current_user.email != 'neilrutherford@icy-fire.com':
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = TeamLeadForm()
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl = TeamLead(user_id=form.user_id.data)
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         region_lead = RegionLead.query.filter_by(crta_code=form.region_lead_id.data).first()
#         cl.region_lead_id = region_lead.id
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='New team lead', form=form)

# # Works, 2020-08-08
# @bp.route('/meta/create/agent', methods=['GET', 'POST'])
# @login_required
# def create_agent():
#     if current_user.email not in authorized:
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = AgentForm()
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl = Agent(user_id=form.user_id.data)
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         team_lead = TeamLead.query.filter_by(crta_code=form.team_lead_id.data).first()
#         cl.team_lead_id = team_lead.id
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='New agent', form=form)

# Works, 2020-08-08
@bp.route('/meta/create/sale', methods=['GET', 'POST'])
@login_required
def create_sale():
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    available_partners = Partner.query.filter_by().all()
    partner_list = [(i.id, i.last_name) for i in available_partners]
    partner_list.insert(0, (0, "This sale did not involve a partner."))
    form = SaleForm()
    form.partner_id.choices = partner_list
    if form.validate_on_submit():
        sale = Sale(client_name=form.client_name.data)
        if form.partner_id.data != 0:
            sale.partner_id = form.partner_id.data
        else:
            sale.partner_id = None
        # if form.agent_id.data != '':
        #     agent = Agent.query.filter_by(crta_code=form.agent_id.data).first()
        #     sale.agent_id = agent.id
        #     team_lead = TeamLead.query.filter_by(crta_code=form.team_lead_id.data).first()
        #     sale.team_lead_id = team_lead.id
        #     region_lead = RegionLead.query.filter_by(crta_code=form.region_lead_id.data).first()
        #     sale.region_lead_id = region_lead.id
        #     country_lead = CountryLead.query.filter_by(crta_code=form.country_lead_id.data).first()
        #     sale.country_lead_id = country_lead.id
        # else:
        #     sale.agent_id = None
        #     sale.team_lead_id = None
        #     sale.region_lead_id = None
        #     sale.country_lead_id = None
        sale.client_street_address = form.client_street_address.data
        sale.client_city = form.client_city.data
        sale.client_state = form.client_state.data
        sale.client_country = form.client_country.data
        sale.client_zip = form.client_zip.data
        sale.client_phone_country = int(form.client_phone_country.data)
        sale.client_phone_number = str(form.client_phone_number.data)
        sale.client_email = form.client_email.data
        sale.product_id = form.product_id.data
        sale.unit_price = form.unit_price.data
        sale.quantity = form.quantity.data
        sale.subtotal = form.subtotal.data
        sale.sales_tax = form.sales_tax.data
        sale.total = form.total.data
        sale.receipt_url = form.receipt_url.data
        sale.payment_reference = form.payment_reference.data
        db.session.add(sale)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='New sale', form=form)

#Works, 2020-08-08
@bp.route('/meta/create/lead', methods=['GET', 'POST'])
@login_required
def create_lead():
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    available_partners = Partner.query.filter_by().all()
    partner_list = [(i.id, i.last_name) for i in available_partners]
    form = LeadForm()
    form.partner_id.choices = partner_list
    if form.validate_on_submit():
        lead = Lead(email=form.email.data)
        lead.partner_id = form.partner_id.data
        # if form.agent_id.data != '':
        #     agent = Agent.query.filter_by(crta_code=form.agent_id.data).first()
        #     lead.agent_id = agent.id
        # else:
        #     lead.agent_id = None
        lead.is_contacted = bool(form.is_contacted.data)
        lead.first_name = form.first_name.data
        lead.last_name = form.last_name.data
        lead.company_name = form.company_name.data
        lead.job_title = form.job_title.data
        lead.number_of_employees = form.number_of_employees.data
        lead.time_zone = form.time_zone.data
        lead.phone_number = str(form.phone_number.data)
        lead.contact_preference = form.contact_preference.data
        lead.time_preference = form.time_preference.data
        lead.email_opt_in = bool(form.email_opt_in.data)
        db.session.add(lead)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='New lead', form=form)

# Works!!! 2020-08-10
@bp.route('/meta/create/server/')
@login_required
def create_server():
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    
    existing_timeslot = TimeSlot.query.filter_by().order_by(TimeSlot.server_id.desc()).first()
    if existing_timeslot is None:
        server_id = 1
    else:
        server_id = existing_timeslot.server_id + 1

    slot_list = []
    days_of_week = ['1', '2', '3', '4', '5', '6', '7']
    for z in range(0, len(days_of_week)):
        x = 0
        y = 0
        while x < 24:
            if x < 10 and y < 10:
                timeslot = TimeSlot(time='0{}:0{}'.format(x,y))
                timeslot.day_of_week = int(days_of_week[z])
                timeslot.server_id = int(server_id)
                slot_list.append(timeslot)
            elif x < 10:
                timeslot = TimeSlot(time='0{}:{}'.format(x,y))
                timeslot.day_of_week = int(days_of_week[z])
                timeslot.server_id = int(server_id)
                slot_list.append(timeslot)
            elif y < 10:
                timeslot = TimeSlot(time='{}:0{}'.format(x,y))
                timeslot.day_of_week = int(days_of_week[z])
                timeslot.server_id = int(server_id)
                slot_list.append(timeslot)
            else:
                timeslot = TimeSlot(time='{}:{}'.format(x,y))
                timeslot.day_of_week = int(days_of_week[z])
                timeslot.server_id = int(server_id)
                slot_list.append(timeslot)
            y += 1
            if y > 59:
                y = 0
                x += 1
    db.session.add_all(slot_list)
    db.session.commit()
    flash('Successfully added Server {}'.format(server_id))
    return redirect(url_for('meta.dashboard'))

# Think it works, but gotta test one more time once the server is running
@bp.route('/meta/system-status')
def system_status():
    available_servers = TimeSlot.query.filter_by().order_by(TimeSlot.server_id.desc()).first()
    if available_servers is None:
        server_list = None
    else:
        server_list = []
        x = int(available_servers.server_id)
        server_list.append(x)
        while x > 1:
            server_list.append(x-1)
    if server_list is not None:
        system_status = []
        for x in server_list:
            limit = datetime.utcnow() - timedelta(days=7)
            weekly_possible_requests = 10080
            all_requests = Sentry.query.filter(Sentry.endpoint == 'api.read', Sentry.timestamp >= limit).all()
            good_calls = []
            fines = []
            errors = []
            for y in all_requests:
                if y.status_code == 200 and str(y.status_message).split('|')[-1] == str(x):
                    good_calls.append(y)
                elif y.status_code == 404 and str(y.status_message).split('|')[-1] == str(x):
                    good_calls.append(y)
                elif y.status_code == 218 and str(y.status_message).split('|')[-1] == str(x):
                    fines.append(y)
                elif y.status_code == 400 and str(y.status_message).split('|')[-1] == str(x):
                    errors.append(y)
                elif y.status_code == 403 and str(y.status_message).split('|')[-1] == str(x):
                    errors.append(y)

            #good_calls = Sentry.query.filter(Sentry.endpoint == 'api.read', Sentry.status_code == 200, Sentry.status_code == 404, str(Sentry.status_message).split('|')[-1] == str(x), Sentry.timestamp >= limit).all()
            #fines = Sentry.query.filter(Sentry.endpoint == 'api.read', Sentry.status_code == 218, str(Sentry.status_message) == str(x), Sentry.timestamp >= limit).all()
            #errors = Sentry.query.filter(Sentry.endpoint == 'api.read', Sentry.status_code == 400, Sentry.status_code == 403, str(Sentry.status_code).split('|')[-1] == str(x), Sentry.timestamp >= limit).all()
            downtime = weekly_possible_requests - (len(good_calls) + len(fines) + len(errors))
            server_status = {'server_id': x, 'good_calls': int((len(good_calls)/weekly_possible_requests)*100), 'fines': int((len(fines)/weekly_possible_requests)*100), 'errors': int((len(errors)/weekly_possible_requests)*100), 'downtime': int((downtime/weekly_possible_requests)*100)}
            system_status.append(server_status)
    else:
        system_status = None
    return render_template('meta/system_status.html', title='System status (past 7 days)', system_status=system_status)

@bp.route('/meta/edit/domain/<domain_id>', methods=['GET', 'POST'])
@login_required
def edit_domain(domain_id):
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    domain = Domain.query.filter_by(id=domain_id).first()
    available_sales = Sale.query.filter_by().all()
    groups_list=[(i.id, i.timestamp) for i in available_sales]
    form = DomainForm(obj=domain)
    form.sale_id.choices = groups_list
    if form.validate_on_submit():
        domain.domain_name = form.domain_name.data
        domain.sale_id = form.sale_id.data
        domain.activation_code = form.activation_code.data
        db.session.add(domain)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='Edit domain', form=form)

# Tested, 2020-08-10
@bp.route('/meta/edit/user/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    user = User.query.filter_by(id=user_id).first()
    available_domains = Domain.query.filter_by().all()
    available_partners = Partner.query.filter_by().all()
    groups_list=[(i.id, i.domain_name) for i in available_domains]
    partner_list = [(i.id, i.last_name) for i in available_partners]
    partner_list.insert(0, (0, "This user is not a partner."))
    form = UserForm(obj=user)
    form.domain_id.choices = groups_list
    form.partner_id.choices = partner_list
    if form.validate_on_submit():
        user.set_password = form.password.data
        user.domain_id = form.domain_id.data
        user.post_count = 0
        user.is_admin = bool(form.is_admin.data)
        user.is_create = bool(form.is_create.data)
        user.is_read = bool(form.is_read.data)
        user.is_update = bool(form.is_update.data)
        user.is_delete = bool(form.is_delete.data)
        user.is_verified = bool(form.is_verified.data)
        user.email_opt_in = bool(form.email_opt_in.data)
        if form.partner_id.data == 0:
            user.partner_id = None
        else:
            user.partner_id = form.partner_id.data
        #user.icyfire_crta = form.icyfire_crta.data
        db.session.add(user)
        db.session.commit()
        flash("Success!")
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='Edit user', form=form)

@bp.route('/meta/edit/partner/<partner_id>', methods=['GET', 'POST'])
@login_required
def edit_partner(partner_id):
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    partner = Partner.query.filter_by(id=partner_id).first()
    form = PartnerForm(obj=partner)
    if form.validate_on_submit():
        partner = Partner(first_name=form.first_name.data)
        partner.last_name = form.last_name.data
        partner.phone_number = form.phone_number.data
        partner.email = form.email.data
        db.session.add(partner)
        db.session.commit()
        flash("Success!")
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='Edit partner', form=form)

# Tested, 2020-08-10
# @bp.route('/meta/edit/country-lead/<country_lead_id>', methods=['GET', 'POST'])
# @login_required
# def edit_country_lead(country_lead_id):
#     if current_user.email not in authorized:
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     cl = CountryLead.query.filter_by(id=country_lead_id).first()
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = CountryLeadForm(obj=cl)
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl.user_id=form.user_id.data
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='Edit country lead', form=form)

# Tested, 2020-08-10
# @bp.route('/meta/edit/region-lead/<region_lead_id>', methods=['GET', 'POST'])
# @login_required
# def edit_region_lead(region_lead_id):
#     if current_user.email not in authorized:
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     cl = RegionLead.query.filter_by(id=region_lead_id).first()
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = RegionLeadForm(obj=cl)
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl.user_id=form.user_id.data
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         cl.country_lead_id = form.country_lead_id.data
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='Edit region lead', form=form)

# Tested, 2020-08-10
# @bp.route('/meta/edit/team-lead/<team_lead_id>', methods=['GET', 'POST'])
# @login_required
# def edit_team_lead(team_lead_id):
#     if current_user.email not in authorized:
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     cl = TeamLead.query.filter_by(id=team_lead_id).first()
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = TeamLeadForm(obj=cl)
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl.user_id=form.user_id.data
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         cl.region_lead_id = form.region_lead_id.data
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='Edit team lead', form=form)

# Tested, 2020-08-10
# @bp.route('/meta/edit/agent/<agent_id>', methods=['GET', 'POST'])
# @login_required
# def edit_agent(agent_id):
#     if current_user.email not in authorized:
#         db.session.delete(current_user)
#         db.session.commit()
#         return redirect("https://imgflip.com/i/4aqeg1")
#     cl = Agent.query.filter_by(id=agent_id).first()
#     available_users = User.query.filter_by().all()
#     groups_list=[(i.id, i.email) for i in available_users]
#     form = AgentForm(obj=cl)
#     form.user_id.choices = groups_list
#     if form.validate_on_submit():
#         cl.user_id=form.user_id.data
#         cl.first_name = form.first_name.data
#         cl.last_name = form.last_name.data
#         cl.phone_country = 1
#         cl.phone_number = str(form.phone_number.data)
#         cl.email = form.email.data
#         cl.crta_code = form.crta_code.data
#         cl.team_lead_id = form.team_lead_id.data
#         db.session.add(cl)
#         db.session.commit()
#         flash("Success!")
#         return redirect(url_for('meta.dashboard'))
#     return render_template('meta/form.html', title='Edit agent', form=form)

# Tested, 2020-08-10
@bp.route('/meta/edit/sale/<sale_id>', methods=['GET', 'POST'])
@login_required
def edit_sale(sale_id):
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    sale = Sale.query.filter_by(id=sale_id).first()
    available_partners = Partner.query.filter_by().all()
    partner_list = [(i.id, i.last_name) for i in available_partners]
    partner_list.insert(0, (0, "This sale did not involve a partner."))
    form = SaleForm(obj=sale)
    form.partner_id.choices = partner_list
    if form.validate_on_submit():
        sale.client_name=form.client_name.data
        if form.partner_id.data != 0:
            sale.partner_id = form.partner_id.data
        else:
            sale.partner_id = None
        # if form.agent_id.data != '':
        #     agent = Agent.query.filter_by(crta_code=form.agent_id.data).first()
        #     sale.agent_id = agent.id
        #     team_lead = TeamLead.query.filter_by(crta_code=form.team_lead_id.data).first()
        #     sale.team_lead_id = team_lead.id
        #     region_lead = RegionLead.query.filter_by(crta_code=form.region_lead_id.data).first()
        #     sale.region_lead_id = region_lead.id
        #     country_lead = CountryLead.query.filter_by(crta_code=form.country_lead_id.data).first()
        #     sale.country_lead_id = country_lead.id
        # else:
        #     sale.agent_id = None
        #     sale.team_lead_id = None
        #     sale.region_lead_id = None
        #     sale.country_lead_id = None
        sale.client_street_address = form.client_street_address.data
        sale.client_city = form.client_city.data
        sale.client_state = form.client_state.data
        sale.client_country = form.client_country.data
        sale.client_zip = form.client_zip.data
        sale.client_phone_country = int(form.client_phone_country.data)
        sale.client_phone_number = str(form.client_phone_number.data)
        sale.client_email = form.client_email.data
        sale.product_id = form.product_id.data
        sale.unit_price = form.unit_price.data
        sale.quantity = form.quantity.data
        sale.subtotal = form.subtotal.data
        sale.sales_tax = form.sales_tax.data
        sale.total = form.total.data
        sale.receipt_url = form.receipt_url.data
        sale.payment_reference = form.payment_reference.data
        db.session.add(sale)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='Edit sale', form=form)
    
# Tested, 2020-08-10
@bp.route('/meta/edit/lead/<lead_id>', methods=['GET', 'POST'])
@login_required
def edit_lead(lead_id):
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    lead = Lead.query.filter_by(id=lead_id).first()
    available_partners = Partner.query.filter_by().all()
    partner_list = [(i.id, i.last_name) for i in available_partners]
    form = LeadForm(obj=lead)
    form.partner_id.choices = partner_list
    if form.validate_on_submit():
        lead.email=form.email.data
        lead.partner_id = form.partner_id.data
        # if form.agent_id.data != '':
        #     agent = Agent.query.filter_by(id=form.agent_id.data).first()
        #     lead.agent_id = agent.id
        # else:
        #     lead.agent_id = None
        lead.is_contacted = bool(form.is_contacted.data)
        lead.first_name = form.first_name.data
        lead.last_name = form.last_name.data
        lead.company_name = form.company_name.data
        lead.job_title = form.job_title.data
        lead.number_of_employees = form.number_of_employees.data
        lead.time_zone = form.time_zone.data
        lead.phone_number = str(form.phone_number.data)
        lead.contact_preference = form.contact_preference.data
        lead.time_preference = form.time_preference.data
        lead.email_opt_in = bool(form.email_opt_in.data)
        db.session.add(lead)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    return render_template('meta/form.html', title='Edit lead', form=form)

# Tested, 2020-08-10
@bp.route('/meta/delete/<model>/<id>')
@login_required
def delete(model, id):
    if current_user.email not in authorized:
        db.session.delete(current_user)
        db.session.commit()
        return redirect("https://imgflip.com/i/4aqeg1")
    if model == 'domain':
        x = Domain.query.filter_by(id=id).first()
        db.session.delete(x)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    elif model == 'user':
        x = User.query.filter_by(id=id).first()
        db.session.delete(x)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    elif model == 'partner':
        x = Partner.query.filter_by(id=id).first()
        db.session.delete(x)
        db.session.commit()
        flash("Success!")
        return redirect(url_for('meta.dashboard'))
    # elif model == 'country_lead':
    #     x = CountryLead.query.filter_by(id=id).first()
    #     db.session.delete(x)
    #     db.session.commit()
    #     flash('Success!')
    #     return redirect(url_for('meta.dashboard'))
    # elif model == 'region_lead':
    #     x = RegionLead.query.filter_by(id=id).first()
    #     db.session.delete(x)
    #     db.session.commit()
    #     flash('Success!')
    #     return redirect(url_for('meta.dashboard'))
    # elif model == 'team_lead':
    #     x = TeamLead.query.filter_by(id=id).first()
    #     db.session.delete(x)
    #     db.session.commit()
    #     flash('Success!')
    #     return redirect(url_for('meta.dashboard'))
    # elif model == 'agent':
    #     x = Agent.query.filter_by(id=id).first()
    #     db.session.delete(x)
    #     db.session.commit()
    #     flash('Success!')
    #     return redirect(url_for('meta.dashboard'))
    elif model == 'sale':
        x = Sale.query.filter_by(id=id).first()
        db.session.delete(x)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    elif model == 'lead':
        x = Lead.query.filter_by(id=id).first()
        db.session.delete(x)
        db.session.commit()
        flash('Success!')
        return redirect(url_for('meta.dashboard'))
    else:
        flash("Couldn't understand that model.")
        return redirect(url_for('meta.dashboard'))