import logging

from competition import neostore
# from lib import my_env

# Todo: Get Username / Password from environment settings
ns = neostore.NeoStore()


class Participant:
    def __init__(self, part_id=None, race_id=None, pers_id=None):
        """
        A Participant Object is the path: (person)-[:is]->(participant)-[:participates]->(race).
        If participant id is provided, then find race id and person id.
        If race id and person id are provided, then try to find participant id. If not successful, then create
        participant id.
        At the end of initialization, participant node, id, race id and person id are set.
        @param part_id: nid of the participant
        @param race_id: nid of the race
        @param pers_id: nid of the person
        @return: Participant object with participant node and nid, race nid and person nid are set.
        """
        self.part_node = None
        self.part_id = -1           # Unique ID (nid) of the Participant node
        if part_id:
            logging.debug("Set Participant with ID: {part_id}".format(part_id=part_id))
            self.part_node = ns.node(part_id)
            self.part_id = part_id
            self.race_id = ns.get_end_node(start_node_id=part_id, rel_type="participates")
            self.pers_id = ns.get_start_node(end_node_id=part_id, rel_type="is")
        elif pers_id and race_id:
            logging.debug(("Trying to get Participant in race for pers {p} and race {r}"
                           .format(p=pers_id, r=race_id)))
            self.race_id = race_id
            self.pers_id = pers_id
            self.part_node = ns.get_participant_in_race(pers_id=pers_id, race_id=race_id)
            if self.part_node:
                self.part_id = self.part_node["nid"]
            else:
                # Participant node not found, so create one.
                self.part_id = self.set_part_race()
        else:
            logging.fatal("No input provided.")
            raise ValueError("CannotCreateObject")
        return

    def get_id(self):
        """
        This method will return the Participant Node ID of this person's participation in the race
        @return: Participant Node ID (nid)
        """
        return self.part_id

    def set_part_race(self):
        """
        This method will link the person to the race. This is done by creating an Participant Node. This function will
        not link the participant to the previous or next participant.
        The method will set the participant node and the participant nid.
        @return: Node ID of the participant node.
        """
        self.part_node = ns.create_node("Participant")
        self.part_id = self.part_node["nid"]
        race_node = ns.node(self.race_id)
        ns.create_relation(from_node=self.part_node, rel="participates", to_node=race_node)
        pers_node = ns.node(self.pers_id)
        ns.create_relation(from_node=pers_node, rel="is", to_node=self.part_node)
        return self.part_id

    @staticmethod
    def set_relation(next_id=None, prev_id=None):
        """
        This method will connect the next runner with the previous runner. The next runner is after the previous runner.
        @param next_id: Node ID of the next runner
        @param prev_id: Node ID of the previous runner
        @return:
        """
        prev_part_node = ns.node(prev_id)
        next_part_node = ns.node(next_id)
        if neostore.validate_node(prev_part_node, "Participant") \
                and neostore.validate_node(next_part_node, "Participant"):
            ns.create_relation(from_node=next_part_node, rel="after", to_node=prev_part_node)

    def add(self, prev_pers_id=None):
        """
        This function will add the participant in the sequence of participants. The participant's predecessor is known.
        Possibilities:
        1. No predecessor. This is the first participant in this race. Check if there is a successor!
        2. No successor. This participant is  the last participant in the race.
        3. A predecessor that was linked to a successor already. This participant will break the existing link and
           enters between the predecessor and the successor.
        Check if there is a next participant for this participant, so if current runner enters an existing sequence.
        Create the person participant node only when the relations are known. Otherwise the new participant node can
        conflict with the sequence asked for.
        @param prev_pers_id: Node ID of the previous person, or None if the person is the first arrival.
        @return:
        """
        logging.debug("Add person {id} to previous person {prev_id} for race {race_id}"
                      .format(id=self.pers_id, prev_id=prev_pers_id, race_id=self.race_id))
        if prev_pers_id:
            logging.debug("Before create object for previous participant")
            prev_part = Participant(pers_id=prev_pers_id, race_id=self.race_id)
            prev_part_id = prev_part.get_id()
            logging.debug("Object for prev_part is created")
            if prev_part.next_runner():
                # The previous runner for this participant was not the last one so far in the race.
                # Get next runner to assign as next runner for participant.
                next_part_id = prev_part.next_runner()
                # Add link between part and next_part
                self.set_relation(prev_id=self.part_id, next_id=next_part_id)
                # Add link between prev_part and part
                self.set_relation(prev_id=prev_part_id, next_id=self.part_id)
                # Remove 'after' relation between prev_part and next_part
                ns.remove_relation(start_nid=next_part_id, end_nid=prev_part_id, rel_type="after")
            else:
                # Previous participant but no next participant
                # Add link between prev_part and this participant only. This participant is last finisher so far in race
                self.set_relation(prev_id=prev_part_id, next_id=self.part_id)
        else:
            # No previous participant. Find current first participant in race
            # If found: Add link between participant and next_participant.
            first_person_id = participant_first_id(self.race_id)
            if first_person_id:
                first_part = Participant(race_id=self.race_id, pers_id=first_person_id)
                first_part_id = first_part.get_id()
                # Create the participant node for this person
                self.set_relation(prev_id=self.part_id, next_id=first_part_id)
        return

    def prev_runner(self):
        """
        This method will get the node ID for this Participant's previous runner.
        The participant must have been created before.
        @return: ID of previous runner participant Node, False if there is no previous runner.
        """
        if not neostore.validate_node(self.part_node, "Participant"):       # pragma: no cover
            return False
        prev_part_id = ns.get_end_node(start_node_id=self.part_id, rel_type="after")
        return prev_part_id

    def next_runner(self):
        """
        This method will get the node ID for this Participant's next runner.
        The participant must have been created before.
        @return: ID of next runner participant Node, False if there is no next runner.
        """
        if not neostore.validate_node(self.part_node, "Participant"):       # pragma: no cover
            return False
        next_part_id = ns.get_start_node(end_node_id=self.part_id, rel_type="after")
        return next_part_id

    def remove(self):
        """
        This method will remove the participant from the race.
        @return:
        """
        if self.prev_runner() and self.next_runner():
            # There is a previous and next runner, link them
            ns.create_relation(from_node=ns.node(self.next_runner()), rel="after", to_node=ns.node(self.prev_runner()))
        # Remove Participant Node
        ns.remove_node_force(self.part_id)
        # Reset Object
        self.part_id = -1
        self.part_node = None
        return


