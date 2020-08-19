from app import create_app, db
from app.models import User, Domain, TimeSlot, CountryLead

# Initializes one week's worth of time slots so that users can link their social media creds and servers can begin querying
def create_server():
    server_id = 1
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
    print("Server successfully created.")

# Creates an IcyFire domain object
def create_icyfire_domain():
    icyfire = Domain(domain_name='IcyFire Technologies, LLC')
    db.session.add(icyfire)
    db.session.commit()
    print("IcyFire domain successfully created.")

# Creates a meta user, which opens up access to the meta / maintenance module
def create_meta_user():
    icyfire = Domain.query.filter_by(domain_name='IcyFire Technologies, LLC').first()
    meta = User(email='neilrutherford@icy-fire.com', domain_id=icyfire.id, post_count=0, is_admin=True, is_create=True, is_read=True, is_update=True, is_delete=True, email_opt_in=True, icyfire_crta='USA-00-00-00')
    meta.set_password('password123')
    db.session.add(meta)
    db.session.commit()
    print("Meta access account successfully created.")

# Creates the head of the sales hierarchy so that child positions can be created
def create_country_lead():
    meta = User.query.filter_by(email='neilrutherford@icy-fire.com').first()
    country_lead = CountryLead(user_id=meta.id, first_name='Neil', last_name='Rutherford', phone_country=1, phone_number='1112223333', email='neilrutherford@icy-fire.com', crta_code='USA-00-00-00')
    db.session.add(country_lead)
    db.session.commit()
    print("Country lead successfully created.")

# Creates an account with only read permission so that prospective clients can explore the app
def create_demo_account():
    icyfire = Domain.query.filter_by(domain_name='IcyFire Technologies, LLC').first()
    demo = User(email='demo@icy-fire.com', domain_id=icyfire.id, post_count=0, is_admin=False, is_create=False, is_read=True, is_update=False, is_delete=True, email_opt_in=False, icyfire_crta=None)
    demo.set_password('demo')
    db.session.add(demo)
    db.session.commit()
    print("Demo account successfully created.")

# Creates app context
create_app().app_context().push()
db.create_all()

create_server()
create_icyfire_domain()
create_meta_user()
create_country_lead()
create_demo_account()