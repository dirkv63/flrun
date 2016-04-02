import unittest
from competition import create_app, db
from competition.sql_models import User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        db.create_all()

    def tearDown(self):
        db.drop_all()
        self.app_ctx.pop()

    def test_password(self):
        u = User()
        u.username = 'dirk'
        u.set_password('olse')
        self.assertTrue(u.verify_password('olse'))
        self.assertFalse(u.verify_password('xolse'))

    def test_registration(self):
        User.register('dirk', 'olse')
        u = User.query.filter_by(username='dirk').first()
        self.assertIsNotNone(u)
        self.assertTrue(u.verify_password('olse'))
        self.assertFalse(u.verify_password('dog'))