class Person:
    def __init__(self, person_id=None):
        if person_id:
            self.person_id, self.name = self.set(person_id)
        else:
            self.name = 'NotYetDefined'
            self.person_id = person_id

    def find(self):
        """
        Find ID of the person with name 'name'. Return node ID, else return false.
        This function must be called from add(), so make it an internal function?
        @return: Node ID, or false if no node could be found.
        """
        props = {
            "name": self.name
        }
        person_node = ns.get_node("Person", **props)
        if person_node:
            self.person_id = person_node["nid"]
            return True
        else:
            logging.debug("No person found")
            return False

    def add(self, **properties):
        """
        Attempt to add the participant with name 'name'. The name must be unique. Person object is set to current
        participant. Name is set in this procedure, ID is set in the find procedure.
        @param properties: Properties (in dict) for the person
        @return: True, if registered. False otherwise.
        """
        self.name = properties['name']
        if self.find():
            # Person is found, Name and ID set, no need to register.
            return False
        else:
            # Person not found, register participant.
            ns.create_node("Person", **properties)
            # Now call find() again to set ID for the person
            self.find()
            return True

    def edit(self, **properties):
        """
        This method will update an existing person node. A check is done to guarantee that the name is not duplicated
        to an existing name on another node. Modified properties will be updated and removed properties will be deleted.
        @param properties: New set of properties for the node
        @return: True - in case node is rewritten successfully.
        """
        properties["nid"] = self.person_id
        ns.node_update(**properties)
        return True

    def set(self, person_id):
        """
        This method will set the person associated with this ID. The assumption is that the person_id relates to a
        existing and valid person.
        @param person_id:
        @return: Person object is set to the participant.
        """
        logging.debug("Person ID: {org_id}".format(org_id=person_id))
        person_node = ns.node(person_id)
        if person_node:
            self.name = person_node["name"]
            self.person_id = person_id
            return self.person_id, self.name
        else:
            raise ValueError("NodeNotFound")

    def get(self):
        return self.name

    def props(self):
        """
        This method will return the properties for the node in a dictionary format.
        @return:
        """
        return ns.node_props(nid=self.person_id)


