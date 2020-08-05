from app import create_app, db
import os
import unittest
import app
from app.models import User, Sentry, Domain
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class AdminTest(unittest.TestCase):
#class AdminTest(TestCase):

    #def setUp(self):
        #self.app = create_app(TestConfig)
        #self.app_context = self.app.app_context()
        #self.app_context.push()
        #db.create_all()
    

    #def tearDown(self):
        #db.session.remove()
        #db.drop_all()
        #self.app_context.pop()


    def set_users(self):
        beatles = Domain(domain_name='The Beatles')
        stones = Domain(domain_name='The Rolling Stones')
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
        tester = app.test_client(self)
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)
        response = tester.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"lennon@beatles.com", response.data)
        self.assertIn(b"mccartney@beatles.com", response.data)
        self.assertIn(b"starr@beatles.com", response.data)
        self.assertIn(b"harrison@beatles.com", response.data)
        self.assertNotIn(b"jagger@stones.com", response.data)


    def test_dashboard_abnormal(self):
        # Can non-admin users access the dashboard?
        self.set_users()
        tester = app.test_client(self)
        tester.post('/login', data=dict(email='lennon@beatles.com', password='come-together'), follow_redirects=True)
        response = tester.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ERROR: You don't have permission to do that.", response.data)


    def test_grantPermission_normal(self):
        # Grants Lennon create permission
        self.set_users()
        tester = app.test_client(self)
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)
        response = tester.get('/admin/2/+c', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=2).first()
        self.assertTrue(user.is_create)
        self.assertFalse(user.is_read)
        self.assertFalse(user.is_update)
        self.assertFalse(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"Create permission granted.", response.data)

        # Grants McCartney read permission
        response = tester.get('/admin/3/+r', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=3).first()
        self.assertFalse(user.is_create)
        self.assertTrue(user.is_read)
        self.assertFalse(user.is_update)
        self.assertFalse(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"Read permission granted.", response.data)

        # Grants Starr update permission
        response = tester.get('/admin/4/+u', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=4).first()
        self.assertFalse(user.is_create)
        self.assertFalse(user.is_read)
        self.assertTrue(user.is_update)
        self.assertFalse(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"Update permission granted.", response.data)

        # Grants Harrison delete permission
        response = tester.get('/admin/5/+d', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=5).first()
        self.assertFalse(user.is_create)
        self.assertFalse(user.is_read)
        self.assertFalse(user.is_update)
        self.assertTrue(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"Delete permission granted.", response.data)
    

    def test_grantPermission_abnormal(self):
        self.set_users()
        tester = app.test_client(self)
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)

        # Can I give someone in a different domain permission?
        response = tester.get('/admin/6/+c', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=6).first()
        self.assertFalse(user.is_create)
        self.assertFalse(user.is_read)
        self.assertFalse(user.is_update)
        self.assertFalse(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"ERROR: That user isn't part of your domain.", response.data)

        # Handle for non-existent users
        response = tester.get('/admin/10/+d', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=10).first()
        self.assertIsNone(user)
        self.assertIn(b"ERROR: Can't find that user.", response.data)

        # Handle for malformed requests
        response = tester.get('/admin/2/+wtffffff', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ERROR: Not a valid permission.', response.data)

        # Can a non-admin grant permissions?
        tester.get('/logout', follow_redirects=True)
        tester.post('/login', data=dict(email='harrison@beatles.com', password='cant-buy-me-love'), follow_redirects=True)
        response = tester.get('/admin/2/+r', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=2).first()
        self.assertFalse(user.is_create)
        self.assertFalse(user.is_read)
        self.assertFalse(user.is_update)
        self.assertFalse(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"ERROR: You don't have permission to do that.", response.data)


    def test_revokePermission_normal(self):
        self.set_users()
        tester = app.test_client(self)
        lennon = User.query.filter_by(email='lennon@beatles.com').first()
        lennon.is_create = True
        mccartney = User.query.filter_by(email='mccartney@beatles.com').first()
        mccartney.is_read = True
        starr = User.query.filter_by(email='starr@beatles.com').first()
        starr.is_update = True
        harrison = User.query.filter_by(email='harrison@beatles.com').first()
        harrison.is_delete = True
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)

        # Revoke Lennon's create permission
        response = tester.get('/admin/2/-c', follow_redirects=True)
        self.assertFalse(lennon.is_create)
        self.assertFalse(lennon.is_read)
        self.assertFalse(lennon.is_update)
        self.assertFalse(lennon.is_delete)
        self.assertFalse(lennon.is_admin)
        self.assertIn(b"Create permission revoked.", response.data)

        # Revoke McCartney's read permission
        response = tester.get('/admin/3/-r', follow_redirects=True)
        self.assertFalse(mccartney.is_create)
        self.assertFalse(mccartney.is_read)
        self.assertFalse(mccartney.is_update)
        self.assertFalse(mccartney.is_delete)
        self.assertFalse(mccartney.is_admin)
        self.assertIn(b"Read permission revoked.", response.data)

        # Revoke Starr's update permission
        response = tester.get('/admin/4/-u', follow_redirects=True)
        self.assertFalse(starr.is_create)
        self.assertFalse(starr.is_read)
        self.assertFalse(starr.is_update)
        self.assertFalse(starr.is_delete)
        self.assertFalse(starr.is_admin)
        self.assertIn(b"Update permission revoked.", response.data)

        # Revoke Harrison's delete permission
        response = tester.get('/admin/5/-d', follow_redirects=True)
        self.assertFalse(harrison.is_create)
        self.assertFalse(harrison.is_read)
        self.assertFalse(harrison.is_update)
        self.assertFalse(harrison.is_delete)
        self.assertFalse(harrison.is_admin)
        self.assertIn(b"Delete permission revoked.", response.data)

        # Kill Lennon
        response = tester.get('/admin/2/-kill', follow_redirects=True)
        self.assertIsNone(lennon)
        self.assertIn(b"User deleted.", response.data)
    

    def test_revokePermission_abnormal(self):
        self.set_users()
        tester = app.test_client(self)
        jagger = User.query.filter_by(email='jagger@stones.com').first()
        jagger.is_create = True
        lennon = User.query.filter_by(email='lennon@beatles.com').first()
        lennon.is_read = True

        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)
        
        # Can I revoke a permission for someone in a different domain?
        response = tester.get('/admin/6/-c', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=6).first()
        self.assertTrue(user.is_create)
        self.assertFalse(user.is_read)
        self.assertFalse(user.is_update)
        self.assertFalse(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"ERROR: That user isn't part of your domain.", response.data)

        # Handle for non-existent users
        response = tester.get('/admin/10/-d', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=10).first()
        self.assertIsNone(user)
        self.assertIn(b"ERROR: Can't find that user.", response.data)

        # Handle for malformed requests
        response = tester.get('/admin/2/-wtffffff', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ERROR: Not a valid permission.', response.data)

        # Can a non-admin grant permissions?
        tester.get('/logout', follow_redirects=True)
        tester.post('/login', data=dict(email='harrison@beatles.com', password='cant-buy-me-love'), follow_redirects=True)
        response = tester.get('/admin/2/-r', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(id=2).first()
        self.assertFalse(user.is_create)
        self.assertTrue(user.is_read)
        self.assertFalse(user.is_update)
        self.assertFalse(user.is_delete)
        self.assertFalse(user.is_admin)
        self.assertIn(b"ERROR: You don't have permission to do that.", response.data)


    def test_escalateCiso(self):
        tester = app.test_client(self)
        i1 = Sentry(ip_address='111.22.333.444', user_id=1, domain_id=1, endpoint='main.example', status_code=403, status_message='Access denied!', flag=False)
        i2 = Sentry(ip_address='123.45.678.901', user_id=2, domain_id=2, endpoint='auth.login', status_code=200, status_message='OK', flag=False)
        db.session.add(i1)
        db.session.add(i2)
        db.session.commit()
        response = tester.get('/admin/sentry/escalate-ciso/1', follow_redirects=True)
        incident1 = Sentry.query.filter_by(id=1).first()
        incident2 = Sentry.query.filter_by(id=2).first()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(incident1.flag)
        self.assertFalse(incident2.flag)
        self.assertIn(b"Thank you for your feedback. You'll hear from us shortly.", response.data)

        response = tester.get('/admin/sentry/escalate-ciso/100', follow_redirects=True)
        incident = Sentry.query.filter_by(id=100).first()
        self.assertIsNone(incident)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ERROR: Can't find that incident.", response.data)


    def test_getUserInfo_normal(self):
        self.set_incidents()
        tester = app.test_client(self)
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)

        # Can it display everything that Lennon has been doing?
        response = tester.get('/admin/sentry/user/2', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'B', response.data)
        self.assertIn(b'403', response.data)
        self.assertIn(b'200', response.data)
        self.assertIn(b'404', response.data)
        self.assertIn(b'Grant', response.data)
        self.assertIn(b'incorrect creds', response.data)
        self.assertIn(b'ok', response.data)
        self.assertIn(b'lennon@beatles.com', response.data)

        # Can it display the one weird thing that Jagger did in the Beatles domain?
        response = tester.get('/admin/sentry/user/6', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'X', response.data)
        self.assertIn(b'200', response.data)
        self.assertIn(b'main.create_post', response.data)
        self.assertIn(b'jagger@stones.com', response.data)

    
    def test_getUserInfo_abnormal(self):
        # Access page as a non-admin user
        self.set_incidents()
        tester = app.test_client(self)
        tester.post('/login', data=dict(email='starr@beatles.com', password='love-me-do'), follow_redirects=True)
        response = tester.get('/admin/sentry/user/2', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ERROR: You don't have permission to do that.", response.data)

        # Handle for non-existent users
        tester.get('/logout', follow_redirects=True)
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)
        response = tester.get('/admin/sentry/user/100000', follow_redirects=True)
        user = User.query.filter_by(id=100000).first()
        self.assertIsNone(user)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ERROR: Can't find that user.", response.data)


    def test_createSuccess_normal(self):
        self.set_users()
        tester = app.test_client(self)
        x1 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_short_text', status_code=200, status_message='Create #1', flag=False)
        x2 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_long_text', status_code=200, status_message='Create #2', flag=False)
        x3 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_image', status_code=200, status_message='Create #3', flag=False)
        x4 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_video', status_code=200, status_message='Create #4', flag=False)
        x5 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_short_text', status_code=403, status_message='Should not appear', flag=False)
        db.session.add(x1)
        db.session.add(x2)
        db.session.add(x3)
        db.session.add(x4)
        db.session.add(x5)
        db.session.commit()
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)
        response = tester.get('/admin/sentry/create/success', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create #1', response.data)
        self.assertIn(b'Create #2', response.data)
        self.assertIn(b'Create #3', response.data)
        self.assertIn(b'Create #4', response.data)
        self.assertNotIn(b'Should not appear', response.data)


    def test_createSuccess_abnormal(self):
        self.set_users()
        tester = app.test_client(self)
        x1 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_short_text', status_code=200, status_message='Create #1', flag=False)
        x2 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_long_text', status_code=200, status_message='Create #2', flag=False)
        x3 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_image', status_code=200, status_message='Create #3', flag=False)
        x4 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_video', status_code=200, status_message='Create #4', flag=False)
        x5 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_short_text', status_code=403, status_message='Should not appear', flag=False)
        db.session.add(x1)
        db.session.add(x2)
        db.session.add(x3)
        db.session.add(x4)
        db.session.add(x5)
        db.session.commit()
        tester.post('/login', data=dict(email='harrison@beatles.com', password='cant-buy-me-love'), follow_redirects=True)
        response = tester.get('/admin/sentry/create/success')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Create #1', response.data)
        self.assertIn(b"ERROR: You don't have permission to do that.", response.data)


    def test_createFail_normal(self):
        self.set_users()
        tester = app.test_client(self)
        x1 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_short_text', status_code=403, status_message='Create #1', flag=False)
        x2 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_long_text', status_code=403, status_message='Create #2', flag=False)
        x3 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_image', status_code=403, status_message='Create #3', flag=False)
        x4 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_video', status_code=403, status_message='Create #4', flag=False)
        x5 = Sentry(ip_address='A', user_id=2, domain_id=1, endpoint='main.create_short_text', status_code=200, status_message='Should not appear', flag=False)
        db.session.add(x1)
        db.session.add(x2)
        db.session.add(x3)
        db.session.add(x4)
        db.session.add(x5)
        db.session.commit()
        tester.post('/login', data=dict(email='epstein@beatles.com', password='yellow-submarine'), follow_redirects=True)
        response = tester.get('/admin/sentry/create/fail', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create #1', response.data)
        self.assertIn(b'Create #2', response.data)
        self.assertIn(b'Create #3', response.data)
        self.assertIn(b'Create #4', response.data)
        self.assertNotIn(b'Should not appear', response.data)



if __name__ == "__main__":
    unittest.main()