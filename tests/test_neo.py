"""
This procedure will test the neostore functionality.
"""

import unittest

from competition import create_app, neostore

# Import py2neo to test on class types
from py2neo import Node


class TestNeoStore(unittest.TestCase):

    def setUp(self):
        # Initialize Environment
        """
        neo4j_params = {
            'user': "neo4j",
            'password': "_m8z8IpJUPyR",
            'db': "stratenloop15.db"
        }
        """
        self.app = create_app('testing')
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        self.ns = neostore.NeoStore()
#       my_env.init_loghandler(__name__, "c:\\temp\\log", "warning")

    def tearDown(self):
        self.app_ctx.pop()

    def test_get_participant_in_race(self):
        # Valid relation, return single node
        part_node = self.ns.get_participant_in_race(pers_id="0b306bd0-7c88-43b9-8657-a644486e377d",
                                                    race_id="df504d4b-b4b6-4b4f-b1d9-304092850324")
        self.assertTrue(isinstance(part_node, Node))
        self.assertEqual(part_node["nid"], "da9c7b42-5a08-4e6a-8b35-d019ffadc1c2")
        # Relation that doesn't exist, return False
        part_node = self.ns.get_participant_in_race(pers_id="df504d4b-b4b6-4b4f-b1d9-304092850324",
                                                    race_id="0b306bd0-7c88-43b9-8657-a644486e377d")
        self.assertTrue(isinstance(part_node, bool))
        self.assertEqual(part_node, False)

    def test_get_end_node(self):
        # Test if relation does not exist, do we have a valid end-node?
        # Valid organization, type Wedstrijd so nid is the return value, check for True
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        self.assertTrue(self.ns.get_end_node(org_id, "type"))
        # Invalid organization ID, I need False as Reply
        org_id = "9d26d01c-d961-47ca-9e45-d32dcc4413a0"
        self.assertFalse(self.ns.get_end_node(org_id, "type"))
        # Check if I get organization types
        org_id = "7ba23dbc-9514-439b-a7b3-9d630972f68c"
        org_type_id = self.ns.get_end_node(start_node_id=org_id, rel_type="type")
        org_type_node = self.ns.node(org_type_id)
        self.assertEqual(org_type_node["name"], "Wedstrijd")
        org_id = "0db8a807-eb25-4494-9c9c-29ef2a2df764"
        org_type_id = self.ns.get_end_node(start_node_id=org_id, rel_type="type")
        org_type_node = self.ns.node(org_type_id)
        self.assertEqual(org_type_node["name"], "Deelname")

    def test_get_end_nodes(self):
        # Test if I get list back. 'Dirk Van Dijck participated in 4 races"
        node_id = "53db6b6c-45cc-4ed8-bb63-93ff40e5c101"
        rel_type = "is"
        # I need to get a list back
        res = self.ns.get_end_nodes(start_node_id=node_id, rel_type=rel_type)
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 4)
        # Unexistent relation needs to return False
        node_id = "5971e8ce-bffc-48d1-997d-654e6610ada5"
        self.assertFalse(self.ns.get_end_nodes(start_node_id=node_id, rel_type=rel_type))

    def test_get_node(self):
        # This will test get_nodes in the same go.
        # Get a single node
        label = "Person"
        props = {
            "name": "Dirk Vermeylen"
        }
        self.assertEqual(self.ns.get_node(label, **props)["name"], "Dirk Vermeylen")
        # Too many returns
        self.assertTrue(isinstance(self.ns.get_node(label), Node))
        # No node returned, Return value is False
        self.assertFalse(self.ns.get_node("Label bestaat niet", **props))
        # Test for get_organization_type
        props = {
            "name": "Wedstrijd"
        }
        org_node = self.ns.get_node("OrgType", **props)
        self.assertEqual(org_node["name"], "Wedstrijd")

    def test_get_nodes(self):
        # Return list of all nodes
        self.assertEqual(len(self.ns.get_nodes()), 132)
        # Return list of all Races
        label = "Race"
        self.assertEqual(len(self.ns.get_nodes(label)), 18)
        # Races of 10 km
        props = {
            "name": "10 km"
        }
        self.assertEqual(len(self.ns.get_nodes(label, **props)), 5)

    def test_get_organization(self):
        org_dict = {
            "name": "RAM",
            "location": "Mechelen",
            "datestamp": "2015-04-19"
        }
        self.assertEqual(self.ns.get_organization(**org_dict), "726d030b-e80c-4a1f-8cbd-86cade4ea090")
        # Test on non-existing Organization
        org_dict["name"] = "Erps Kwerps"
        self.assertFalse(self.ns.get_organization(**org_dict))

    def test_get_organization_by_id(self):
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        # Get date and city for the organization
        self.assertEqual(self.ns.get_organization_from_id(org_id)["date"], "2015-05-17")
        self.assertEqual(self.ns.get_organization_from_id(org_id)["city"], "Oostmalle")
        # Check for invalid org_id
        org_id = "9d26d01c-d961-47ca-9e45-d32dcc4413a0"
        self.assertFalse(self.ns.get_organization_from_id(org_id))

    def test_get_organization_list(self):
        # I need to have a list of organization dictionaries. I need to get 9 organizations back.
        res = self.ns.get_organization_list()
        # Do I get a list?
        self.assertTrue(isinstance(res, list))
        # Each entry needs to be a dictionary
        org = res[4]
        self.assertTrue(isinstance(org, dict))
        # I need to have 9 organizations in return
        self.assertEqual(len(res), 9)

    def test_get_participant_seq_list(self):
        # Test if I get a participant list for a race_id
        race_id = "332e1cce-e73e-4a87-bf78-acbdd05cbda3"
        res = self.ns.get_participant_seq_list(race_id)
        print("Res: {}".format(res))
        self.assertTrue(isinstance(res, list))
        self.assertTrue(isinstance(res[0], Node))
        """
        node_list = neostore.nodelist_from_cursor(res)
        print("{}".format(type(node_list)))
        self.assertTrue(isinstance(res, list))
        """
        # Test for race without participants
        race_id = "a0d3ffb2-5fd3-42fb-909d-11f1c635fdc6"
        self.assertFalse(self.ns.get_participant_seq_list(race_id))

    def test_get_race_in_org(self):
        # A valid race in an organization
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        racetype_id = "38c4984e-5303-42e9-8adc-f671bbc4bf72"
        name = "9 km"
        self.assertEqual(self.ns.get_race_in_org(org_id, racetype_id, name), 1)
        self.assertFalse(self.ns.get_race_in_org(org_id, racetype_id, "109 km"))

    def test_get_race_label(self):
        # For a vaild Race ID I want to have a dictionary back.
        race_id = "b484cf1d-e2ad-43d0-84a7-e2f3e25bba5e"
        res = self.ns.get_race_label(race_id)
        self.assertTrue(isinstance(res, dict))
        # For this Race ID I want to get Organization name
        self.assertEqual(res["org"], "Rivierenhofloop")
        # For an invalid Race ID I want to get a False back.
        race_id = "0db8a807-eb25-4494-9c9c-29ef2a2df764"
        self.assertFalse(self.ns.get_race_label(race_id))

    def test_get_race_list(self):
        # For an organization I need to get a list of race dictionaries. For this organiztaion I want to get 2 races.
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        res = self.ns.get_race_list(org_id)
        # Do I get a list?
        self.assertTrue(isinstance(res, list))
        # Each entry needs to be a dictionary
        org = res[1]
        self.assertTrue(isinstance(org, dict))
        # I need to have 2 organizations in return
        self.assertEqual(len(res), 2)

    def test_get_race4person(self):
        # I want to get a list of dictionaries.
        person_id = "0857952c-6a80-438e-b9a0-b25825b70a64"
        res = self.ns.get_race4person(person_id)
        self.assertTrue(isinstance(res, list))
        # I want to have x races in the list.
        self.assertEqual(len(res), 3)
        # Each Entry needs to be a dictionary
        self.assertTrue(isinstance(res[1], dict))
        # The dictionary consists of a valid node, referring to a race.
        race = res[1]
        race_id = race["race_id"]
        self.assertTrue(isinstance(race_id, str))
        race_node = self.ns.node(race_id)
        self.assertTrue(isinstance(race_node, Node))
        # For an invalid Person ID, I need to get a False back.
        person_id = "ccbb1440-382e-43c2-9e5f-6c91c5a5f9da"
        self.assertFalse(self.ns.get_race4person(person_id))

    def test_get_wedstrijd_type(self):
        # Check for valid combination
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        racetype = "Hoofdwedstrijd"
        self.assertEqual(self.ns.get_wedstrijd_type(org_id, racetype), 1)
        # Check for invalid racetype
        racetype = "XXX"
        self.assertFalse(self.ns.get_wedstrijd_type(org_id, racetype))
        # Check for invalid org_id
        org_id = "9d26d01c-d961-47ca-9e45-d32dcc4413a0"
        racetype = "Hoofdwedstrijd"
        self.assertFalse(self.ns.get_wedstrijd_type(org_id, racetype))

    def test_node(self):
        node_id = "ea83be48-fa39-4f6b-8f57-4952283997b7"
        self.assertTrue(isinstance(self.ns.node(node_id), Node))
        self.assertFalse(self.ns.node("NodeIDDoesNotExist"))

    def test_validate_node(self):
        # Validate Participant
        part_node = self.ns.get_participant_in_race(pers_id="0b306bd0-7c88-43b9-8657-a644486e377d",
                                                    race_id="df504d4b-b4b6-4b4f-b1d9-304092850324")
        self.assertTrue(neostore.validate_node(part_node, "Participant"))
        # Accept invalid node
        self.assertFalse(neostore.validate_node("Participant", "Participant"))
        # Accept invalid label
        self.assertFalse(neostore.validate_node(part_node, "XXX_Participant"))

if __name__ == "__main__":
    unittest.main()
