import unittest
from competition import create_app, db
from competition.models_sql import User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()
        User.register('dirk', 'olse')

    def tearDown(self):
        db.drop_all()
        self.app_ctx.pop()

    def test_login(self):
        r = self.client.get_label('/login')
        self.assertEqual(r.status_code, 200)
        self.assertTrue('<h1>Login</h1>' in r.get_data(as_text=True))
        r = self.client.post('/login',
                             data={'username': 'dirk', 'password': 'olse'},
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue('<h1>Header for Running Competition</h1>' in r.get_data(as_text=True))
