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
        part_node = self.ns.get_participant_in_race(pers_id=15, race_id=17)
        self.assertEqual(str(type(part_node)), "<class 'py2neo.types.Node'>")
        self.assertEqual(part_node["nid"], 38)
        # Relation that doesn't exist, return False
        part_node = self.ns.get_participant_in_race(pers_id=17, race_id=15)
        self.assertEqual(str(type(part_node)), "<class 'bool'>")
        self.assertEqual(part_node, False)

    def test_validate_node(self):
        # Validate Participant
        part_node = self.ns.get_participant_in_race(pers_id=15, race_id=17)
        self.assertTrue(neostore.validate_node(part_node, "Participant"))
        # Accept invalid node
        self.assertFalse(neostore.validate_node("Participant", "Participant"))
        # Accept invalid label
        self.assertFalse(neostore.validate_node(part_node, "XXX_Participant"))

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

    def test_get_organization(self):
        org_dict = {
            "name": "RAM",
            "location": "Mechelen",
            "datestamp": "2015-04-19"
        }
        self.assertEqual(self.ns.get_organization(**org_dict), 12)
        # Test on non-existing Organization
        org_dict["name"] = "Erps Kwerps"
        self.assertFalse(self.ns.get_organization(**org_dict))

if __name__ == "__main__":
    unittest.main()
