"""
This procedure will test the models_graph functionality.
"""

import unittest
from competition import create_app, models_graph as mg
from lib import my_env


class TestModelGraph(unittest.TestCase):

    def setUp(self):
        # Initialize Environment
        self.app = create_app('testing')
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        my_env.init_loghandler(__name__, "c:\\temp\\log", "warning")

    def tearDown(self):
        self.app_ctx.pop()

    def test_person(self):
        pers_id = "0857952c-6a80-438e-b9a0-b25825b70a64"
        person = mg.Person()
        person.set(pers_id)
        self.assertTrue(isinstance(person, mg.Person))
        self.assertEqual(person.get(), "Dirk Vermeylen")

    def test_person_list(self):
        # Person list, check if list is back.
        person_list = mg.person_list()
        self.assertTrue(isinstance(person_list, list))
        self.assertEqual(len(person_list), 25)
        # Person list should be  a list of dictionaries
        person = person_list[12]
        self.assertTrue(isinstance(person, dict))
        self.assertTrue(isinstance(person["name"], str))
        self.assertTrue(isinstance(person["id"], str))

    def test_races4person(self):
        # ID for Dirk Vermeylen
        pers_id = "0857952c-6a80-438e-b9a0-b25825b70a64"
        races = mg.races4person(pers_id)
        self.assertTrue(isinstance(races, list))
        # Participated in 3 races
        self.assertEqual(len(races), 3)
        print("Races: {}".format(races))
        # Dictionary has fields race_id and race_label
        race = races[2]
        self.assertTrue(isinstance(race, dict))
        self.assertTrue(isinstance(race['race_id'], str))
        self.assertTrue(isinstance(race['race_label'], str))

if __name__ == "__main__":
    unittest.main()
