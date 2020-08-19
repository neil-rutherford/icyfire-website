<p align="center">
    <a href="http://www.icy-fire.com">
        <img src="app/static/new_logo_transparent600.png" alt="IcyFire logo" width="80" height="80">
    </a>

    <h3 align="center">IcyFire website</h3>

<p align="center">
    Digital marketing runs on time with IcyFire.
    <br />
    <a href="https://github.com/neil-rutherford/icyfire-website"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="http://www.icy-fire.com/product/demo">View demo</a>
        ·
    <a href="https://github.com/neil-rutherford/icyfire-website/issues">Report bug</a>
        ·
    <a href="https://github.com/neil-rutherford/icyfire-website/issues">Request feature</a>
</p>
</p>

## Table of contents

* [About the project](#about-the-project)
  * [Built with](#built-with)
* [Getting started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)

## About the project

This is the website of IcyFire Technologies, a tech startup based out of Denver, Colorado. At the moment, this serves as both a promotional and functional platform for IcyFire Social, our flagship product. IcyFire Social is a social media queuing tool that aims to make digital marketing easier for small businesses, automate content publishing schedules, facilitate teamwork while employees are working from home, and open doors to outsourcing marketing work. IcyFire Social offers social media integrations for Facebook, Twitter, Tumblr, and Reddit via their respective APIs. The website serves as a input collection and data storage tool; external servers manage the timing and publishing.

This website is designed to be run on a hosting service with an ephemeral filesystem.

### Built with

* [Flask](https://flask.palletsprojects.com/en/1.1.x/)
* [Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/)
* [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/)
* [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/)
* [Flask-Login](https://flask-login.readthedocs.io/en/latest/)
* [Flask-Bootstrap](https://pythonhosted.org/Flask-Bootstrap/) 
* [Flask-Mail](https://pythonhosted.org/Flask-Mail/)
* [Flask-Moment](https://github.com/miguelgrinberg/Flask-Moment)
* [PDFRW](https://pypi.org/project/pdfrw/)
* [PyJWT](https://pyjwt.readthedocs.io/en/latest/)
* [Cryptography](https://cryptography.io/en/latest/)
* [Facebook SDK](https://facebook-sdk.readthedocs.io/en/latest/)
* [Python Twitter](https://github.com/bear/python-twitter)
* [PyTumblr](https://github.com/tumblr/pytumblr)
* [PRAW](https://praw.readthedocs.io/en/latest/)
* [Dropbox](https://www.dropbox.com/developers/documentation/python#documentation)

## Getting started

You are free to run this locally on your own system, but please note that some of the functionality will be missing. This includes services that need API keys to run, such as Dropbox and Flask-Mail, as well as the servers that query the IcyFire API. With that in mind, let's begin.

### Prerequisites

To run this, you will need Python 3.x and Git installed.

### Installation

In the terminal, execute the following commands:

```sh
# Clone the Github repository
git clone https://github.com/neil-rutherford/icyfire-website.git

# Set up and activate the virtual environment
python3 -m venv venv
source venv/bin/activate        # For Unix/Linux systems, or...
source venv\Scripts\activate    # For pure Windows systems, or...
source venv/Scripts/activate    # For Windows running a Bash emulator

# Install all dependencies
python3 -m pip install -r requirements.txt

# Set environmental variables
export DROPBOX_ACCESS_KEY=<dropbox_access_key>
export READ_TOKEN=<read_token>
export DELETE_TOKEN=<delete_token>
export SECURITY_TOKEN=<security_token>
export SECRET_KEY=<secret_key>
export SALT=<salt>
export MAIL_SERVER=<mail_server>
export MAIL_PORT=<mail_port>
export MAIL_USE_TLS=<mail_use_tls>
export MAIL_USERNAME=<mail_username>
export MAIL_PASSWORD=<mail_password>

# Initialize the Alembic migration repository
flask db init
flask db migrate -m "Initial commit"
flask db upgrade
```

Prior to running the Flask app, the database must be populated with certain objects so that things don't error out. Run the following Python script to take care of this:

```py
#!/usr/bin/env python3

from app import create_app, db
from app.models import User, Domain, CountryLead, TimeSlot

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
def create_meta_access():
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

create_server()
create_icyfire_domain()
create_meta_user()
create_country_lead()
create_demo_account()
```

Finally, run the Flask app:

`flask run`

## Usage

_Register the sales team_: Log in as meta user -> go to `/meta/dashboard` -> "New Region Lead" -> "New Team Lead" -> "New Agent"

_Register a new sale_: Log in as an Agent -> go to `/create/sale` -> input information -> download receipt and give it to the client

_Register a new domain_: Go to `/register/domain` -> use activation code on receipt to register

_Link social accounts_: Log in as domain admin -> go to `/register/link-social` -> follow instructions to get API credentials -> input credentials -> choose UTC timeslots

_Grant CRUD permissions_: Log in as domain admin -> go to `/admin/dashboard` -> find the user in the table -> click "Grant"/"Revoke"

_See security data_: Log in as domain admin -> go to `/admin/dashboard` -> scroll down and pick the option you would like to see -> for iffy incidents, follow directions on whether or not to escalate to the IcyFire security team

_Queue a post_: Log in as a user with create permissions -> go to `/dashboard` -> at the top, click the type of post you want to make -> choose which social sites you want to publish to -> compose your post -> click "Done"

_Register as a new user_: Go to `register/user` -> input domain name -> wait for domain admin to grant CRUD permissions

For more complete documentation, please refer to the "docs" folder in the Github repository or visit the <a href="http://www.icy-fire.com/help">help section of the IcyFire website</a>.

## Roadmap

See the [open issues](https://github.com/neil-rutherford/icyfire-website/issues) for a list of features and known issues curated by the open-source community.
See the [Jira roadmap](https://icyfire.atlassian.net/jira/software/projects/ICYFIRE/boards/1/roadmap) for a list of features planned by the IcyFire team.

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Neil Rutherford - [@neilbolyard](https://twitter.com/neilbolyard) - neilrutherford@icy-fire.com
IcyFire Technologies - [@IcyFireTech](https://twitter.com/IcyFireTech) - support@icy-fire.com