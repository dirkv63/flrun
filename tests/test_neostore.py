"""
This procedure will test the neostore functionality.
"""

import unittest
import uuid

from competition import create_app, neostore
from datetime import date

# Import py2neo to test on class types
from py2neo import Node


# @unittest.skip("Focus on Coverage")
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
        self.ns.init_graph()
#       my_env.init_loghandler(__name__, "c:\\temp\\log", "warning")

    def tearDown(self):
        self.app_ctx.pop()

    def test_clear_locations(self):
        # Count number of location nodes. Add two locations.
        # Count number of locations again. Difference must be 2.
        # Clear locations. List After must be equal to list before.
        loc_label = 'Location'
        bef_list = self.ns.get_nodes(loc_label)
        bef_list_length = len(bef_list)
        new_loc = {
            'city': str(uuid.uuid4())
        }
        self.ns.create_node(loc_label, **new_loc)
        new_loc['city'] = str(uuid.uuid4())
        self.ns.create_node(loc_label, **new_loc)
        create_list = self.ns.get_nodes(loc_label)
        create_length = len(create_list)
        self.assertEqual(bef_list_length+2, create_length)
        self.ns.clear_locations()
        aft_list = self.ns.get_nodes(loc_label)
        # Not sure if lists will return in same sequence...
        self.assertEqual(bef_list, aft_list)

    def test_date(self):
        # This function tests the date_node method, remove_date and the clear_date_node method.
        nr_nodes = len(self.ns.get_nodes())
        # Set Dates
        dsd = date(year=1963, month=7, day=2)
        self.ns.date_node(dsd)
        dsc = date(year=1964, month=10, day=28)
        self.ns.date_node(dsc)
        # Number of nodes +3: Year - Month - Day
        ds_nr_nodes = len(self.ns.get_nodes())
        self.assertEqual(nr_nodes+6, ds_nr_nodes)
        # Test to set date from string
        self.assertTrue(isinstance(self.ns.date_node("1963-07-02"), Node))
        # Test date from invalid string is False
        self.assertFalse(isinstance(self.ns.date_node("OngeldigeDatum"), Node))
        self.ns.clear_date()
        # Check number of nodes back to original number
        ds_nr_nodes = len(self.ns.get_nodes())
        self.assertEqual(nr_nodes, ds_nr_nodes)

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
        # Invalid start node ID
        self.assertFalse(self.ns.get_end_node(start_node_id="BestaatNiet", rel_type="OokNiet"))
        # More than 1 end node
        node_id = "53db6b6c-45cc-4ed8-bb63-93ff40e5c101"
        self.assertTrue(self.ns.get_end_node(start_node_id=node_id, rel_type="is"))

    def test_get_end_nodes(self):
        # Test if I get list back. 'Dirk Van Dijck participated in 4 races"
        node_id = "53db6b6c-45cc-4ed8-bb63-93ff40e5c101"
        rel_type = "is"
        # I need to get a list back
        res = self.ns.get_end_nodes(start_node_id=node_id, rel_type=rel_type)
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 4)
        # Invalid relation needs to return False
        node_id = "5971e8ce-bffc-48d1-997d-654e6610ada5"
        self.assertFalse(self.ns.get_end_nodes(start_node_id=node_id, rel_type=rel_type))
        # Invalid start node needs to return False
        self.assertFalse(self.ns.get_end_nodes(start_node_id="Ongeldig", rel_type=rel_type))

    def test_get_start_node(self):
        # Test for non-existing end node
        node_id = "BestaatNiet"
        self.assertFalse(self.ns.get_start_node(end_node_id=node_id, rel_type="BestaatNiet"))
        rel_type = "participates"
        node_id = "494fd20a-a0a1-4fa4-a24c-6950285efffc"
        self.assertTrue(self.ns.get_start_node(end_node_id=node_id, rel_type=rel_type))

    def test_get_start_nodes(self):
        # Test for non-existing end node
        node_id = "BestaatNiet"
        self.assertFalse(self.ns.get_start_nodes(end_node_id=node_id, rel_type="BestaatNiet"))

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
        self.assertEqual(len(self.ns.get_nodes()), 133)
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
        # Return tuple of race nid and organization name
        (race_nid, org_name) = self.ns.get_race_in_org(org_id, racetype_id, name)
        self.assertEqual(race_nid, "a41af63a-5039-405c-b5eb-289481fab82b")
        self.assertEqual(org_name, "Parel Der Kempen")
        # An invalid race
        self.assertFalse(self.ns.get_race_in_org(org_id, racetype_id, "109 km"))

    def test_get_race_label(self):
        # For a valid Race ID I want to have a dictionary back.
        race_id = "b484cf1d-e2ad-43d0-84a7-e2f3e25bba5e"
        res = self.ns.get_race_label(race_id)
        self.assertTrue(isinstance(res, dict))
        # For this Race ID I want to get Organization name
        self.assertEqual(res["org"], "Rivierenhofloop")
        # For an invalid Race ID I want to get a False back.
        race_id = "0db8a807-eb25-4494-9c9c-29ef2a2df764"
        self.assertFalse(self.ns.get_race_label(race_id))

    def test_get_race_list(self):
        # For an organization I need to get a list of race dictionaries. For this organization I want to get 2 races.
        org_id = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        res = self.ns.get_race_list(org_id)
        # Do I get a list?
        self.assertTrue(isinstance(res, list))
        # Each entry needs to be a dictionary
        org = res[1]
        self.assertTrue(isinstance(org, dict))
        # I need to have 2 organizations in return
        self.assertEqual(len(res), 2)
        # Test what will happen if I ask for organization without races.
        org_id = "BestaatNiet"
        self.assertFalse(self.ns.get_race_list(org_id))

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
        result_dict = res[1]
        race = result_dict["race"]
        self.assertTrue(isinstance(race, dict))
        race_id=race["nid"]
        self.assertTrue(isinstance(race_id, str))
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

    def test_node_id(self):
        node_id = "ea83be48-fa39-4f6b-8f57-4952283997b7"
        self.assertFalse(self.ns.node_id(node_id))

    def test_node_no_nid(self):
        # Function to test setting of nids on nodes.
        # Initially every node should have a nid.
        self.assertEqual(self.ns.get_nodes_no_nid(), 0)
        # Then add date for new year
        ds = "1987-10-03"
        self.ns.date_node(ds)
        # Check that date node with month has nid
        props = dict(key="1987-10")
        node = self.ns.get_node(**props)
        self.assertTrue(isinstance(node["nid"], str))
        # Remove date nodes
        self.ns.clear_date()

    def test_node_props(self):
        # This method will test node_props and node_update
        nid = "0857952c-6a80-438e-b9a0-b25825b70a64"
        my_props = self.ns.node_props(nid)
        self.assertEqual(my_props["name"], "Dirk Vermeylen")
        self.assertEqual(my_props["nid"], nid)
        name_orig = my_props["name"]
        name_upd = "kweenie"
        add_attrib = "add_attrib"
        my_props["name"] = name_upd
        my_props[add_attrib] = add_attrib
        self.ns.node_update(**my_props)
        my_props = self.ns.node_props(nid)
        self.assertEqual(my_props["name"], name_upd)
        self.assertEqual(my_props["nid"], nid)
        self.assertEqual(len(my_props), 4)
        my_props["name"] = name_orig
        del my_props[add_attrib]
        self.ns.node_update(**my_props)
        my_props = self.ns.node_props(nid)
        self.assertEqual(len(my_props), 3)
        self.assertEqual(my_props["name"], "Dirk Vermeylen")
        # Remove nid from my_props, Test on node_update return False
        del my_props["nid"]
        self.assertFalse(self.ns.node_update(**my_props))
        # Test for invalid nid
        my_props["nid"] = "Ongeldig"
        self.assertFalse(self.ns.node_update(**my_props))
        self.assertFalse(self.ns.node_props("Ongeldig"))

    def test_relations(self):
        # Try to remove node with relations. This will test the methods remove_node and relations.
        nid = "0857952c-6a80-438e-b9a0-b25825b70a64"
        self.assertFalse(self.ns.remove_node(nid))
        # Try to remove invalid node nid
        nid = "BestaatNiet"
        self.assertFalse(self.ns.remove_node(nid))
        self.assertFalse(self.ns.relations(nid))

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
