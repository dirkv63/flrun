import logging
import sys
from py2neo import Graph, Node, Relationship
from py2neo.ext.calendar import GregorianCalendar

graph = Graph()
calendar = GregorianCalendar(graph)
# watch("py2neo.cypher")


class Person:
    def __init__(self):
        self.name = 'NotYetDefined'
        self.person_id = -1

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

    def register(self, name):
        """
        Attempt to register the participant with name 'name'. The name must be unique. Person object is set to current
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

    def set_person(self, person_id):
        """
        This method will get the person associated with this ID. The assumption is that the person_id relates to a
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
        return True

    def get_name(self):
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
            self.set_organization(org_id_arr[0].org_id)
            return True
        else:
            # Todo - Error handling is required to handle more than one array returned.
            sys.exit()

    def register(self, name, location, datestamp):
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

    def set_organization(self, org_id):
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

    def get_label(self):
        return self.label


class Location:
    def __init__(self, loc):
        self.loc = loc

    def find(self):
        loc = graph.find_one("Location", "city", self.loc)
        return loc

    def register(self):
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
        self.register()    # Register if required, ignore else
        node = self.find()
        return node


def get_organizations():
    logging.info("In models.get_organization")
    query = """
    MATCH (day:Day)<-[:On]-(org:Organization)-[:In]->(loc:Location)
    RETURN day.key as date, org.name as organization, loc.city as city, id(org) as id
    ORDER BY day.key ASC
    """
    return graph.cypher.execute(query)


def get_participants():
    logging.info("In models.get_participants")
    query = """
        MATCH (n:Person)
        RETURN n.name as name, id(n) as id
        ORDER BY n.name ASC
    """
    return graph.cypher.execute(query)


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
