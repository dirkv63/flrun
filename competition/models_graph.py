import logging
import sys
import competition.p2n_wrapper as pu
from lib import my_env
from py2neo import Graph, Node, Relationship
from py2neo.ext.calendar import GregorianCalendar

graph = Graph()
calendar = GregorianCalendar(graph)
# watch("py2neo.cypher")
# Set Node IDs, to improve performance.


class Participant:
    def __init__(self, part_id=None, race_id=None, pers_id=None):
        self.part = None
        self.part_id = -1
        self.prev_runner_id = -1
        self.next_runner_id = -1
        if part_id:
            logging.debug("Set Participant with ID: {part_id}".format(part_id=part_id))
            self.part, self.part_id = self.set(part_id)
        elif pers_id and race_id:
            logging.debug("Set Participant from person with ID: {pers_id}".format(pers_id=pers_id))
            self.part, self.part_id = self.get_part_race(race_id=race_id, pers_id=pers_id)

    @staticmethod
    def set(part_id):
        """
        This method will set the Participant Object
        :param part_id: Node ID of the participant
        :return:
        """
        return graph.node(part_id), part_id

    def get_id(self):
        """
        This method will return the Participant Node ID of this person's participation in the race
        :return: Participant Node ID
        """
        return self.part_id

    def get_part_race(self, race_id=None, pers_id=None):
        """
        This method will get the participant from Person ID and Race ID. If the participant exists already, it will
        be returned. If the participant did not exist already, it will return False.
        Use the method set_part_race to set a participant in the race.
        :param race_id: Node ID of the Race
        :param pers_id: Node ID of the Person
        :return: Participant Object, created or existing.
        """
        query = """
            MATCH (pers:Person)-[:is]->(part:Participant)-[:participates]->(race:Race)
            WHERE id(pers)={pers_id} AND id(race)={race_id}
            RETURN part, id(part) as id
        """.format(pers_id=pers_id, race_id=race_id)
        res = graph.cypher.execute(query)
        logging.debug("Res: {res}".format(res=res))
        if len(res) > 0:
            self.part, self.part_id = res[0]
            return self.part, self.part_id
        else:
            return False

    def set_part_race(self, race_id=Node, pers_id=None):
        """
        This method will set the participant for the race. This can be done only when it is known the condition for the
        previous and next runner. Otherwise the function 'find_first_participant' will fail.
        :param race_id: Node ID of the race.
        :param pers_id: Node ID of the person.
        :return: Node ID of the participant.
        """
        self.part, = graph.create(Node("Participant"))  # Create returns tuple
        self.part_id = pu.node_id(self.part)
        race = graph.node(race_id)
        graph.create(Relationship(self.part, "participates", race))
        runner = graph.node(pers_id)
        graph.create(Relationship(runner, "is", self.part))
        return self.part_id

    def add(self, pers_id=None, prev_pers_id=-1, race_id=None):
        """
        Check if there is a next participant for this participant, so if current runner enters an existing sequence.
        Create the person participant node only when the relations are known. Otherwise the new participant node can
        conflict with the sequence asked for.
        :param pers_id: Node ID of the person to add to the participant sequence.
        :param prev_pers_id: Node ID of the previous person, or -1 if the person is the first arrival.
        :param race_id: Node ID of the race to which the person needs to be added.
        :return:
        """
        logging.debug("Add person {id} to previous person {prev_id} for race {race_id}"
                      .format(id=pers_id, prev_id=prev_pers_id, race_id=race_id))
        if prev_pers_id > 0:
            logging.debug("Before create object for prev_part")
            prev_part = Participant(pers_id=prev_pers_id, race_id=race_id)
            prev_part_id = prev_part.get_id()
            logging.debug("Object for prev_part is created")
            if prev_part.next_runner():
                # The previous runner for this participant was not the last one so far in the race.
                # Get next runner to assign as next runner for participant.
                next_part_id = prev_part.next_runner()
                # Create the participant node for this person
                self.set_part_race(race_id=race_id, pers_id=pers_id)
                # Add link between part and next_part
                self.set_relation(prev_id=self.part_id, next_id=next_part_id)
                # Add link between prev_part and part
                self.set_relation(prev_id=prev_part_id, next_id=self.part_id)
                # Remove 'after' relation between prev_part and next_part
                pu.remove_relation(next_part_id, prev_part_id, "after")
            else:
                # Previous participant but no next participant
                # Create the participant node for this person
                self.set_part_race(race_id=race_id, pers_id=pers_id)
                # Add link between prev_part and this participant only. This participant is last finisher so far in race
                self.set_relation(prev_id=prev_part_id, next_id=self.part_id)
        else:
            # No previous participant. Find current first participant in race
            # If found: Add link between participant and next_participant.
            first_person_id = participant_first_id(race_id)
            if first_person_id > -1:
                first_part = Participant(race_id=race_id, pers_id=first_person_id)
                first_part_id = first_part.get_id()
                # Create the participant node for this person
                self.set_part_race(race_id=race_id, pers_id=pers_id)
                self.set_relation(prev_id=self.part_id, next_id=first_part_id)
            else:
                # Create the participant node for this person
                self.set_part_race(race_id=race_id, pers_id=pers_id)
        return

    @staticmethod
    def validate_node(node):
        """
        This method will validate if the provided node is a participant node. A valid participant node is type Node and
        has label 'participant'.
        :param node: Node to validate
        :return: True if this looks to be a valid participant node, false otherwise.
        """
        # Todo: validate that the participant node is connected to a person and to a race.
        if type(node) is Node:
            if 'Participant' in node.labels:
                return True
            else:
                nid = pu.node_id(node)
                logging.error("Got node ID {nid}, but this is not of type participant".format(nid=nid))
        else:
            logging.error("Expected object type Node, got {obj_type}".format(obj_type=type(node)))
        return False

    def set_relation(self, next_id=None, prev_id=None):
        """
        This method will connect the next runner with the previous runner. The next runner is after the previous runner.
        :param next_id: Node ID of the next runner
        :param prev_id: Node ID of the previous runner
        :return: True if the relation is created, false otherwise.
        """
        prev_runner = graph.node(prev_id)
        next_runner = graph.node(next_id)
        if self.validate_node(prev_runner) and self.validate_node(next_runner):
            rel = Relationship(next_runner, "after", prev_runner)
            graph.create(rel)

    def prev_runner(self):
        """
        This method will get the node ID for this Participant's previous runner. If node ID = -1, then the value has
        not yet been initialized. If value = -2, then there is no previous runner.
        The participant must have been created before.
        :return: ID of previous runner participant Node, False if there is no previous runner.
        """
        if not self.validate_node(self.part):
            return False
        try:
            rel = next(graph.match(start_node=self.part, rel_type="after"))
        except StopIteration:
            # There is no previous runner
            self.prev_runner_id = -2
            return False
        else:
            self.prev_runner_id = pu.node_id(rel.end_node)
            return self.prev_runner_id

    def next_runner(self):
        """
        This method will get the node ID for this Participant's next runner. If node ID = -1, then the value has
        not yet been initialized. If value = -2, then there is no next runner.
        The participant must have been created before.
        :return: ID of next runner participant Node, False if there is no previous runner.
        """
        if not self.validate_node(self.part):
            return False
        try:
            rel = next(graph.match(end_node=self.part, rel_type="after"))
        except StopIteration:
            # There is no next runner
            self.next_runner_id = -2
            return False
        else:
            self.next_runner_id = pu.node_id(rel.start_node)
            return self.next_runner_id

    def remove(self):
        """
        This method will remove the participant from the race.
        :return:
        """
        if self.prev_runner() and self.next_runner():
            # There is a previous and next runner, link them
            rel = Relationship(graph.node(self.next_runner_id), "after", graph.node(self.prev_runner_id))
            graph.create(rel)
        # Remove Participant Node
        pu.remove_node_force(self.part_id)
        # Reset Object
        self.part_id = -1
        self.part = None
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
        :return: Node ID, or false if no node could be found.
        """
        query = "match (p:Person {name: {name}}) return id(p) as id"
        pers_id_arr = graph.cypher.execute(query, name=self.name)
        if len(pers_id_arr):
            self.person_id = pers_id_arr[0].id
            return True
        else:
            logging.debug("No person found")
            return False

    def add(self, **properties):
        """
        Attempt to add the participant with name 'name'. The name must be unique. Person object is set to current
        participant. Name is set in this procedure, ID is set in the find procedure.
        :param properties: Properties (in dict) for the person
        :return: True, if registered. False otherwise.
        """
        self.name = properties['name']
        if self.find():
            # Person is found, Name and ID set, no need to register.
            return False
        else:
            # Person not found, register participant.
            person = Node("Person", **properties)
            graph.create(person)
            # Now call find() again to set ID for the person
            self.find()
            return True

    def edit(self, **properties):
        """
        This method will update an existing person node. A check is done to guarantee that the name is not duplicated
        to an existing name on another node. Modified properties will be updated and removed properties will be deleted.
        :param properties: New set of properties for the node
        :return: True - in case node is rewritten successfully.
        """
        pu.node_update(self.person_id, **properties)
        return True

    def set(self, person_id):
        """
        This method will set the person associated with this ID. The assumption is that the person_id relates to a
        existing and valid person.
        :param person_id:
        :return: Person object is set to the participant.
        """
        logging.debug("Person ID: {org_id}".format(org_id=person_id))
        query = """
        MATCH (p:Person)
        WHERE id(p) = {person_id}
        RETURN p.name as name
        """.format(person_id=person_id)
        person_array = graph.cypher.execute(query)
        this_person = person_array[0]
        # Todo - expecting one and exactly one row back. Handle errors?
        self.name = this_person.name
        self.person_id = person_id
        return self.person_id, self.name

    def get(self):
        return self.name

    def props(self):
        """
        This method will return the properties for the node in a dictionary format.
        :return:
        """
        return pu.node_props(nid=self.person_id)


class Organization:
    """
    This class instantiates to an organization.
    :return: Object
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
        :param org_dict: New set of properties for the node. These properties are: name, location, datestamp and
         org_type
        :return: True if organization is found, False otherwise.
        """
        query = """
        MATCH (day:Day {key: {datestamp}})<-[:On]-(org:Organization {name: {name}}),
              (org)-[:In]->(loc:Location {city: {location}})
        RETURN id(org) as org_id
        """
        org_id_arr = graph.cypher.execute(query, name=org_dict["name"], location=org_dict["location"],
                                          datestamp=org_dict["datestamp"])
        if len(org_id_arr) == 0:
            # No organization found on this date for this location
            return False
        elif len(org_id_arr) == 1:
            # Organization ID found, remember organization attributes
            self.org_id = org_id_arr[0].org_id
            self.set(self.org_id)
            return self.org_id
        else:
            tot_len = len(org_id_arr)
            logging.error("Expected to find 0 or 1 organization, found {tot_len} (Organization: {name}, "
                          "Location: {loc}, Date: {date}"
                          .format(tot_len=tot_len, name=org_dict["name"], loc=org_dict["location"],
                                  date=org_dict["datestamp"]))
            return False

    def add(self, **org_dict):
        """
        This method will check if the organization is registered already. If not, the organization graph object
        (exists of organization name with link to date and city where it is organized) will be created.
        The organization instance attributes will be set.
        :param org_dict: New set of properties for the node. These properties are: name, location, datestamp and
         org_type
        :return: True if the organization has been registered, False if it existed already.
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
            self.org_node = Node("Organization", name=self.org["name"])
            # graph.create(self.org_node)  # Node will be created on first Relation creation.
            # Organization node known, now I can link it with the Location.
            self.set_location(self.org["location"])
            # Set Date  for Organization
            self.set_date(self.org["datestamp"])
            # Set Organization Type
            org_type_node = get_org_type_node(org_type)
            graph.create(Relationship(self.org_node, "type", org_type_node))
            # Set organization parameters by finding the created organization
            # self.find(name, location, datestamp)
            return True

    def edit(self, **properties):
        """
        This method will check if the organization is registered already. If not, the organization graph object
        (exists of organization name with link to date and city where it is organized) will be created.
        The organization instance attributes will be set.
        Edit function needs to redirect relations, so it has begin and end nodes. This function can then remove single
        date nodes and location nodes if required. The Organization delete function will force to remove an organization
        node without a need to find the date and location first. Therefore the delete function requires a more generic
        date and location removal, where check on all orphans is done.
        :param properties: New set of properties for the node. These properties are: name, location, datestamp and
         org_type
        :return: True if the organization has been updated, False if it existed already.
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
                        name=properties["name"]
                    )
                    pu.node_update(self.org_id, **node_prop)
                    logging.debug("Name needs to be updated from {on} to {nn}"
                                  .format(on=self.org["name"], nn=properties["name"]))
                if 'location' in changed_keys:
                    logging.debug("Location needs to be updated from {ol} to {nl}"
                                  .format(ol=self.org["location"], nl=properties["location"]))
                    # Remember current location - before fiddling around with relations!
                    curr_loc = Location(self.org["location"]).get_node()
                    curr_loc_id = pu.node_id(curr_loc)
                    # First create link to new location
                    self.set_location(properties["location"])
                    # Then remove link to current location
                    pu.remove_relation(self.org_id, curr_loc_id, "In")
                    # Finally check if current location is still required. Remove if there are no more links.
                    pu.remove_node(curr_loc_id)
                if 'datestamp' in changed_keys:
                    logging.debug("Date needs to be updated from {od} to {nd}"
                                  .format(od=type(self.org["datestamp"]), nd=type(properties["datestamp"])))
                    # Get Node for current day
                    curr_ds = self.org["datestamp"]
                    curr_date_node = calendar.date(curr_ds.year, curr_ds.month, curr_ds.day).day
                    # First create link to new date
                    self.set_date(properties["datestamp"])
                    # Then remove link from current date
                    pu.remove_relation(self.org_id, pu.node_id(curr_date_node), "On")
                    # Finally check if date (day, month, year) can be removed.
                    pu.remove_date(curr_ds)
        return True

    def set(self, org_id):
        """
        This method will get the organization associated with this ID. The assumption is that the org_id relates to a
        existing and valid organization.
        It will set the organization labels.
        :param org_id:
        :return:
        """
        logging.debug("Org ID: {org_id}".format(org_id=org_id))
        query = """
            MATCH (date:Day)<-[:On]-(org:Organization)-[:In]->(loc:Location)
            WHERE id(org) = {org_id}
            RETURN date.day as day, date.month as month, date.year as year, date.key as date,
                   org.name as org, loc.city as city, org as org_node
        """.format(org_id=org_id)
        org_array = graph.cypher.execute(query)
        this_org = org_array[0]
        # Todo - expecting one and exactly one row back. Handle errors?
        self.label = "{org_name} ({city}, {day:02d}-{month:02d}-{year})".format(org_name=this_org.org,
                                                                                city=this_org.city,
                                                                                day=this_org.day,
                                                                                month=this_org.month,
                                                                                year=this_org.year)
        self.org = dict(
            name=this_org.org,
            location=this_org.city,
            datestamp=my_env.datestr2date(this_org.date)
        )
        self.name = this_org.org
        self.org_id = org_id
        self.org_node = this_org.org_node
        return True

    def get_label(self):
        """
        This method will return the label of the Organization. (Organization name, city and date). Assumption is that
        the organization has been set already.
        :return:
        """
        return self.label

    def get_location(self):
        """
        This method will return the location for the Organization.
        :return: Location name (city name), or False if no location found.
        """
        loc_id = pu.get_end_node(self.org_id, "In")
        loc_node = pu.node(loc_id)
        city = loc_node["city"]
        return city

    def get_date(self):
        """
        This method will return the date for the Organization.
        :return: Date, Format YYYY-MM-DD
        """
        date_id = pu.get_end_node(self.org_id, "On")
        date_node = pu.node(date_id)
        datestamp = date_node["key"]
        return datestamp

    def get_org_type(self):
        """
        This method will return the organization type as a Number. If not available, then Organization type is
        Wedstrijd (1).
        :return: Organization Type. 1: Wedstrijd - 2: Deelname
        """
        org_type = {
            "Wedstrijd": 1,
            "Deelname": 2
            }
        org_type_name = 'Wedstrijd'
        org_type_id = pu.get_end_node(self.org_id, "type")
        if org_type_id:
            org_type_node = pu.node(org_type_id)
            org_type_name = org_type_node["name"]
        return org_type[org_type_name]

    def has_wedstrijd_type(self, racetype="NotFound"):
        """
        This method will check the number of races of type racetype. It can be used to check if there is a
        'Hoofdwedstrijd' assigned with the Organization.
        :param racetype: Race Type (Hoofdwedstrijd, Bijwedstrijd, Deelname)
        :return: Number of races for this type, False if there are no races.
        """
        qm = "MATCH (org:Organization)-[:has]->(race:Race)-[:type]->(rt:RaceType {name: {racetype}})"
        qw = "WHERE id(org)={org_id} ".format(org_id=self.org_id)
        qr = "RETURN org, race, rt"
        query = "{qm} {qw} {qr}".format(qm=qm, qw=qw, qr=qr)
        logging.debug("Look, my query: {query}".format(query=query))
        res = graph.cypher.execute(query, racetype=racetype)
        if len(res):
            logging.debug("Organization has {len} races for type {racetype}".format(len=len(res), racetype=racetype))
            return len(res)
        else:
            return False

    def ask_for_hoofdwedstrijd(self):
        """
        This method will check if adding a race needs an option to select a 'Hoofdwedstrijd'. This is required if
        Organization Type is 'Wedstrijd' (1) and no hoofdwedstrijd has been selected.
        :return: True - if Hoofdwedstrijd option for race is required, False otherwise.
        """
        if self.get_org_type() == 1 and not self.has_wedstrijd_type("Hoofdwedstrijd"):
            return True
        else:
            return False

    def set_location(self, loc=None):
        """
        This method will create a relation between the organization and the location. Relation type is 'In'.
        Organization Node must be available for this method.
        :param loc: Name of the city.
        :return:
        """
        loc_node = Location(loc).get_node()   # Get Location Node
        pu.create_relation(start_node=self.org_node, end_node=loc_node, rel_type="In")
        return

    def set_date(self, ds=None):
        """
        This method will create a relation between the organization and the date. Relation type is 'On'.
        Organization Node must be available for this method.
        :param ds: Datestamp
        :return:
        """
        date_node = calendar.date(ds.year, ds.month, ds.day).day   # Get Date (day) node
        graph.create(Relationship(self.org_node, "On", date_node))
        return

    def set_org_type(self, new_org_type, curr_org_type=None):
        """
        This method will set or update the Organization Type. In case of update Organization Type, then the current link
        needs to be removed, and links between Races need to be updated. In case new organization type is 'Deelname',
        then all races will be updated to 'Deelname'. In case new organization type is 'Wedstrijd', then all races will
        be updated to 'Bijwedstrijd' since it is not possible to guess the 'Hoofdwedstrijd'. The user needs to remember
        to update the 'Hoofdwedstrijd'. (Maybe send a pop-up message to the user?)
        :param new_org_type:
        :param curr_org_type:
        :return:
        """
        logging.debug("In set_org_type, change from current {cot} to new {newot}"
                      .format(cot=curr_org_type, newot=new_org_type))
        # First get node and node_id for Organization Type Wedstrijd and Organization Type Deelname
        org_type_wedstrijd = graph.merge_one("OrgType", "name", "Wedstrijd")
        org_type_wedstrijd_id = pu.node_id(org_type_wedstrijd)
        org_type_deelname = graph.merge_one("OrgType", "name", "Deelname")
        org_type_deelname_id = pu.node_id(org_type_deelname)
        race_type_wedstrijd = graph.merge_one("RaceType", "name", "Bijwedstrijd")
        # race_type_wedstrijd_id = pu.node_id(race_type_wedstrijd)
        race_type_deelname = graph.merge_one("RaceType", "name", "Deelname")
        # race_type_deelname_id = pu.node_id(race_type_deelname)
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
        pu.create_relation(start_node=self.org_node, end_node=org_type_node, rel_type="type")
        # Remove curr_org_type for Organization
        if curr_org_type:
            if curr_org_type == 1:
                org_type_node_id = org_type_wedstrijd_id
            elif curr_org_type == 2:
                org_type_node_id = org_type_deelname_id
            else:
                logging.error("Unrecognized Current Organization Type: {org_type}".format(org_type=curr_org_type))
                return False
            pu.remove_relation(start_nid=self.org_id, end_nid=org_type_node_id, rel_type="type")
        # Set new_org_type for all races in Organization
        # Get all races for this organization
        races = pu.get_end_nodes(self.org_id, "has")
        # Set all race types.
        for race_id in races:
            set_race_type(race_id, race_type_node)
        return


class Race:
    """
    This class instantiates to a race. This can be done as a new race that links to an organization, in which case
    org_id needs to be specified, or it can be done as a race node ID.
    """
    def __init__(self, org_id=None, race_id=None):
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
        then organization attributes will be set using method set_organization. If not found, 'False' will be returned.
        :param racetype_id: Type of the Race
        :return: True if the race is found for this organization, False otherwise.
        """
        match = "MATCH (org:Organization)-->(race:Race {name: {name}})-->(racetype:RaceType) "
        where = "WHERE id(org)={org_id} AND id(racetype)={racetype} ".format(org_id=self.org_id, racetype=racetype_id)
        ret = "RETURN id(race) as race"
        query = match + where + ret
        logging.debug("Query: {query}".format(query=query))
        race_id_arr = graph.cypher.execute(query, name=self.name)
        if len(race_id_arr) == 0:
            # No organization found on this date for this location
            return False
        elif len(race_id_arr) == 1:
            # Organization ID found, remember organization attributes
            pass
            return True
        else:
            # Todo - Error handling is required to handle more than one array returned.
            sys.exit()

    def add(self, name, racetype=None):
        """
        This method will check if the race is registered for this organization. If not, the race graph object
        (exists of race name with link to race type and the organization) will be created.
        :param name: Name of the race
        :param racetype: 1 > Hoofdwedstrijd. If False: then calculate (bijwedstrijd or Deelname).
        :return: True if the race has been registered, False if it existed already.
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
        racetype_id = pu.node_id(racetype_node)
        if self.find(racetype_id):
            # No need to register (Race exist already).
            return False
        else:
            # Race for Organization does not yet exist, register it.
            race = Node("Race", name=name)
            org_node = graph.node(self.org_id)
            graph.create(race)
            graph.create(Relationship(org_node, "has", race))
            set_race_type(race_id=pu.node_id(race), race_type_node=racetype_node)
            # Set organization paarameters by finding the created organization
            # self.find(name, location, datestamp)
            return True

    def node_set(self, nid=None):
        """
        Given the node_id, this method will configure the race object.
        :param nid: Node ID of the race node.
        :return: Fully configured race object.
        """
        logging.debug("In node_set to create race node for id {node_id}".format(node_id=nid))
        self.race_id = nid
        race_node = Node(self.race_id)
        logging.debug("Race node set")
        self.name = race_node.properties['name']
        self.org_id = self.get_org_id()
        self.label = self.set_label()
        return

    def get_org_id(self):
        """
        This method set and return the org_id for a race node_id. A valid race_id must be set.
        :return: org_id
        """
        query = """
        MATCH (org:Organization)-[:has]->(race:Race)
        WHERE id(race)={race_id}
        return id(org) as id
        """.format(race_id=self.race_id)
        org_id_arr = graph.cypher.execute(query)
        logging.debug("ID of the Org for Race ID {race_id} is {org_id}"
                      .format(org_id=org_id_arr[0], race_id=self.race_id))
        return org_id_arr[0].id

    def set_label(self):
        """
        This method will set the label for the race. Assumptions are that the race name and the organization ID are set
        already.
        :return:
        """
        logging.debug("Trying to get Organization label for org ID {org_id}".format(org_id=self.org_id))
        org_node = graph.node(self.org_id)
        org_name = org_node.properties["name"]
        self.label = "{race_name} ({org_name})".format(race_name=self.name, org_name=org_name)
        return self.label


class Location:
    def __init__(self, loc):
        self.loc = loc

    def find(self):
        loc = graph.find_one("Location", "city", self.loc)
        return loc

    def add(self):
        if not self.find():
            name = Node("Location", city=self.loc)
            graph.create(name)
            return True
        else:
            return False

    def get_node(self):
        """
        This method will get the node that is associated with the location. If the node does not exist already, it will
        be created.
        :return:
        """
        self.add()    # Register if required, ignore else
        node = self.find()
        return node


def organization_list():
    query = """
    MATCH (day:Day)<-[:On]-(org:Organization)-[:In]->(loc:Location),
          (org)-[:type]->(ot:OrgType)
    RETURN day.key as date, org.name as organization, loc.city as city, id(org) as id, ot.name as type
    ORDER BY day.key ASC
    """
    return graph.cypher.execute(query)


def organization_delete(org_id=None):
    """
    This methdod will delete an organization. This can be done only if there are no more races attached to the
    organization. If an organization is removed, then check is done for orphan date and orphan location. If available,
    these will also be removed.
    :param org_id:
    :return:
    """
    if pu.get_end_nodes(start_node_id=org_id, rel_type="has"):
        logging.info("Organization with id {org_id} cannot be removed, races are attached.".format(org_id=org_id))
        return False
    else:
        # Remove Organization
        pu.remove_node_force(org_id)
        # Check if this results in orphan dates, remove these dates
        pu.clear_date()
        # Check if this results in orphan locations, remove these locations.
        pu.clear_locations()
        logging.info("Organization with id {org_id} removed.".format(org_id=org_id))
        return True


def get_org_id(race_id):
    """
    This method will return the organization ID for a Race ID: Organization has Race.
    :param race_id: Node ID of the race.
    :return: Node ID of the organization.
    """
    org_id = pu.get_start_node(end_node_id=race_id, rel_type="has")
    return org_id


def get_org_type(org_id):
    """
    This method will get the organization Type for this organization. Type can be 'Wedstrijd' or 'Deelname'.
    :param org_id: Node ID of the Organization.
    :return: Type of the Organization: Wedstrijd or Deelname
    """
    query = """
        MATCH (org:Organization)-[:type]->(ot:OrgType)
        WHERE id(org)={org_id}
        RETURN ot.name as name
    """.format(org_id=org_id)
    res = graph.cypher.execute(query)
    return res[0][0]


def get_org_type_node(org_type_id):
    """
    This method will find the Organization Type Node.
    :param org_type_id: RadioButton selected for Organization Type.
    :return: Organization Type Node
    """
    if org_type_id == 1:
        name = "Wedstrijd"
    else:
        name = "Deelname"
    query = "MATCH (n:OrgType {name: {name}}) return n"
    res = graph.cypher.execute(query, name=name)
    return res[0][0]


def get_race_type_node(racetype):
    """
    This method will return the racetype node associated with this racetype.
    :param racetype: Racetype specifier (Hoofdwedstrijd, Bijwedstrijd, Deelname)
    :return: Racetype Node, or False if it could not be found.
    """
    if racetype in ["Hoofdwedstrijd", "Bijwedstrijd", "Deelname"]:
        # RaceType defined, so it must be Hoofdwedstrijd.
        racetype_node = graph.merge_one("RaceType", "name", racetype)
        return racetype_node
    else:
        logging.error("RaceType unknown: {racetype}.".format(racetype=racetype))
        return False


def get_races_for_org(org_id):
    """
    This method will return the list of races for an Organization ID: Organization has Race.
    :param org_id: Node ID of the Organization.
    :return: List of node IDs of races.
    """
    races = pu.get_end_nodes(start_node_id=org_id, rel_type="has")
    return races


def race_list(org_id):
    query = """
        MATCH (org:Organization)-[:has]->(race:Race)-[:type]->(racetype:RaceType)
        WHERE id(org) = {org_id}
        RETURN race.name as race, racetype.name as type, id(race) as race_id
        ORDER BY racetype.weight, race.name
    """.format(org_id=org_id)
    return graph.cypher.execute(query)


def race_label(race_id):
    query = """
        MATCH (race:Race)<-[:has]-(org)-[:On]->(date),
              (org)-[:In]->(loc)
        WHERE id(race)={race_id}
        RETURN race.name as race, org.name as org, loc.city as city, date.day as day,
               date.month as month, date.year as year
    """.format(race_id=race_id)
    recordlist = graph.cypher.execute(query)
    record = recordlist[0]
    label = "{day:02d}-{month:02d}-{year} - {city}, {race}".format(race=record["race"], city=record["city"],
                                                                   day=record["day"], month=record["month"],
                                                                   year=record["year"])
    return label


def races4person(pers_id):
    """
    This method will get the list of races for the person.
    :param pers_id: Node ID for the person
    :return: list with hash per race. Hash has race label and race type.
    """
    # Todo: Add identifier for the Competition (e.g. Stratenloop 2016).
    query = """
        MATCH (person:Person)-[:is]->(part:Participant)-[:participates]->(race:Race)
              <-[:has]-(org:Organization)-[:On]->(day:Day)
        WHERE id(person)={pers_id}
        RETURN id(race) as race_id
        ORDER BY day.key DESC
    """.format(pers_id=pers_id)
    recordlist = graph.cypher.execute(query)
    races = [{'race_id': record.race_id, 'race_label': race_label(record.race_id)} for record in recordlist]
    return races


def race_delete(race_id=None):
    """
    This methdod will delete a race. This can be done only if there are no more participants attached to the
    race.
    :param race_id: Node ID of the race to be removed.
    :return: True if race is removed, False otherwise.
    """
    if pu.get_start_nodes(end_node_id=race_id, rel_type="participates"):
        logging.info("Race with id {race_id} cannot be removed, participants are attached.".format(race_id=race_id))
        return False
    else:
        # Remove Organization
        pu.remove_node_force(race_id)
        logging.info("Race with id {race_id} removed.".format(race_id=race_id))
        return True


def person_list():
    """
    Return the list of persons in hash of id, name.
    :return: List of persons. Each person is represented in a hash id, name of the person.
    """
    query = """
        MATCH (n:Person)
        RETURN id(n) as id, n.name as name
        ORDER BY n.name ASC
    """
    return graph.cypher.execute(query)


def person4participant(part_id):
    """
    This method will get the person name from a participant ID. First it will convert the participant ID to a
    participant node. Then it gets the (reverse) relation ('is') from participant to person.
    Finally it will return the id and the name of the person in a hash.
    :param part_id: Node ID of the participant.
    :return: Name (label) associated with the person
    """
    logging.debug("Trying to find participant node for ID: {part_id}".format(part_id=part_id))
    # First get Node from participant ID
    part = graph.node(part_id)
    # Then get relation from participant to person.
    rel = next(item for item in graph.match(end_node=part, rel_type="is"))
    # logging.debug("Node: {node}".format(node=rel.start_node.ref))
    pers_name = rel.start_node["name"]
    pers_id = pu.node_id(rel.start_node)
    return dict(name=pers_name, id=pers_id)


def participant_list(race_id):
    """
    Returns the list of participants in hash of id, name.
    :param race_id: ID of the race for which current participants are returned
    :return: List of participants. Each participant is represented as a hash id, name of the participant.
    """
    query = """
        MATCH (n)-[:is]->()-[:participates]->(race)
        WHERE id(race) = {race_id}
        RETURN id(n) as id, n.name as name
        ORDER BY n.name ASC
    """.format(race_id=race_id)
    return graph.cypher.execute(query)


def participant_seq_list(race_id):
    """
    This method will collect the people in a race in sequence of arrival.
    :param race_id: ID of the race for which the participants are returned in sequence of arrival.
    :return: List of names of the participants in the race. Each item has the person ID and the person name.
    """
    query = """
        MATCH race_ptn = (race)<-[:participates]-(participant),
              participants = (participant)<-[:after*0..]-()
        WHERE id(race) = {race_id}
        WITH COLLECT(participants) AS results, MAX(length(participants)) AS maxLength
        WITH FILTER(result IN results WHERE length(result) = maxLength) AS result_coll
        UNWIND result_coll as result
        RETURN nodes(result)
    """.format(race_id=race_id)
    # Get the result of the query in a recordlist
    recordlist = graph.cypher.execute(query)
    finisher_list = []
    # If there are finishers, then recordlist has one element, which is a nodelist
    if len(recordlist) > 0:
        node_list = recordlist[0][0]
        # For each node (participant), find the person name (this may be converted to function).
        for part in node_list:
            # graph.match returns iterator. There can be one relation only so getting the first item of the iterator
            # is sufficient.
            rel = next(item for item in graph.match(end_node=part, rel_type="is"))
            logging.debug("Node: {node}".format(node=rel.start_node.ref))
            pers_name = rel.start_node["name"]
            pers_id = pu.node_id(rel.start_node)
            logging.debug("pers_name: {pers_name}, pers_id: {pers_id}".format(pers_name=pers_name, pers_id=pers_id))
            pers_obj = [pers_id, pers_name]
            finisher_list.append(pers_obj)
    return finisher_list


def participant_after_list(race_id):
    """
    This method will return the participant sequence list as a SelectField list. It will call participant_seq_list
    and 'prepend' a value for 'eerste aankomer' (value -1).
    :param race_id: Node ID of the race
    :return: List of the names of the participants and value for 'eerste aankomer'.
    """
    eerste = [-1, 'Eerste aankomst']
    finisher_list = participant_seq_list(race_id)
    finisher_list.insert(0, eerste)
    return finisher_list


def participant_last_id(race_id):
    """
    This method will get the ID of the last participant in the race. It call check participant_after_list and fetch
    the last ID of the runner. This way no special threatment is required in case there are no participants. The
    ID of the last runner will redirect to -1 then.
    :param race_id: Node ID of the race.
    :return: Node ID of the last finisher so far in the race, -1 if no finishers registered yet.
    """
    finisher_list = participant_after_list(race_id)
    part_arr = finisher_list.pop()
    part_last = part_arr[0]
    logging.debug("ID of last finisher: {part_last}".format(part_last=part_last))
    return part_last


def participant_first_id(race_id):
    """
    This method will get the ID of the first person in the race.
    :param race_id: Node ID of the race.
    :return: Node ID of the first person so far in the race, -1 if no finishers registered yet.
    """
    finisher_list = participant_seq_list(race_id)
    if len(finisher_list):
        person_id = int(finisher_list[0][0])
    else:
        person_id = -1
    logging.debug("This is person_id {person_id} from finisher_list {fl} - race_id {race_id}"
                  .format(person_id=person_id, fl=finisher_list, race_id=race_id))
    return person_id


def next_participant(race_id):
    """
    This method will get the list of potential next participants. This is the list of all persons minus the people that
    have been selected already in this race. Also all people that have been selected in other races for this
    organization will no longer be available for selection.
    :param race_id:
    :return:
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