class Organization:
    """
    This class instantiates to an organization.
    @return: Object
    """
    def __init__(self, org_id=None):
        self.name = 'NotYetDefined'
        self.org_id = -1
        self.org_node = None
        self.label = "NotYetDefined"
        self.org = None
        if org_id:
            self.set(org_id)

    def find(self, **org_dict):
        """
        This method searches for the organization based on organization name, location and datestamp. If found,
        then organization attributes will be set using method set_organization. If not found, 'False' will be returned.
        @param org_dict: New set of properties for the node. These properties are: name, location, datestamp and
         org_type
        @return: True if organization is found, False otherwise.
        """
        org_id = ns.get_organization(**org_dict)
        if org_id:
            self.org_id = org_id
            self.set(self.org_id)
            return True
        else:
            return False

    def add(self, **org_dict):
        """
        This method will check if the organization is registered already. If not, the organization graph object
        (exists of organization name with link to date and city where it is organized) will be created.
        The organization instance attributes will be set.
        @param org_dict: New set of properties for the node. These properties are: name, location, datestamp and
         org_type. Datestamp needs to be of the form 'YYYY-MM-DD'. org_type 1 for Wedstrijd, 2 for deelname.
        @return: True if the organization has been registered, False if it existed already.
        """
        logging.debug("Add Organization: {org_dict}".format(org_dict=org_dict))
        org_type = org_dict["org_type"]
        del org_dict["org_type"]
        self.org = org_dict
        if self.find(**org_dict):
            # No need to register (Organization exist already), and organization attributes are set.
            return False
        else:
            # Organization on Location and datestamp does not yet exist, register the node.
            self.org_node = ns.create_node("Organization", name=self.org["name"])
            # graph.create(self.org_node)  # Node will be created on first Relation creation.
            # Organization node known, now I can link it with the Location.
            self.set_location(self.org["location"])
            # Set Date  for Organization
            self.set_date(self.org["datestamp"])
            # Set Organization Type
            org_type_node = get_org_type_node(org_type)
            ns.create_relation(from_node=self.org_node, rel="type", to_node=org_type_node)
            # Set organization parameters by finding the created organization
            self.find(**org_dict)
            return True

    def edit(self, **properties):
        """
        This method will check if the organization is registered already. If not, the organization graph object
        (exists of organization name with link to date and city where it is organized) will be created.
        The organization instance attributes will be set.
        Edit function needs to redirect relations, so it has begin and end nodes. This function can then remove single
        date nodes and location nodes if required. The Organization delete function will force to remove an organization
        node without a need to find the date and location first. Therefore the delete function requires a more generic
        date and location removal, where a check on all orphans is done.
        @param properties: New set of properties for the node. These properties are: name, location, datestamp and
         org_type. Datestamp must be of the form 'YYYY-MM-DD'
        @return: True if the organization has been updated, False if the organization (name, location, date) existed
         already. A change in Organization Type only is also a successful (True) change.
        """
        logging.debug("In Organization.Edit with properties {properties}".format(properties=properties))
        # Check Organization Type
        curr_org_type = self.get_org_type()
        if not curr_org_type == properties["org_type"]:
            self.set_org_type(new_org_type=properties["org_type"], curr_org_type=curr_org_type)
        del properties["org_type"]
        # Check if name, date or location are changed
        changed_keys = [key for key in sorted(properties) if not (properties[key] == self.org[key])]
        if len(changed_keys) > 0:
            # Something is changed, so I need to end-up in unique combination of name, location, date
            if self.find(**properties):
                logging.error("Aangepaste Organisatie bestaat reeds: {props}".format(props=properties))
                return False
            else:
                if 'name' in changed_keys:
                    node_prop = dict(
                        name=properties["name"],
                        nid=self.org_id
                    )
                    ns.node_update(**node_prop)
                    logging.debug("Name needs to be updated from {on} to {nn}"
                                  .format(on=self.org["name"], nn=properties["name"]))
                if 'location' in changed_keys:
                    logging.debug("Location needs to be updated from {ol} to {nl}"
                                  .format(ol=self.org["location"], nl=properties["location"]))
                    # Remember current location - before fiddling around with relations!
                    curr_loc = Location(self.org["location"]).get_node()
                    curr_loc_id = ns.node_id(curr_loc)
                    # First create link to new location
                    self.set_location(properties["location"])
                    # Then remove link to current location
                    ns.remove_relation(start_nid=self.org_id, end_nid=curr_loc_id, rel_type="In")
                    # Finally check if current location is still required. Remove if there are no more links.
                    ns.remove_node(curr_loc_id)
                if 'datestamp' in changed_keys:
                    logging.debug("Date needs to be updated from {od} to {nd}"
                                  .format(od=type(self.org["datestamp"]), nd=type(properties["datestamp"])))
                    # Get Node for current day
                    curr_ds = self.org["datestamp"]
                    curr_date_node = ns.date_node(curr_ds)
                    # First create link to new date
                    self.set_date(properties["datestamp"])
                    # Then remove link from current date
                    ns.remove_relation(start_nid=self.org_id, end_nid=ns.node_id(curr_date_node), rel_type="On")
                    # Finally check if date (day, month, year) can be removed.
                    # Don't remove single date, clear all dates that can be removed. This avoids the handling of key
                    # because date nodes don't have a nid.
                    ns.clear_date()
                # New attributes configured, now set Organization again.
                self.set(self.org_id)
        return True

    def set(self, org_id):
        """
        This method will get the organization associated with this ID. The assumption is that the org_id relates to a
        existing and valid organization.
        It will set the organization labels.
        @param org_id:
        @return:
        """
        logging.debug("Org ID: {org_id}".format(org_id=org_id))
        this_org = ns.get_organization_from_id(org_id)
        self.label = "{org_name} ({city}, {day:02d}-{month:02d}-{year})".format(org_name=this_org["org"],
                                                                                city=this_org["city"],
                                                                                day=this_org["day"],
                                                                                month=this_org["month"],
                                                                                year=this_org["year"])
        self.org = dict(
            name=this_org["org"],
            location=this_org["city"],
            datestamp=this_org["date"]
        )
        self.name = this_org["org"]
        self.org_id = org_id
        self.org_node = ns.node(org_id)
        return True

    def get_label(self):
        """
        This method will return the label of the Organization. (Organization name, city and date). Assumption is that
        the organization has been set already.
        @return:
        """
        return self.label

    def get_location(self):
        """
        This method will return the location for the Organization.
        @return: Location name (city name), or False if no location found.
        """
        loc_id = ns.get_end_node(self.org_id, "In")
        loc_node = ns.node(loc_id)
        city = loc_node["city"]
        return city

    def get_date(self):
        """
        This method will return the date for the Organization.
        @return: Date, Format YYYY-MM-DD
        """
        date_id = ns.get_end_node(self.org_id, "On")
        date_node = ns.node(date_id)
        datestamp = date_node["key"]
        return datestamp

    def get_org_id(self):
        """
        This method will return the nid of the Organization node.
        :return: nid of the Organization node
        """
        return self.org_id

    def get_org_type(self):
        """
        This method will return the organization type as a Number. If not available, then Organization type is
        Wedstrijd (1). Not sure what the purpose of this method is.
        @return: Organization Type. 1: Wedstrijd (Default) - 2: Deelname
        """
        # Todo: Review usage of this method.
        org_type = {
            "Wedstrijd": 1,
            "Deelname": 2
            }
        org_type_name = 'Wedstrijd'
        org_type_id = ns.get_end_node(self.org_id, "type")
        if org_type_id:
            org_type_node = ns.node(org_type_id)
            org_type_name = org_type_node["name"]
        return org_type[org_type_name]

    def has_wedstrijd_type(self, racetype="NotFound"):
        """
        This method will check the number of races of type racetype. It can be used to check if there is a
        'Hoofdwedstrijd' assigned with the Organization.
        @param racetype: Race Type (Hoofdwedstrijd, Bijwedstrijd, Deelname)
        @return: Number of races for this type, False if there are no races.
        """
        res = ns.get_wedstrijd_type(self.org_id, racetype)
        if res:
            logging.debug("Organization has {res} races for type {racetype}".format(res=res, racetype=racetype))
            return res
        else:
            return False

    def ask_for_hoofdwedstrijd(self):
        """
        This method will check if adding a race needs an option to select a 'Hoofdwedstrijd'. This is required if
        Organization Type is 'Wedstrijd' (1) and no hoofdwedstrijd has been selected.
        @return: True - if Hoofdwedstrijd option for race is required, False otherwise.
        """
        if self.get_org_type() == 1 and not self.has_wedstrijd_type("Hoofdwedstrijd"):
            return True
        else:
            return False

    def set_location(self, loc=None):
        """
        This method will create a relation between the organization and the location. Relation type is 'In'.
        Organization Node must be available for this method.
        @param loc: Name of the city.
        @return:
        """
        loc_node = Location(loc).get_node()   # Get Location Node
        ns.create_relation(from_node=self.org_node, to_node=loc_node, rel="In")
        return

    def set_date(self, ds=None):
        """
        This method will create a relation between the organization and the date. Relation type is 'On'.
        Organization Node must be available for this method.
        @param ds: Datestamp
        @return:
        """
        date_node = ns.date_node(ds)   # Get Date (day) node
        ns.create_relation(from_node=self.org_node, rel="On", to_node=date_node)
        return

    def set_org_type(self, new_org_type, curr_org_type=None):
        """
        This method will set or update the Organization Type. In case of update Organization Type, then the current link
        needs to be removed, and links between Races need to be updated. In case new organization type is 'Deelname',
        then all races will be updated to 'Deelname'. In case new organization type is 'Wedstrijd', then all races will
        be updated to 'Bijwedstrijd' since it is not possible to guess the 'Hoofdwedstrijd'. The user needs to remember
        to update the 'Hoofdwedstrijd'. (Maybe send a pop-up message to the user?)
        @param new_org_type:
        @param curr_org_type:
        @return:
        """
        logging.debug("In set_org_type, change from current {cot} to new {newot}"
                      .format(cot=curr_org_type, newot=new_org_type))
        # First get node and node_id for Organization Type Wedstrijd and Organization Type Deelname
        prop_type = {
            "name": "Wedstrijd"
        }
        org_type_wedstrijd = ns.get_node("OrgType", **prop_type)
        org_type_wedstrijd_id = org_type_wedstrijd["nid"]
        prop_type["name"] = "Deelname"
        org_type_deelname = ns.get_node("OrgType", **prop_type)
        org_type_deelname_id = org_type_deelname["nid"]
        prop_type["name"] = "Bijwedstrijd"
        race_type_wedstrijd = ns.get_node("RaceType", **prop_type)
        prop_type["name"] = "Deelname"
        race_type_deelname = ns.get_node("RaceType", **prop_type)
        # Set new_org_type for Organization
        if new_org_type == 1:
            org_type_node = org_type_wedstrijd
            race_type_node = race_type_wedstrijd
        elif new_org_type == 2:
            org_type_node = org_type_deelname
            race_type_node = race_type_deelname
        else:
            logging.error("Unrecognized New Organization Type: {org_type}".format(org_type=new_org_type))
            return False
        ns.create_relation(from_node=self.org_node, to_node=org_type_node, rel="type")
        # Remove curr_org_type for Organization
        if curr_org_type:
            if curr_org_type == 1:
                org_type_node_id = org_type_wedstrijd_id
            elif curr_org_type == 2:
                org_type_node_id = org_type_deelname_id
            else:
                logging.error("Unrecognized Current Organization Type: {org_type}".format(org_type=curr_org_type))
                return False
            ns.remove_relation(start_nid=self.org_id, end_nid=org_type_node_id, rel_type="type")
        # Set new_org_type for all races in Organization
        # Get all races for this organization
        races = ns.get_end_nodes(self.org_id, "has")
        # Set all race types.
        for race_id in races:
            set_race_type(race_id, race_type_node)
        return


