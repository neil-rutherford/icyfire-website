from app import create_app, db
import unittest
import os
from config import Config
from app.models import User, Domain, Sentry
from flask_login import current_user, login_user

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True

class FlaskTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()


    def tearDown(self):
        #self.app_context.pop()
        db.session.remove()
        db.drop_all()


    def set_users(self):
        beatles = Domain(domain_name='The Beatles', sale_id=1, activation_code='abc123')
        stones = Domain(domain_name='The Rolling Stones', sale_id=2, activation_code='123abc')
        db.session.add(beatles)
        db.session.add(stones)
        db.session.commit()

        admin = User(email='epstein@beatles.com', is_admin=True, is_create=True, is_read=True, is_update=True, is_delete=True, post_count=0, domain_id=1)
        admin.set_password('yellow-submarine')

        u1 = User(email='lennon@beatles.com', is_admin=False, is_create=False, is_read=False, is_update=False, is_delete=False, post_count=0, domain_id=1)
        u1.set_password('come-together')

        u2 = User(email='mccartney@beatles.com', is_admin=False, is_create=False, is_read=False, is_update=False, is_delete=False, post_count=0, domain_id=1)
        u2.set_password('all-you-need-is-love')

        u3 = User(email='starr@beatles.com', is_admin=False, is_create=False, is_read=False, is_update=False, is_delete=False, post_count=0, domain_id=1)
        u3.set_password('love-me-do')

        u4 = User(email='harrison@beatles.com', is_admin=False, is_create=False, is_read=False, is_update=False, is_delete=False, post_count=0, domain_id=1)
        u4.set_password('cant-buy-me-love')

        u5 = User(email='jagger@stones.com', is_admin=False, is_create=False, is_read=False, is_update=False, is_delete=False, post_count=0, domain_id=2)
        u5.set_password('paint-it-black')

        db.session.add(admin)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        db.session.add(u5)
        db.session.commit()


    def set_incidents(self):
        self.set_users()
        #Epstein
        user = User.query.filter_by(email='epstein@beatles.com').first()
        ok1 = Sentry(ip_address='A', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=403, status_message='incorrect creds', flag=False)
        ok2 = Sentry(ip_address='A', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=200, status_message='ok', flag=False)
        ok3 = Sentry(ip_address='A', user_id=user.id, domain_id=user.domain_id, endpoint='admin.dashboard', status_code=200, status_message='ok', flag=False)
        eh1 = Sentry(ip_address='A', user_id=user.id, domain_id=user.domain_id, endpoint='admin.grant_permission', status_code=200, status_message='ok', flag=False)
        db.session.add(ok1)
        db.session.add(ok2)
        db.session.add(ok3)
        db.session.add(eh1)
        db.session.commit()
        #Lennon
        user = User.query.filter_by(email='lennon@beatles.com').first()
        ok1 = Sentry(ip_address='B', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=403, status_message='incorrect creds', flag=False)
        ok2 = Sentry(ip_address='B', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=200, status_message='ok', flag=False)
        ok3 = Sentry(ip_address='B', user_id=user.id, domain_id=user.domain_id, endpoint='main.dashboard', status_code=200, status_message='ok', flag=False)
        eh1 = Sentry(ip_address='B', user_id=user.id, domain_id=user.domain_id, endpoint='main.update_post', status_code=404, status_message='ok', flag=False)
        db.session.add(ok1)
        db.session.add(ok2)
        db.session.add(ok3)
        db.session.add(eh1)
        db.session.commit()
        #McCartney
        user = User.query.filter_by(email='mccartney@beatles.com').first()
        ok1 = Sentry(ip_address='C', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=403, status_message='incorrect creds', flag=False)
        ok2 = Sentry(ip_address='C', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=200, status_message='ok', flag=False)
        ok3 = Sentry(ip_address='C', user_id=user.id, domain_id=user.domain_id, endpoint='main.dashboard', status_code=200, status_message='ok', flag=False)
        eh1 = Sentry(ip_address='C', user_id=user.id, domain_id=user.domain_id, endpoint='main.update_post', status_code=404, status_message='ok', flag=False)
        db.session.add(ok1)
        db.session.add(ok2)
        db.session.add(ok3)
        db.session.add(eh1)
        db.session.commit()
        #Starr
        user = User.query.filter_by(email='starr@beatles.com').first()
        ok1 = Sentry(ip_address='D', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=403, status_message='incorrect creds', flag=False)
        ok2 = Sentry(ip_address='D', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=200, status_message='ok', flag=False)
        ok3 = Sentry(ip_address='D', user_id=user.id, domain_id=user.domain_id, endpoint='main.dashboard', status_code=200, status_message='ok', flag=False)
        eh1 = Sentry(ip_address='D', user_id=user.id, domain_id=user.domain_id, endpoint='main_update_post', status_code=404, status_message='ok', flag=False)
        db.session.add(ok1)
        db.session.add(ok2)
        db.session.add(ok3)
        db.session.add(eh1)
        db.session.commit()
        #Harrison
        user = User.query.filter_by(email='harrison@beatles.com').first()
        ok1 = Sentry(ip_address='E', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=403, status_message='incorrect creds', flag=False)
        ok2 = Sentry(ip_address='E', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=200, status_message='ok', flag=False)
        ok3 = Sentry(ip_address='E', user_id=user.id, domain_id=user.domain_id, endpoint='main.dashboard', status_code=200, status_message='ok', flag=False)
        eh1 = Sentry(ip_address='E', user_id=user.id, domain_id=user.domain_id, endpoint='main.update_post', status_code=404, status_message='ok', flag=False)
        db.session.add(ok1)
        db.session.add(ok2)
        db.session.add(ok3)
        db.session.add(eh1)
        db.session.commit()
        #Jagger
        user = User.query.filter_by(email='jagger@stones.com').first()
        wrong_domain = Domain.query.filter_by(domain_name='The Beatles').first()
        ok1 = Sentry(ip_address='X', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=403, status_message='incorrect creds', flag=False)
        ok2 = Sentry(ip_address='X', user_id=user.id, domain_id=user.domain_id, endpoint='auth.login', status_code=200, status_message='ok', flag=False)
        ok3 = Sentry(ip_address='X', user_id=user.id, domain_id=user.domain_id, endpoint='main.dashboard', status_code=200, status_message='ok', flag=False)
        eh1 = Sentry(ip_address='X', user_id=user.id, domain_id=user.domain_id, endpoint='main.update_post', status_code=404, status_message='ok', flag=False)
        lol_wut = Sentry(ip_address='X', user_id=user.id, domain_id=wrong_domain.id, endpoint='main.create_post', status_code=200, status_message='ok', flag=True)
        db.session.add(ok1)
        db.session.add(ok2)
        db.session.add(ok3)
        db.session.add(eh1)
        db.session.add(lol_wut)
        db.session.commit()


    def test_dashboard_normal(self):
        # Makes sure all four Beatles are on the dashboard, and that Mick Jagger is not
        self.set_users()
        #tester = self.app.test_client(self)
        #admin = User.query.filter_by(email='epstein@beatles.com').first()
        #login_user(admin)
        with self.client:
            #response = self.client.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine', remember_me=False), follow_redirects=True)
            login_user(User.query.filter_by(email='epstein@beatles.com').first())
            print(response.data)
            #self.assertEqual(current_user.email, 'epstein@beatles.com')
            #response = self.client.get('/admin/dashboard', follow_redirects=True)
            
            #self.assertNotIn(b"Please log in to access this page.", response.data)
            #self.assertEqual(response.status_code, 200)
        #self.assertIn(b"lennon@beatles.com", response.data)
        #self.assertIn(b"mccartney@beatles.com", response.data)
        #self.assertIn(b"starr@beatles.com", response.data)
        #self.assertIn(b"harrison@beatles.com", response.data)
        #self.assertNotIn(b"jagger@stones.com", response.data)

if __name__ == '__main__':
    unittest.main()