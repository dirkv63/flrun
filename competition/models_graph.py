import logging
import sys
from py2neo import Graph, Node, Relationship
from py2neo.ext.calendar import GregorianCalendar

graph = Graph()
calendar = GregorianCalendar(graph)
# watch("py2neo.cypher")


class Participant:
    def __init__(self):
        self.prev_runner_id = -1
        self.runner_id = -1
        self.race_id = -1
        self.comp_id = -1   # Allows to configure if participation in competion is OK: wearing shirt, ...

    def set(self, race_id=None, runner_id=None, prev_runner_id=None):
        """
        This method will set the participant in the race. The participant will be linked to the race,
        to the competition, (if applicable) to the prev runner and (if applicable) to the next runner.
        :param race_id:
        :param runner_id:
        :param prev_runner_id:
        :return:
        """
        if race_id:
            self.race_id = race_id
        if runner_id:
            self.runner_id = runner_id
        if prev_runner_id:
            self.prev_runner_id = prev_runner_id
        # Find last runner so far, to link to the previous runner
        # This must execute BEFORE creating current participant node,
        # otherwise that is the one that will be returned...
        query = """
        MATCH (prev_part:Participant)-[:participates]->(race:Race)
        WHERE (NOT (prev_part)<-[:after]-(:Participant))
          AND id(race)={race_id}
        return prev_part
        """.format(race_id=self.race_id)
        prev_part_arr = graph.cypher.execute(query)
        # Create Participant node
        participant = Node("Participant")
        # Link to prev_participant (if it exist)
        if len(prev_part_arr) > 0:
            prev_part_node = prev_part_arr[0].prev_part
            graph.create(Relationship(participant, 'after', prev_part_node))
        race = graph.node(race_id)
        graph.create(Relationship(participant, "participates", race))
        runner = graph.node(runner_id)
        graph.create(Relationship(runner, "is", participant))
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

    def add(self, name):
        """
        Attempt to add the participant with name 'name'. The name must be unique. Person object is set to current
        participant. Name is set in this procedure, ID is set in the find procedure.
        :param name: Name of the participant
        :return: True, if registered. False otherwise.
        """
        self.name = name
        if self.find():
            # Person is found, Name and ID set, no need to register.
            return False
        else:
            # Person not found, register participant.
            name = Node("Person", name=self.name)
            graph.create(name)
            # Now call find() again to set ID for the person
            self.find()
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