def init_graph(config):
    """
    This method will initialize the graph. It will set indeces and create nodes required for the application
    (on condition that the nodes do not exist already).
    :param config: Config object
    :return:
    """
    stmt = "CREATE CONSTRAINT ON (n:{0}) ASSERT n.{1} IS UNIQUE"
    graph.cypher.execute(stmt.format('Location', 'city'))
    graph.cypher.execute(stmt.format('Person', 'name'))
    graph.cypher.execute(stmt.format('RaceType', 'name'))
    graph.cypher.execute(stmt.format('OrgType', 'name'))

    # RaceType
    hoofdwedstrijd = graph.merge_one("RaceType", "name", "Hoofdwedstrijd")
    bijwedstrijd = graph.merge_one("RaceType", "name", "Bijwedstrijd")
    deelname = graph.merge_one("RaceType", "name", "Deelname")
    hoofdwedstrijd['beschrijving'] = config['RaceType']['hoofdwedstrijd']
    bijwedstrijd['beschrijving'] = config['RaceType']['bijwedstrijd']
    deelname['beschrijving'] = config['RaceType']['deelname']
    # Weight factor is used to sort the types in selection lists.
    hoofdwedstrijd['weight'] = 10
    bijwedstrijd['weight'] = 20
    deelname['weight'] = 100
    hoofdwedstrijd.push()
    bijwedstrijd.push()
    deelname.push()
    # OrgType
    wedstrijd = graph.merge_one("OrgType", "name", "Wedstrijd")
    org_deelname = graph.merge_one("OrgType", "name", "Deelname")
    wedstrijd['beschrijving'] = config['OrgType']['wedstrijd']
    org_deelname['beschrijving'] = config['OrgType']['deelname']
    wedstrijd.push()
    org_deelname.push()
    return


def racetype_list():
    """
    This method will get all the race types. It will return them as a list of tuples with race type ID and race type
    name.
    :return:
    """
    query = "match (n:RaceType) return id(n) as id, n.name as name"
    race_types = graph.cypher.execute(query)
    return race_types


def set_race_type(race_id=None, race_type_node=None):
    """
    Check if old node type is defined. If so, remove the link.
    Then add new link.
    :param race_id: Node ID for the race
    :param race_type_node:
    :return:
    """
    race_node = pu.node(race_id)
    # Check if there is a link now.
    curr_race_type_id = pu.get_end_node(race_id, "type")
    if curr_race_type_id:
        pu.remove_relation(race_id, curr_race_type_id, "type")
    pu.create_relation(start_node=race_node, end_node=race_type_node, rel_type="type")
    return
