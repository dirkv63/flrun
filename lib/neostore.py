"""
This class consolidates functions related to the neo4J datastore.
"""

import logging
import sys
import uuid
from py2neo import Graph, Node, Relationship, NodeSelector
from py2neo.database import DBMS


class NeoStore:

    def __init__(self, config):
        """
        Method to instantiate the class in an object for the neostore.
        :param config object, to get connection parameters.
        :return: Object to handle neostore commands.
        """
        logging.debug("Initializing Neostore object")
        self.config = config
        self.graph = self._connect2db()
        self.selector = NodeSelector(self.graph)
        return

    def _connect2db(self):
        """
        Internal method to create a database connection. This method is called during object initialization.
        :return: Database handle and cursor for the database.
        """
        logging.debug("Creating Neostore object.")
        neo4j_config = {
            'user': self.config['Graph']['username'],
            'password': self.config['Graph']['password'],
        }
        # Connect to Graph
        graph = Graph(**neo4j_config)
        # Check that we are connected to the expected Neo4J Store - to avoid accidents...
        dbname = DBMS().database_name
        if dbname != self.config['Graph']['neo_db']:
            logging.fatal("Connected to Neo4J database {d}, but expected to be connected to {n}"
                          .format(d=dbname, n=self.config['Main']['neo_db']))
            sys.exit(1)
        return graph

    def create_node(self, *labels, **props):
        """
        Function to create node. The function will return the node object.
        Note that a 'nid' attribute will be added to the node. This is a UUID4 unique identifier. This is a temporary
        solution cause there seems to be no other way to extract the node ID from a node.
        @param labels: Labels for the node
        @param props: Value dictionary with values for the node.
        @return:
        """
        props['nid'] = str(uuid.uuid4())
        component = Node(*labels, **props)
        self.graph.create(component)
        return component

    def create_relation(self, left_node, rel, right_node):
        """
        Function to create relationship between nodes.
        @param left_node:
        @param rel:
        @param right_node:
        @return:
        """
        rel = Relationship(left_node, rel, right_node)
        self.graph.merge(rel)
        return

    def clear_date_node(self, label):
        """
        This method will clear the date node as specified by label. Label can be Day, Month or Year.
        :param label: Day, Month or Year
        :return:
        """
        query = """
            MATCH (n:«label»)-[rel]-()
            WITH n, count(rel) as rel_cnt
            WHERE rel_cnt=1
            RETURN id(n) as nid, n.key as key
        """
        reclist = self.graph.cypher.execute(query, label=label)
        for rec in reclist:
            logging.info("Deleting date node {date}".format(date=rec.key))
            self.remove_node_force(rec.nid)
        return

    def clear_date(self):
        """
        This method will clear dates that are no longer connected to an organization, a person's birthday or any other
        item.
        First find days with one relation only, this must be a connection to the month. Remove these days.
        Then find months with one relation only, this must be a connection to the year. Remove these months.
        Finally find years with one relation only, this must be a connection to the Gregorian calendar. Remove these
        years.
        Compare with method remove_date(ds), that will check to remove only a specific date.
        :return:
        """
        # First Remove Days
        self.clear_date_node("Day")
        self.clear_date_node("Month")
        self.clear_date_node("Year")
        return

    def node(self, nid):
        """
        This method will get a node ID and return a node, (or false in case no Node can be associated with the ID.
        The current release of py2neo 3.1.2 throws a IndexError in case a none-existing node ID is requested.)
        Note that since there seems to be no way to extract the Node ID of a node, the nid attribute is used. As a
        consequence, it is not possible to use the node(nid).
        :param nid: ID of the node to be found.
        :return: Node, or False (None) in case the node could not be found.
        """
        """
        try:
            node_obj = self.graph.node(nid)
        except IndexError:
            logging.error("Non-existing node ID: {nid}".format(nid=nid))
            return False
        else:
            return node_obj
        """
        selected = self.selector.select(nid=nid)
        node = selected.first()
        return node

    def node_id(self, node_obj):
        """
        py2neo 3.1.2 doesn't have a method to get the ID from a node.
        Not sure how to get an ID from a node...
        Advice from Neo4J community seems to be not to use internal Node ID, since this can be reused when nodes are
        removed.
        For now each node has an attribute nid which contains a random node ID.

        :param node_obj: Node object
        :return: ID of the node (integer), or False.
        """
        # First check if my object is a node (not sure it is a node, but I am sure it is a subgraph)
        try:
            self.graph.exists(node_obj)
            # OK, my object is a node (or a relation?). Now return the nid attribute
            return node_obj['nid']
        except TypeError:
            logging.error("Node expected, but got object of type {nodetype}".format(nodetype=type(node_obj)))
            return False

    def node_props(self, nid=None):
        """
        This method will get a node and return the node properties in a dictionary.
        :param nid: nid of the node required
        :return: Dictionary of the node properties
        """
        my_node = self.node(nid)
        if my_node:
            logging.debug("Node Properties: {props}".format(props=dict(my_node)))
            return dict(my_node)
        else:
            logging.error("Could not bind ID {node_id} to a node.".format(node_id=nid))
            return False

    def node_update(self, nid, **properties):
        """
        This method will update the node's properties with the properties specified. Modified properties will be
        updated, new properties will be added and removed properties will be deleted.
        :param nid: ID of the node to modify.
        :param properties: Dictionary of the property set for the node. 'nid' cannot be part of it, but will be set.
        :return: True if successful update, False otherwise.
        """
        my_node = self.node(nid)
        if my_node:
            curr_props = self.node_props(nid)
            # Remove properties
            remove_props = [prop for prop in curr_props if prop not in properties]
            for prop in remove_props:
                # Set value to None to remove a key.
                del my_node[prop]
            # Modify properties and add new properties
            for prop in properties:
                my_node[prop] = properties[prop]
            # Also add nid again...
            my_node['nid'] = nid
            # Now push the changes to Neo4J database.
            self.graph.push(my_node)

    def remove_node_force(self, nid):
        """
        This method will remove node with ID node_id. The node and the relations to/from the node will also be deleted.
        Use 'remove_node' to remove nodes only when there should be no relations attached to it.
        :param nid: ID of the node
        :return: True if node is deleted, False otherwise
        """
        logging.debug("Trying to remove node with ID {nid}".format(nid=nid))
        query = "MATCH (n) WHERE id(n)={node_id} DETACH DELETE n"
        self.graph.cypher.execute(query.format(node_id=nid))
        return True