class Race:
    """
    This class instantiates to a race. This can be done as a new race that links to an organization, in which case
    org_id needs to be specified, or it can be done as a race node ID (in which case org_id should be none).
    """
    def __init__(self, org_id=None, race_id=None):
        """
        Define the Race object.
        @param org_id: Node ID of the Organization, used to create a new race.
        @param race_id: Node ID of the Race, to handle an existing race.
        @return:
        """
        self.name = 'NotYetDefined'
        self.label = 'NotYetDefined'
        self.org_id = 'NotYetDefined'
        self.race_id = 'NotYetDefined'
        if org_id:
            self.org_id = org_id
        elif race_id:
            logging.debug("Trying to set Race Object for ID {race_id}".format(race_id=race_id))
            self.node_set(nid=race_id)

    def find(self, racetype_id):
        """
        This method searches for the organization based on organization name, location and datestamp. If found,
        then organization attributes will be set using method set_organization and True will be returned.
        If not found, 'False' will be returned.
        @param racetype_id: Type of the Race
        @return: True if a race is found for this organization and racetype, False otherwise.
        """
        try:
            (race_nid, org_name) = ns.get_race_in_org(org_id=self.org_id, racetype_id=racetype_id, name=self.name)
        except TypeError:
            return False
        else:
            self.race_id = race_nid
            self.label = self.set_label()
            return True

    def add(self, name, racetype=None):
        """
        This method will check if the race is registered for this organization. If not, the race graph object
        (exists of race name with link to race type and the organization) will be created.
        @param name: Name of the race
        @param racetype: 1 then Hoofdwedstrijd. If False: then calculate (bijwedstrijd or Deelname).
        @return: True if the race has been registered, False if it existed already.
        """
        # Todo - add tests on race type: deelname must be for each race of organization, hoofdwedstrijd only one.
        logging.debug("Name: {name}".format(name=name))
        self.name = name
        org_type = get_org_type(self.org_id)
        if racetype:
            # RaceType defined, so it must be Hoofdwedstrijd.
            racetype = "Hoofdwedstrijd"
        elif org_type == "Wedstrijd":
            racetype = "Bijwedstrijd"
        else:
            racetype = "Deelname"
        racetype_node = get_race_type_node(racetype)
        racetype_id = racetype_node["nid"]
        if self.find(racetype_id):
            # No need to register (Race exist already).
            return False
        else:
            # Race for Organization does not yet exist, register it.
            props = {
                "name": name
            }
            race_node = ns.create_node("Race", **props)
            self.race_id = race_node["nid"]
            org_node = ns.node(self.org_id)
            ns.create_relation(from_node=org_node, rel="has", to_node=race_node)
            set_race_type(race_id=ns.node_id(race_node), race_type_node=racetype_node)
            # Set organization parameters by finding the created organization
            self.find(racetype_id)
            return True

    def edit(self, name):
        """
        This method will update the name of the race. It is not possible to modify the race type in this step.
        @param name: Name of the race
        @return: True if the race has been updated, False otherwise.
        """
        # Todo - add tests on race type: deelname must be for each race of organization, hoofdwedstrijd only one.
        logging.debug("Edit race to new name: {name}".format(name=name))
        self.name = name
        props = dict(name=self.name, nid=self.race_id)
        ns.node_update(**props)
        return True

    def node_set(self, nid=None):
        """
        Given the node_id, this method will configure the race object.
        @param nid: Node ID of the race node.
        @return: Fully configured race object.
        """
        logging.debug("In node_set to create race node for id {node_id}".format(node_id=nid))
        self.race_id = nid
        race_node = ns.node(self.race_id)
        logging.debug("Race node set")
        self.name = race_node['name']
        logging.debug("Name: {name}".format(name=self.name))
        self.org_id = self.get_org_id()
        self.label = self.set_label()
        return

    def get_org_id(self):
        """
        This method set and return the org_id for a race node_id. A valid race_id must be set.
        @return: org_id
        """
        org_node_nid = ns.get_start_node(end_node_id=self.race_id, rel_type="has")
        logging.debug("ID of the Org for Race ID {race_id} is {org_id}"
                      .format(org_id=org_node_nid, race_id=self.race_id))
        return org_node_nid

    def get_name(self):
        """
        This method get the name of the race.
        @return: org_id
        """
        return self.name

    def set_label(self):
        """
        This method will set the label for the race. Assumptions are that the race name and the organization ID are set
        already.
        @return:
        """
        logging.debug("Trying to get Organization label for org ID {org_id}".format(org_id=self.org_id))
        org_node = ns.node(self.org_id)
        org_name = org_node["name"]
        self.label = "{race_name} ({org_name})".format(race_name=self.name, org_name=org_name)
        return self.label


