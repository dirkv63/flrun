import logging
import sys
from . import db, lm
from flask_login import UserMixin
from py2neo import Graph, Node, Relationship, watch
from py2neo.ext.calendar import GregorianCalendar
from werkzeug.security import generate_password_hash, check_password_hash

graph = Graph()
calendar = GregorianCalendar(graph)
watch("py2neo.cypher")


class Person:
    def __init__(self, name):
        self.name = name

    def find(self):
        name = graph.find_one("Person", "name", self.name)
        return name

    def register(self):
        if not self.find():
            name = Node("Person", name=self.name)
            graph.create(name)
            return True
        else:
            return False


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


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), index=True, unique=True)
    passwork_hash = db.Column(db.String(64))

    def set_password(self, password):
        self.passwork_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passwork_hash, password)

    @staticmethod
    def register(username, password):
        user = User()
        user.username = username
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

    def __repr__(self):
        return "<User {user}>".format(user=self.username)


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
    RETURN n.name as name
    ORDER BY n.name ASC
    """
    return graph.cypher.execute(query)


@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