class Organization:
    """
    This class instantiates to an organization.
    """
    def __init__(self):
        self.name = 'NotYetDefined'
        self.org_id = -1
        self.label = 'NotYetDefined'

    def find(self, name, location, datestamp):
        """
        This method searches for the organization based on organization name, location and datestamp. If found,
        then organization attributes will be set using method set_organization. If not found, 'False' will be returned.
        :param name: Name of the organization
        :param location: City where the organization is
        :param datestamp: Date of the organization
        :return: True if organization is found, False otherwise.
        """
        query = """
        MATCH (day:Day {key: {datestamp}})<-[:On]-(org:Organization {name: {name}}),
        (org)-[:In]->(loc:Location {city: {location}})
        RETURN id(org) as org_id
        """
        org_id_arr = graph.cypher.execute(query, name=name, location=location, datestamp=datestamp)
        if len(org_id_arr) == 0:
            # No organization found on this date for this location
            return False
        elif len(org_id_arr) == 1:
            # Organization ID found, remember organization attributes
            self.set(org_id_arr[0].org_id)
            return True
        else:
            # Todo - Error handling is required to handle more than one array returned.
            sys.exit()

    def add(self, name, location, datestamp):
        """
        This method will check if the organization is registered already. If not, the organization graph object
        (exists of organization name with link to date and city where it is organized) will be created.
        The organization instance attributes will be set.
        :param name: Name of the organization
        :param location: City where the organization takes place
        :param datestamp: Date of the organization.
        :return: True if the organization has been registered, False if it existed already.
        """
        logging.debug("Name: {name}, Location: {location}, Date: {datestamp}"
                      .format(name=name, location=location, datestamp=type(datestamp)))
        if self.find(name, location, datestamp):
            # No need to register (Organization exist already), and organization attributes are set.
            return False
        else:
            # Organization on Location and datestamp does not yet exist, register it.
            loc = Location(location).get_node()   # Get Location Node
            # year, month, day = [int(x) for x in datestamp.split('-')]
            date_node = calendar.date(datestamp.year, datestamp.month, datestamp.day).day   # Get Date (day) node
            org = Node("Organization", name=name)
            graph.create(org)
            graph.create(Relationship(org, "On", date_node))
            graph.create(Relationship(org, "In", loc))
            # Set organization paarameters by finding the created organization
            self.find(name, location, datestamp)
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
        MATCH (day:Day)<-[:On]-(org:Organization)-[:In]->(loc:Location)
        WHERE id(org) = {org_id}
        RETURN day.key as date, org.name as org, loc.city as city
        """.format(org_id=org_id)
        org_array = graph.cypher.execute(query)
        this_org = org_array[0]
        # Todo - expecting one and exactly one row back. Handle errors?
        self.label = "{org_name} ({city}, {date})".format(org_name=this_org.org,
                                                          city=this_org.city,
                                                          date=this_org.date)
        logging.debug("Label: {label}".format(label=self.label))
        self.name = this_org.org
        self.org_id = org_id
        return True

    def get(self):
        return self.label


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
            self.node_set(node_id=race_id)

    def find(self, racetype):
        """
        This method searches for the organization based on organization name, location and datestamp. If found,
        then organization attributes will be set using method set_organization. If not found, 'False' will be returned.
        :param racetype: Type of the Race
        :return: True if the race is found for this organization, False otherwise.
        """
        match = "MATCH (org:Organization)-->(race:Race {name: {name}})-->(racetype:RaceType) "
        where = "WHERE id(org)={org_id} AND id(racetype)={racetype} ".format(org_id=self.org_id, racetype=racetype)
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

    def add(self, name, racetype):
        """
        This method will check if the race is registered for this organization. If not, the race graph object
        (exists of race name with link to race type and the organization) will be created.
        :param name: Name of the race
        :param racetype: Type of the race
        :return: True if the race has been registered, False if it existed already.
        """
        # Todo - add tests on race type: deelname must be for each race of organization, hoofdwedstrijd only one.
        logging.debug("Name: {name}".format(name=name))
        self.name = name
        if self.find(racetype):
            # No need to register (Race exist already).
            return False
        else:
            # Race for Organization does not yet exist, register it.
            race = Node("Race", name=name)
            racetype_node = graph.node(racetype)
            org_node = graph.node(self.org_id)
            graph.create(race)
            graph.create(Relationship(org_node, "has", race))
            graph.create(Relationship(race, "type", racetype_node))
            # Set organization paarameters by finding the created organization
            # self.find(name, location, datestamp)
            return True

    def node_set(self, node_id=None):
        """
        Given the node_id, this method will configure the race object.
        :param node_id: Node ID of the race node.
        :return: Fully configured race object.
        """
        logging.debug("In node_set to create race node for id {node_id}".format(node_id=node_id))
        self.race_id = node_id
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
    logging.debug("In models.get_organization")
    query = """
    MATCH (day:Day)<-[:On]-(org:Organization)-[:In]->(loc:Location)
    RETURN day.key as date, org.name as organization, loc.city as city, id(org) as id
    ORDER BY day.key ASC
    """
    return graph.cypher.execute(query)


def race_list(org_id):
    logging.debug("In models.get_races for org_id: {org_id}".format(org_id=org_id))
    query = """
    MATCH (org:Organization)-[:has]->(race:Race)-[:type]->(racetype:RaceType)
    WHERE id(org) = {org_id}
    RETURN race.name as race, racetype.name as type, id(race) as race_id
    ORDER BY racetype.weight, race.name
    """.format(org_id=org_id)
    return graph.cypher.execute(query)


def person_list():
    query = """
        MATCH (n:Person)
        RETURN id(n) as id, n.name as name
        ORDER BY n.name ASC
    """
    return graph.cypher.execute(query)


def participant_list(race_id):
    query = """
        MATCH (n)-[:is]->()-[:participates]->(race)
        WHERE id(race) = {race_id}
        RETURN id(n) as id, n.name as name
        ORDER BY n.name ASC
    """.format(race_id=race_id)
    return graph.cypher.execute(query)


def participant_seq_list(race_id):
    query = """
        MATCH race_ptn = (race),
              finishers = (finisher)-[:is]->(participant)<-[:after*]-()
        WHERE ()<-[:participates]-(participant)
          AND id(race) = {race_id}
        WITH COLLECT(finishers) AS results, MAX(length(finishers)) AS maxLength
        WITH FILTER(result IN results WHERE length(result) = maxLength) AS result_coll
        UNWIND result_coll as result
        RETURN nodes(result)
    """.format(race_id=race_id)
    # Todo: convert to list of participants
    return graph.cypher.execute(query)


def next_participant(race_id):
    """
    This method will get the list of potential next participants. This is the list of all persons minus the people that
    have been selected already in this race.
    :param race_id:
    :return:
    """
    # Todo: extend to participants that have been selected for this organization (one participation per race per org.)
    participants = participant_list(race_id)
    persons = person_list()
    next_participants = [part for part in persons if part not in participants]
    return next_participants


def relations(node_id):
    """
    This method will check if node with ID has relations. Returns True if there are relations, returns False otherwise.
    :param node_id: ID of the object to check relations
    :return: True - if there are relations, False - there are no relations.
    """
    logging.debug("In method relations for id {node_id}".format(node_id=node_id))
    query = """
        MATCH (n)
        WHERE ((n)-[]-())
          AND (id(n)={node_id})
        RETURN n
            """
    res_array = graph.cypher.execute(query.format(node_id=node_id))
    if len(res_array):
        logging.debug("Relations found")
        return True
    else:
        logging.debug("No Relations found")
        return False


def remove_node(node_id):
    """
    This method will remove node with ID node_id. Nodes can be removed only if there are no relations attached to the
    node.
    :param node_id:
    :return: True if node is deleted, False otherwise
    """
    if relations(node_id):
        logging.error("Request to delete node ID {node_id}, but relations found. Node not deleted"
                      .format(node_id=node_id))
        return False
    else:
        query = "MATCH (n) WHERE id(n)={node_id} DELETE n"
        graph.cypher.execute(query.format(node_id=node_id))
        return True


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