class Location:
    def __init__(self, loc):
        self.loc = loc

    def find(self):
        """
        Find the location node
        @return:
        """
        props = {
            "city": self.loc
        }
        loc = ns.get_node("Location", **props)
        return loc

    def add(self):
        if not self.find():
            ns.create_node("Location", city=self.loc)
            return True
        else:
            return False

    def get_node(self):
        """
        This method will get the node that is associated with the location. If the node does not exist already, it will
        be created.
        @return:
        """
        self.add()    # Register if required, ignore else
        node = self.find()
        return node


def organization_list():
    """
    This function will return a list of organizations. Each item in the list is a dictionary with fields date,
    organization, city, id (for organization nid) and type.
    @return:
    """
    return ns.get_organization_list()


def organization_delete(org_id=None):
    """
    This method will delete an organization. This can be done only if there are no more races attached to the
    organization. If an organization is removed, then check is done for orphan date and orphan location. If available,
    these will also be removed.
    @param org_id:
    @return:
    """
    if ns.get_end_nodes(start_node_id=org_id, rel_type="has"):
        logging.info("Organization with id {org_id} cannot be removed, races are attached.".format(org_id=org_id))
        return False
    else:
        # Remove Organization
        ns.remove_node_force(org_id)
        # Check if this results in orphan dates, remove these dates
        ns.clear_date()
        # Check if this results in orphan locations, remove these locations.
        ns.clear_locations()
        logging.info("Organization with id {org_id} removed.".format(org_id=org_id))
        return True


