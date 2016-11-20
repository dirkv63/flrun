"""
This procedure will test the neostore functionality.
"""

import unittest
from lib import my_env, neostore


class TestNeoStore(unittest.TestCase):

    def setUp(self):
        # Initialize Environment
        neo4j_params = {
            'user': "neo4j",
            'password': "_m8z8IpJUPyR",
            'db': "stratenloop15.db"
        }
        self.ns = neostore.NeoStore(**neo4j_params)
        my_env.init_loghandler(__name__, "c:\\temp\\log", "warning")

    def test_get_participant_in_race(self):
        # Valid relation, return single node
        part_node = self.ns.get_participant_in_race(pers_id="0b306bd0-7c88-43b9-8657-a644486e377d",
                                                    race_id="df504d4b-b4b6-4b4f-b1d9-304092850324")
        self.assertEqual(str(type(part_node)), "<class 'py2neo.types.Node'>")
        self.assertEqual(part_node["nid"], "da9c7b42-5a08-4e6a-8b35-d019ffadc1c2")
        # Relation that doesn't exist, return False
        part_node = self.ns.get_participant_in_race(pers_id="df504d4b-b4b6-4b4f-b1d9-304092850324",
                                                    race_id="0b306bd0-7c88-43b9-8657-a644486e377d")
        self.assertEqual(str(type(part_node)), "<class 'bool'>")
        self.assertEqual(part_node, False)

    def test_get_end_node(self):
        # Test if relation does not exist, do we have a valid end-node?
        # Valid organization, type Wedstrijd so nid is the return value, check for True
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        self.assertTrue(self.ns.get_end_node(org_id, "type"))
        # Invalid organization ID, I need False as Reply
        org_id = "9d26d01c-d961-47ca-9e45-d32dcc4413a0"
        self.assertFalse(self.ns.get_end_node(org_id, "type"))

    def test_get_end_nodes(self):
        # Test if I get list back. 'Dirk Van Dijck participated in 4 races"
        node_id = "53db6b6c-45cc-4ed8-bb63-93ff40e5c101"
        rel_type = "is"
        # I need to get a list back
        self.assertEqual(str(type(self.ns.get_end_nodes(start_node_id=node_id, rel_type=rel_type))), "<class 'list'>")
        self.assertEqual(len(self.ns.get_end_nodes(start_node_id=node_id, rel_type=rel_type)), 4)
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
        self.assertEqual(str(type(self.ns.get_node(label))), "<class 'py2neo.types.Node'>")
        # No node returned, Return value is False
        self.assertFalse(self.ns.get_node("Label bestaat niet", **props))

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

    def test_get_race_in_org(self):
        # A valid race in an organization
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        racetype_id = "38c4984e-5303-42e9-8adc-f671bbc4bf72"
        name = "9 km"
        self.assertEqual(self.ns.get_race_in_org(org_id, racetype_id, name), 1)
        self.assertFalse(self.ns.get_race_in_org(org_id, racetype_id, "109 km"))

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
        self.assertEqual(str(type(self.ns.node(node_id))), "<class 'py2neo.types.Node'>")
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
