"""
This procedure will test the classes of the models_graph.
"""

import unittest
from competition import create_app, models_graph as mg, neostore
# from py2neo import Node


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

    def test_class_participant(self):
        # Get Participant 'Luc Van der Welk' in race Lier - 21 km
        person_nid = "0edeb999-f682-4624-8c4e-4faf2c0ecdcb"     # Luc VDWelk
        race_nid = "7ff512b5-7ea3-48ed-86bd-058e791d6a31"       # Lier - 21 km
        participant_nid = "32783d1e-0552-4bc4-808c-89c499d106d2"
        # Get a participant object for existing race and person.
        part = mg.Participant(race_id=race_nid, pers_id=person_nid)
        self.assertTrue(isinstance(part, mg.Participant))
        part_nid = part.get_id()
        self.assertEqual(part_nid, participant_nid)
        # Add a person to a race
        add_person_nid = "08f75c0d-d554-4530-8800-2b85b4e86563"    # Benjamin
        add_part = mg.Participant(race_id=race_nid, pers_id=add_person_nid)
        self.assertTrue(isinstance(add_part, mg.Participant))
        # Add Person after LucVDW
        add_part.add(prev_pers_id=person_nid)
        # Check Benjamin is on Position 7 in the race
        part_seq_list = mg.participant_seq_list(race_id=race_nid)
        self.assertTrue(len(part_seq_list), 8)
        (person_dict, part_dict) = part_seq_list[6]
        self.assertTrue(isinstance(person_dict, dict))
        self.assertEqual(person_dict["label"], "Benjamin Tuffin")
        # Test to remove Benjamin from race
        add_part.remove()
        # Check that sequence of arrivals is back at 7
        part_seq_list = mg.participant_seq_list(race_id=race_nid)
        self.assertTrue(len(part_seq_list), 7)
        # Then add Benjamin as last participant in the race
        add_part = mg.Participant(race_id=race_nid, pers_id=add_person_nid)
        person_last_nid = "3be05e1c-56d4-4a4c-922b-b912dffcc339"     # Connie VDB
        add_part.add(prev_pers_id=person_last_nid)
        # Check Benjamin is on Position 8 in the race
        part_seq_list = mg.participant_seq_list(race_id=race_nid)
        self.assertTrue(len(part_seq_list), 8)
        (person_dict, part_dict) = part_seq_list[7]
        self.assertTrue(isinstance(person_dict, dict))
        print("Person Dict: {pd}".format(pd=person_dict))
        self.assertEqual(person_dict["label"], "Benjamin Tuffin")
        # Remove Benjamin from race
        add_part.remove()
        # And add as first person in the race
        """
        add_part = mg.Participant(race_id=race_nid, pers_id=add_person_nid)
        add_part.add()
        # Check Benjamin is first one in the race now, and the 8 participants are there
        part_seq_list = mg.participant_seq_list(race_id=race_nid)
        self.assertTrue(len(part_seq_list), 8)
        (person_dict, part_dict) = part_seq_list[0]
        self.assertEqual(person_dict["label"], "Benjamin Tuffin")
        # Remove Benjamin from race
        add_part.remove()
        """

    def test_class_participant_part_id(self):
        # Get Participant 'Luc Van der Welk' in race Lier - 21 km
        # Not sure if this combination is ever used?
        participant_nid = "32783d1e-0552-4bc4-808c-89c499d106d2"
        # Get a race and person for this participant.
        part = mg.Participant(part_id=participant_nid)
        self.assertTrue(isinstance(part, mg.Participant))

    def test_class_participant_empty_input(self):
        # Test No Input => Return False
        self.assertRaises(ValueError, lambda: mg.Participant())

    def test_class_person(self):
        # Check to set Person with ID
        person_nid = "0edeb999-f682-4624-8c4e-4faf2c0ecdcb"     # Luc VDWelk
        person = mg.Person(person_id=person_nid)
        self.assertTrue(isinstance(person, mg.Person))
        self.assertEqual(person.get(), 'Luc Van der Welk')
        person_nid = "BestaatNiet"
        self.assertRaises(ValueError, lambda: mg.Person(person_id=person_nid))

    def test_class_person_add(self):
        # Add a new person
        new_person = "Voornaam Familienaam"
        props = dict(name=new_person)
        person = mg.Person()
        self.assertTrue(person.add(**props))
        # Check person exists with this name
        self.assertEqual(person.get(), new_person)
        # Get nid for the person
        person_props = person.props()
        nid = person_props["nid"]
        # Check person is active - not active since no races attached.
        self.assertFalse(person.active())
        # Now try to create the person second time
        # This needs to return same nid
        person2 = mg.Person()
        self.assertFalse(person2.add(**props))
        person2_props = person2.props()
        nid2 = person2_props["nid"]
        self.assertEqual(nid, nid2)
        # Now try to get mf label
        self.assertFalse(person2.get_mf())
        # Set to 'vrouw'
        self.assertTrue(person2.set_mf("vrouw"))
        # Verify it is set to vrouw
        self.assertEqual(person2.get_mf(), "vrouw")
        # Remove Person again not to disturb other tests...
        # Check person is not active
        self.assertFalse(person2.active())
        self.ns.remove_node_force(nid2)

    def test_class_person_edit(self):
        nid = "0857952c-6a80-438e-b9a0-b25825b70a64"
        person = mg.Person(person_id=nid)
        props = person.props()
        self.assertEqual(nid, props["nid"])
        del props["nid"]
        self.assertTrue(person.edit(**props))
        props2 = person.props()
        self.assertEqual(nid, props2["nid"])

    def test_class_person_m2v(self):
        # Test get_mf, set from man to vrouw, then back (of course)
        nid = "f6c70583-6b16-4e28-afb7-3caacc4d4aa8"    # Jan
        person = mg.Person(person_id=nid)
        self.assertEqual(person.get_mf(), "man")
        self.assertTrue(person.set_mf("vrouw"))
        self.assertEqual(person.get_mf(), "vrouw")
        self.assertTrue(person.set_mf("man"))
        self.assertEqual(person.get_mf(), "man")
        # Return False if set already
        self.assertFalse(person.set_mf("man"))

    def test_class_organization(self):
        # Create New Organization
        org = mg.Organization()
        self.assertTrue(isinstance(org, mg.Organization))
        # Create Existing Organization
        org_nid = "436de584-4a6a-4ff4-b37e-b34b9e1c4df5"
        org = mg.Organization(org_id=org_nid)
        self.assertTrue(isinstance(org, mg.Organization))
        org_label = "Parel Der Kempen (Oostmalle, 17-05-2015)"
        self.assertEqual(org.get_label(), org_label)

    def test_class_organization_add_existing(self):
        # Try to add an existing organization, this needs to fail
        ds = "2015-05-17"
        loc = "Oostmalle"
        name = "Parel Der Kempen"
        org_type = "Wedstrijd"
        props = dict(name=name, location=loc, datestamp=ds, org_type=org_type)
        org = mg.Organization()
        self.assertFalse(org.add(**props))

    def test_class_organization_add_new(self):
        # Try to add a new organization
        ds = '1963-07-02'
        loc = "Nieuwe Loc"
        name = "Nieuwe wedstrijd"
        org_type = 1
        props = dict(name=name, location=loc, datestamp=ds, org_type=org_type)
        org = mg.Organization()
        self.assertTrue(org.add(**props))
        org_label = "Nieuwe wedstrijd (Nieuwe Loc, 02-07-1963)"
        self.assertEqual(org.get_label(), org_label)
        # Edit the organization
        # Set Type to Deelname
        props["org_type"] = 2
        self.assertTrue(org.edit(**props))
        # Type organization is changed, not Label
        self.assertEqual(org.get_label(), org_label)
        self.assertEqual(org.get_org_type(), 2)
        # Now change all attributes
        ds = "1964-10-28"
        loc = "Nog nieuwere Loc"
        name = "Nog Nieuwere wedstrijd"
        org_type = 1
        props = dict(name=name, location=loc, datestamp=ds, org_type=org_type)
        self.assertTrue(org.edit(**props))
        org_label = "Nog Nieuwere wedstrijd (Nog nieuwere Loc, 28-10-1964)"
        self.assertEqual(org.get_label(), org_label)
        nid = org.get_org_id()
        # Now try to configure an existing organization. This should be false.
        ds = '2015-04-19'
        loc = "Mechelen"
        name = "RAM"
        org_type = 1
        props = dict(name=name, location=loc, datestamp=ds, org_type=org_type)
        self.assertFalse(org.edit(**props))
        self.assertEqual(org.get_org_id(), "726d030b-e80c-4a1f-8cbd-86cade4ea090")
        # However, this will have set org_id to existing organization, so use old org to remove.
        # OK, now clean up the organization
        mg.organization_delete(nid)

    def test_class_organization_date(self):
        org_id = "726d030b-e80c-4a1f-8cbd-86cade4ea090"
        org = mg.Organization(org_id=org_id)
        self.assertEqual(org.get_location(), "Mechelen")
        self.assertEqual(org.get_date(), '2015-04-19')

    def test_class_organization_ask_for_hoofdwedstrijd(self):
        org_id = "ea83be48-fa39-4f6b-8f57-4952283997b7"
        org = mg.Organization(org_id=org_id)
        # Deelname => Geen Hoofdwedstrijd
        self.assertFalse(org.ask_for_hoofdwedstrijd())
        org_id = "e92399b0-c143-4696-8543-6b10715817b2"
        org = mg.Organization(org_id=org_id)
        # Wedstrijd met hoofdwedstrijd, so no need to ask for Hoofdwedstrijd
        self.assertFalse(org.ask_for_hoofdwedstrijd())
        # Create new organization for which Hoofdwedstrijd is not yet configured
        ds = '1963-07-02'
        loc = "Nieuwe Loc"
        name = "Nieuwe wedstrijd"
        org_type = 1
        props = dict(name=name, location=loc, datestamp=ds, org_type=org_type)
        org = mg.Organization()
        self.assertTrue(org.add(**props))
        nid = org.get_org_id()
        self.assertTrue(org.ask_for_hoofdwedstrijd())
        # OK, now clean up the organization
        mg.organization_delete(nid)

    def test_class_race_existing(self):
        # Set an existing Race
        race_id = "f99131fd-4092-461c-a7fd-95a42300883f"
        race = mg.Race(race_id=race_id)
        self.assertEqual(race.get_org_id(), "aec986a3-8205-4a21-aad6-963be88575ba")
        race_name = race.get_name()
        self.assertEqual(race_name, "9.9 km")
        new_name = "12 miles"
        self.assertTrue(race.edit(new_name))
        self.assertEqual(race.get_name(), new_name)
        # Reset to old name
        self.assertTrue(race.edit(race_name))

    def test_class_race_new(self):
        # Create an organization first
        ds = '1967-07-02'
        loc = "Nieuwe Loc"
        name = "Nieuwe wedstrijd"
        org_type = 1
        props = dict(name=name, location=loc, datestamp=ds, org_type=org_type)
        org = mg.Organization()
        self.assertTrue(org.add(**props))
        org_label = "Nieuwe wedstrijd (Nieuwe Loc, 02-07-1967)"
        self.assertEqual(org.get_label(), org_label)
        org_id = org.get_org_id()
        # Then add a race to the organization
        race = mg.Race(org_id=org_id)
        self.assertTrue(isinstance(race, mg.Race))
        racename = "10 Miles"
        self.assertTrue(race.add(racename, 1))
        # OK, remove race and organization
        race_id = race.race_id
        self.assertTrue(mg.race_delete(race_id))
        # Also remove Organization
        mg.organization_delete(org_id)


if __name__ == "__main__":
    unittest.main()