def get_org_id(race_id):
    """
    This method will return the organization ID for a Race ID: Organization has Race.
    @param race_id: Node ID of the race.
    @return: Node ID of the organization.
    """
    org_id = ns.get_start_node(end_node_id=race_id, rel_type="has")
    return org_id


def get_org_type(org_id):
    """
    This method will get the organization Type for this organization. Type can be 'Wedstrijd' or 'Deelname'.
    @param org_id: Node ID of the Organization.
    @return: Type of the Organization: Wedstrijd or Deelname, or False in case type could not be found.
    """
    org_type_id = ns.get_end_node(start_node_id=org_id, rel_type="type")
    org_type_node = ns.node(org_type_id)
    if org_type_node:
        return org_type_node["name"]
    else:
        return False


def get_org_type_node(org_type_id):
    """
    This method will find the Organization Type Node.
    @param org_type_id: RadioButton selected for Organization Type.
    @return: Organization Type Node. "Wedstrijd" if org_type_id is 1, "Deelname" in every other case.
    """
    if org_type_id == 1:
        name = "Wedstrijd"
    else:
        name = "Deelname"
    props = {
        "name": name
    }
    return ns.get_node("OrgType", **props)


def get_race_type_node(racetype):
    """
    This method will return the racetype node associated with this racetype.
    @param racetype: Racetype specifier (Hoofdwedstrijd, Bijwedstrijd, Deelname)
    @return: Racetype Node, or False if it could not be found.
    """
    if racetype in ["Hoofdwedstrijd", "Bijwedstrijd", "Deelname"]:
        # RaceType defined, so it must be Hoofdwedstrijd.
        props = {
            "name": racetype
        }
        racetype_node = ns.get_node("RaceType", **props)
        return racetype_node
    else:
        logging.error("RaceType unknown: {racetype}.".format(racetype=racetype))
        return False


