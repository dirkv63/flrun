"""
This procedure will test the models_graph functionality.
"""

import unittest
from competition import create_app, models_graph as mg, neostore
from lib import my_env
from py2neo import Node


class TestModelGraph(unittest.TestCase):

    def setUp(self):
        # Initialize Environment
        self.app = create_app('testing')
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        my_env.init_loghandler(__name__, "c:\\temp\\log", "warning")
        self.ns = neostore.NeoStore()

    def tearDown(self):
        self.app_ctx.pop()

    def test_get_races_for_org(self):
        # Enter an organization ID, check if we get a list of nids of all races back
        org_id = "7ba23dbc-9514-439b-a7b3-9d630972f68c"
        races = mg.get_races_for_org(org_id)
        self.assertTrue(isinstance(races, list))
        self.assertEqual(len(races), 2)
        race_nid = races[1]
        race_node = self.ns.node(race_nid)
        self.assertTrue(isinstance(race_node, Node))
        self.assertTrue(neostore.validate_node(race_node, "Race"))

    def test_get_org_id(self):
        # Enter a race_id, get an organization nid back
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        org_id = mg.get_org_id(race_id)
        self.assertTrue(org_id, str)
        org_node = self.ns.node(org_id)
        self.assertTrue(isinstance(org_node, Node))
        self.assertTrue(neostore.validate_node(org_node, "Organization"))

    def test_next_participants(self):
        # For a specific Race, select the list of potential next participants
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        next_part = mg.next_participant(race_id)
        # This needs to be a list
        self.assertTrue(isinstance(next_part, list))
        self.assertEqual(len(next_part), 12)
        # Each entry needs to be a person object: dictionary with id, name
        person_node = next_part[8]
        self.assertTrue(isinstance(person_node, list))
        self.assertTrue(isinstance(person_node[0], str))
        self.assertTrue((isinstance(person_node[1], str)))

    def test_participant_after_list(self):
        # This is the participant_seq_list, with an object [-1, "Eerste Aankomst"] prepended
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        person_list = mg.participant_after_list(race_id)
        self.assertTrue(isinstance(person_list, list))
        self.assertEqual(len(person_list), 7)
        # Check First Person object
        person_object = person_list[0]
        self.assertTrue(isinstance(person_object, list))
        self.assertEqual(len(person_object), 2)
        self.assertEqual(person_object[0], -1)
        self.assertEqual(person_object[1], "Eerste aankomst")

    def test_participant_last_id(self):
        # Get the nid of the last person in the race.
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        last_person_id = mg.participant_last_id(race_id)
        self.assertTrue(isinstance(last_person_id, str))
        last_person_nid = "fa439bde-0319-407b-9e80-d7c7a20957d9"
        self.assertEqual(last_person_id, last_person_nid)

    def test_participant_list(self):
        # Get the List of participants for this race
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        part_list = mg.participant_list(race_id)
        self.assertTrue(isinstance(part_list, list))
        self.assertEqual(len(part_list), 6)
        participant = part_list[5]
        self.assertTrue(isinstance(participant, list))
        self.assertTrue(isinstance(participant[0], str))
        self.assertTrue(isinstance(participant[1], str))

    def test_participant_seq_list(self):
        # Get a dictionary of Person objects for a race nid.
        # A Person object is a list of person NID and Person Name.
        # Braderijloop Schoten - 10 km
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        person_list = mg.participant_seq_list(race_id)
        self.assertTrue(isinstance(person_list, list))
        self.assertEqual(len(person_list), 6)
        # Check for Person object
        person_object = person_list[3]
        self.assertTrue(isinstance(person_object, list))
        self.assertEqual(len(person_object), 2)
        self.assertTrue(isinstance(person_object[0], str))
        self.assertTrue(isinstance(person_object[1], str))
        # Check for race without participants. This should return False.
        race_id = "a0d3ffb2-5fd3-42fb-909d-11f1c635fdc6"
        person_list = mg.participant_seq_list(race_id)
        self.assertFalse(person_list)

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
        self.assertTrue(isinstance(person, list))
        self.assertTrue(isinstance(person[0], str))
        self.assertTrue(isinstance(person[1], str))

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
