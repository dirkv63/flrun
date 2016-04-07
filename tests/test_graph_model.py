import unittest
from competition import create_app, db
from competition.models_sql import User
from py2neo import Graph


class GraphModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        db.create_all()
        self.graph = Graph()
        self.graph_db_empty()
        self.client = self.app.test_client(use_cookies=True)
        User.register('dirk', 'olse')
        self.test_login()

    def tearDown(self):
        # self.graph.unbind()
        db.drop_all()
        self.app_ctx.pop()

    def test_graph_availability(self):
        query = "match (n) return count(*) as cnt"
        cnt = self.graph.cypher.execute(query)
        self.assertEqual(cnt[0].cnt, 33)

    def graph_db_empty(self):
        query = "match (n) return count(*) as cnt"
        cnt = self.graph.cypher.execute(query)
        try:
            assert cnt[0].cnt == 33
        except Exception as e:
            print("Environment is not clean!")
            raise e

    def test_graph_find_user(self):
        r = self.client.get('/participant/list')
        self.assertEqual(r.status_code, 200)
        self.assertTrue('<td>Jean-Pierre</td>' in r.get_data(as_text=True))
        self.assertFalse('<td>Dirkske</td>' in r.get_data(as_text=True))

    def test_login(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)
        self.assertTrue('<h1>Login</h1>' in r.get_data(as_text=True))
        r = self.client.post('/login',
                             data={'username': 'dirk', 'password': 'olse'},
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        return

    def test_register_user(self):
        r = self.client.get('/participant/register')
        self.assertEqual(r.status_code, 200)
        self.assertTrue('<h2>Register Participant</h2>' in r.get_data(as_text=True))
        r = self.client.post('/participant/register',
                             data={'name': 'James Bond'},
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