def get_races_for_org(org_id):
    """
    This method will return the list of races for an Organization ID: Organization has Race.
    @param org_id: Node ID of the Organization.
    @return: List of node IDs of races.
    """
    races = ns.get_end_nodes(start_node_id=org_id, rel_type="has")
    return races


def race_list(org_id):
    """
    This function will return a list of races for an organization ID
    :param org_id: nid of the organization
    :return: List of races.
    """
    return ns.get_race_list(org_id)


def race_label(race_id):
    """
    This function will return the label for the Race nid
    @param race_id:
    @return:
    """
    record = ns.get_race_label(race_id)
    label = "{day:02d}-{month:02d}-{year} - {city}, {race}".format(race=record["race"], city=record["city"],
                                                                   day=record["day"], month=record["month"],
                                                                   year=record["year"])
    return label


def races4person(pers_id):
    """
    This method will get the list of races for the person.

    @param pers_id: Node ID for the person

    @return: list with dictionary per race. The dictionary has fields race_label and race_id.
    """
    recordlist = ns.get_race4person(pers_id)
    races = [{'race_id': record["race_id"], 'race_label': race_label(record["race_id"])} for record in recordlist]
    return races


def race_delete(race_id=None):
    """
    This method will delete a race. This can be done only if there are no more participants attached to the
    race.
    @param race_id: Node ID of the race to be removed.
    @return: True if race is removed, False otherwise.
    """
    if ns.get_start_nodes(end_node_id=race_id, rel_type="participates"):
        logging.info("Race with id {race_id} cannot be removed, participants are attached.".format(race_id=race_id))
        return False
    else:
        # Remove Organization
        ns.remove_node_force(race_id)
        logging.info("Race with id {race_id} removed.".format(race_id=race_id))
        return True


def person_list():
    """
    Return the list of persons as person objects.
    @return: List of persons objects. Each person is represented in a list with nid and name of the person.
    """
    res = ns.get_nodes('Person')
    person_arr = []
    for node in res:
        attribs = [node["nid"], node["name"]]
        person_arr.append(attribs)
    return person_arr


def person4participant(part_id):
    """
    This method will get the person name from a participant ID. First it will convert the participant ID to a
    participant node. Then it gets the (reverse) relation ('is') from participant to person.
    Finally it will return the id and the name of the person in a hash.
    @param part_id: Node ID of the participant.
    @return: Person dictionary with name and nid, or False if no person found for participant id nid.
    """
    person_nid = ns.get_start_node(end_node_id=part_id, rel_type="is")
    if person_nid:
        person_node = ns.node(person_nid)
        person_name = person_node["name"]
        return dict(name=person_name, nid=person_nid)
    else:
        logging.error("Cannot find person for participant node nid: {part_id}".format(part_id=part_id))
        return False


def participant_list(race_id):
    """
    Returns the list of participants in hash of id, name.
    @param race_id: ID of the race for which current participants are returned
    @return: List of Person Objects. Each person object is represented as a list with id, name of the participant.
    """
    res = ns.get_start_nodes(end_node_id=race_id, rel_type="participates")
    part_arr = []
    for part_nid in res:
        person_nid = ns.get_start_node(end_node_id=part_nid, rel_type="is")
        person_node = ns.node(person_nid)
        attribs = [person_node["nid"], person_node["name"]]
        part_arr.append(attribs)
    return part_arr


