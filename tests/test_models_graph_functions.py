"""
This procedure will test the functions of the models_graph module.
"""

import unittest
from competition import create_app, models_graph as mg, neostore
from py2neo import Node


# @unittest.skip("Focus on Coverage")
class TestModelGraph(unittest.TestCase):

    def setUp(self):
        # Initialize Environment
        # my_env.init_loghandler(__name__, "c:\\temp\\log", "warning")
        self.app = create_app('testing')
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        self.ns = neostore.NeoStore()

    def tearDown(self):
        self.app_ctx.pop()

    def test_get_org_type(self):
        # Check if I get org Type back for Wedstrijd or Deelname
        # Check on invalid node
        org_type_nid = "726d030b-e80c-4a1f-8cbd-86cade4ea090"
        self.assertEqual(mg.get_org_type(org_type_nid), "Wedstrijd")
        org_type_nid = "ea83be48-fa39-4f6b-8f57-4952283997b7"
        self.assertEqual(mg.get_org_type(org_type_nid), "Deelname")
        # Not ID of an organization
        org_type_nid = "cf36c737-5171-41ba-b621-c66de41b6209"
        self.assertFalse(mg.get_org_type(org_type_nid))
        # Not an node at all
        self.assertFalse(mg.get_org_type("BestaatNiet"))

    def test_get_org_type_node(self):
        # Return node for Wedstrijd in case org_type_id = 1,
        # Return node for Deelname in any other case
        org_type_id = 1
        org_type_node = mg.get_org_type_node(org_type_id)
        self.assertTrue(isinstance(org_type_node, Node))
        self.assertEqual(org_type_node["name"], "Wedstrijd")
        org_type_id = 2
        org_type_node = mg.get_org_type_node(org_type_id)
        self.assertTrue(isinstance(org_type_node, Node))
        self.assertEqual(org_type_node["name"], "Deelname")
        org_type_node = mg.get_org_type_node("BestaatNiet")
        self.assertTrue(isinstance(org_type_node, Node))
        self.assertEqual(org_type_node["name"], "Deelname")

    def test_get_org_id(self):
        # Enter a race_id, get an organization nid back
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        org_id = mg.get_org_id(race_id)
        self.assertTrue(org_id, str)
        org_node = self.ns.node(org_id)
        self.assertTrue(isinstance(org_node, Node))
        self.assertTrue(neostore.validate_node(org_node, "Organization"))

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

    def test_get_race_type_node(self):
        # Check on valid / invalid race types
        race_types = ["Hoofdwedstrijd", "Bijwedstrijd", "Deelname"]
        for race_type in race_types:
            self.assertTrue(isinstance(mg.get_race_type_node(race_type), Node))
        self.assertFalse(mg.get_race_type_node("Ongeldig"))

    def test_next_participant(self):
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

    # def test_organization_delete(self):
    #   This test is done in test_models_graph_classes.py

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

    def test_participant_finisher_list(self):
        # Check for race_id Halve Marathon Lier
        race_id = "7ff512b5-7ea3-48ed-86bd-058e791d6a31"
        first_nid = mg.participant_first_id(race_id)
        # First finisher is Kevin Kennis
        exp_first_nid = "1c727f4c-7423-428f-bdb8-08575031d181"
        self.assertEqual(first_nid, exp_first_nid)
        # Race without participants - Groenteloop Schriek, 10,7km
        race_id = "a0d3ffb2-5fd3-42fb-909d-11f1c635fdc6"
        first_nid = mg.participant_first_id(race_id)
        self.assertFalse(first_nid)

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
        self.assertTrue(isinstance(person_object, tuple))
        self.assertEqual(len(person_object), 2)
        self.assertTrue(isinstance(person_object[0], dict))
        self.assertTrue(isinstance(person_object[1], dict))
        # Check for race without participants. This should return False.
        race_id = "a0d3ffb2-5fd3-42fb-909d-11f1c635fdc6"
        person_list = mg.participant_seq_list(race_id)
        self.assertFalse(person_list)

    def test_person4participant(self):
        # For a valid participant id, I need to get person name and id back
        # For an invalide participant id, I want to get False back
        part_nid = "aaca43c8-0c35-4d32-9ccb-b3c9eee3eeec"
        person = mg.person4participant(part_nid)
        self.assertEqual(person["name"], "Ann Smet")
        self.assertEqual(person["nid"], "f9414813-fb14-4370-b609-19312adfbd8e")
        part_nid = "BestaatNiet"
        self.assertFalse(mg.person4participant(part_nid))

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

    def test_race_delete(self):
        # Try to delete a race with participants
        # This should fail and return False
        race_id = "df504d4b-b4b6-4b4f-b1d9-304092850324"
        self.assertFalse(mg.race_delete(race_id))

    def test_race_list(self):
        # For a valid organization ID I need to get a race list back
        # For an invalide organization ID False needs to be returned
        org_id = "e92399b0-c143-4696-8543-6b10715817b2"
        races = mg.race_list(org_id)
        self.assertTrue(isinstance(races, list))
        self.assertEqual(len(races), 3)
        # For a new organization ID I want to have a valid empty list
        org_id = "ea83be48-fa39-4f6b-8f57-4952283997b7"
        races = mg.race_list(org_id)
        self.assertTrue(isinstance(races, list))
        self.assertEqual(len(races), 0)
        org_id = "BestaatNiet"
        self.assertFalse(mg.race_list(org_id))

    def test_racetype_list(self):
        # Check if I get a list of tuples back. Each tuple must be a nid and a racetype name.
        rtl = mg.racetype_list()
        self.assertTrue(isinstance(rtl, list))
        self.assertTrue(isinstance(rtl[1], tuple))
        (nid, name) = rtl[2]
        self.assertTrue(isinstance(nid, str))
        self.assertTrue(isinstance(name, str))

    def test_races4person(self):
        # ID for Dirk Vermeylen
        pers_id = "0857952c-6a80-438e-b9a0-b25825b70a64"
        races = mg.races4person(pers_id)
        self.assertTrue(isinstance(races, list))
        # Participated in 3 races
        self.assertEqual(len(races), 3)
        # Dictionary has fields race_id and race_label
        race = races[2]
        self.assertTrue(isinstance(race, dict))
        self.assertTrue(isinstance(race['race'], dict))
        self.assertTrue(isinstance(race['part'], dict))

if __name__ == "__main__":
    unittest.main()