def participant_seq_list(race_id):
    """
    This method will collect the people in a race in sequence of arrival.
    @param race_id: nid of the race for which the participants are returned in sequence of arrival.
    @return: List of names of the participant items in the race. Each item is a list of person nid and the person name.
    False if no participants in the list.
    """
    node_list = ns.get_participant_seq_list(race_id)
    if node_list:
        finisher_list = []
        # If there are finishers, then recordlist has one element, which is a nodelist
        for part in node_list:
            # Get person node for this participant
            pers_nid = ns.get_start_node(end_node_id=part["nid"], rel_type="is")
            pers_node = ns.node(pers_nid)
            pers_name = pers_node["name"]
            logging.debug("pers_name: {pers_name}, pers_id: {pers_id}".format(pers_name=pers_name, pers_id=pers_nid))
            pers_obj = [pers_nid, pers_name]
            finisher_list.append(pers_obj)
        return finisher_list
    else:
        return False


def participant_after_list(race_id):
    """
    This method will return the participant sequence list as a SelectField list. It will call participant_seq_list
    and 'prepend' a value for 'eerste aankomer' (value -1).
    @param race_id: Node ID of the race
    @return: List of the Person objects (list of Person nid and Person name) in sequence of arrival and value for
    'eerste aankomer'.
    """
    eerste = [-1, 'Eerste aankomst']
    finisher_list = participant_seq_list(race_id)
    finisher_list.insert(0, eerste)
    return finisher_list


def participant_last_id(race_id):
    """
    This method will return the nid of the last participant in the race. It calls check participant_after_list and
    fetches the last ID of the runner. This way no special treatment is required in case there are no participants. The
    ID of the last runner will redirect to -1 then.
    @param race_id: Node nid of the race.
    @return: nid of the Person Node of the last finisher so far in the race, -1 if no finishers registered yet.
    """
    finisher_list = participant_after_list(race_id)
    part_arr = finisher_list.pop()
    part_last = part_arr[0]
    logging.debug("ID of last finisher: {part_last}".format(part_last=part_last))
    return part_last


def participant_first_id(race_id):
    """
    This method will get the ID of the first person in the race.
    @param race_id: Node ID of the race.
    @return: Node ID of the first person so far in the race, -1 if no finishers registered yet.
    """
    finisher_list = participant_seq_list(race_id)
    if finisher_list:
        person_id = finisher_list[0][0]
        logging.debug("This is person_id {person_id} from finisher_list {fl} - race_id {race_id}"
                      .format(person_id=person_id, fl=finisher_list, race_id=race_id))
        return person_id
    else:
        return False


def next_participant(race_id):
    """
    This method will get the list of potential next participants. This is the list of all persons minus the people that
    have been selected already in this race. Also all people that have been selected in other races for this
    organization will no longer be available for selection.
    @param race_id:
    @return: List of the Person objects (Person nid and Person name) that can be selected as participant in the race.
    """
    # Todo: extend to participants that have been selected for this organization (one participation per race per org.)
    # Get Organization for this race
    # org_id = get_org_id(race_id)
    org_id = get_org_id(race_id)
    races = get_races_for_org(org_id)
    participants = []
    for race_id in races:
        parts_race = participant_list(race_id)
        participants += parts_race
    persons = person_list()
    next_participants = [part for part in persons if part not in participants]
    return next_participants


def racetype_list():
    """
    This method will get all the race types. It will return them as a list of tuples with race type ID and race type
    name.
    @return:
    """
    race_nodes = ns.get_nodes("RaceType")
    race_types = []
    for node in race_nodes:
        race_tuple = (node["nid"], node["name"])
        race_types.append(race_tuple)
    return race_types


def relations(node_id):
    """
    This method will return True if the node with node_id has relations, False otherwise.
    @param node_id:
    @return:
    """
    return ns.relations(node_id)


def remove_node(node_id):
    """
    This function will remove the node with node ID node_id
    @param node_id:
    @return:
    """
    return ns.remove_node(node_id)


def set_race_type(race_id=None, race_type_node=None):
    """
    Check if old node type is defined. If so, remove the link.
    Then add new link.
    @param race_id: Node ID for the race
    @param race_type_node:
    @return:
    """
    race_node = ns.node(race_id)
    # Check if there is a link now.
    curr_race_type_id = ns.get_end_node(race_id, "type")
    if curr_race_type_id:
        ns.remove_relation(race_id, curr_race_type_id, "type")
    ns.create_relation(from_node=race_node, to_node=race_type_node, rel="type")
    return
