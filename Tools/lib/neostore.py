"""
This class consolidates functions related to the neo4J datastore.
"""

import logging
import sys
import uuid
from py2neo import Graph, Node, Relationship, NodeSelector
from py2neo.database import DBMS
from py2neo.ext.calendar import GregorianCalendar


class NeoStore:

    def __init__(self, **n4j_params):
        """
        Method to instantiate the class in an object for the neostore.
        :param config object, to get connection parameters.
        :return: Object to handle neostore commands.
        """
        logging.debug("Initializing Neostore object")
        self.graph = self._connect2db(**n4j_params)
        self.calendar = GregorianCalendar(self.graph)
        self.selector = NodeSelector(self.graph)
        return

    def _connect2db(self, **n4j_params):
        """
        Internal method to create a database connection. This method is called during object initialization.
        :return: Database handle and cursor for the database.
        """
        logging.debug("Creating Neostore object.")
        neo4j_config = {
            'user': n4j_params['user'],
            'password': n4j_params['password'],
        }
        # Connect to Graph
        graph = Graph(**neo4j_config)
        # Check that we are connected to the expected Neo4J Store - to avoid accidents...
        dbname = DBMS().database_name
        if dbname != n4j_params['db']:
            logging.fatal("Connected to Neo4J database {d}, but expected to be connected to {n}"
                          .format(d=dbname, n=n4j_params['db']))
            sys.exit(1)
        return graph

    def clear_locations(self):
        """
        This method will check if there are orphan locations. These are locations without relations. These locations
        can be removed.
        :return:
        """
        # Note that you could DETACH DELETE location nodes here, but then you miss the opportunity to log what is
        # removed.
        query = """
            MATCH (loc:Location) WHERE NOT (loc)--() RETURN loc.nid as loc_nid, loc.city as city
        """
        res = self.graph.run(query)
        for locs in res:
            logging.info("Remove location {city} with nid {loc_nid}".format(city=locs['city'], loc_nid=locs['loc_nid']))
            self.remove_node(locs['loc_nid'])
        return

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

    def create_relation(self, left_node=None, rel=None, right_node=None):
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
        This method will clear every date node as specified by label. Label can be Day, Month or Year. The node will be
        deleted if not used anymore. So it can have only one incoming relation: DAY - MONTH or YEAR.
        Therefore find all relations. If there is only one, then the date node can be deleted.
        :param label: Day, Month or Year
        :return:
        """
        logging.info("Clearing all date nodes with label {l}".format(l=label))
        query = """
            MATCH (n:{label})-[rel]-()
            WITH n, count(rel) as rel_cnt
            WHERE rel_cnt=1
            DETACH DELETE n
        """.format(label=label.capitalize())
        self.graph.run(query)
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

    def date_node(self, ds):
        """
        This method will get a datetime.date timestamp and return the associated node. The calendar module will
        ensure that the node is created if required.
        :param ds: datetime.date representation of the date.
        :return: node associated with the date
        """
        date_node = self.calendar.date(ds.year, ds.month, ds.day).day   # Get Date (day) node
        return date_node

    def get_end_node(self, start_node_id=None, rel_type=None):
        """
        This method will calculate the end node from an start Node ID and a relation type. If relation type is not
        specified then any relation type will do.
        The purpose of the function is to find a single end node. If there are multiple end nodes, then a random one
        is returned and an error message will be displayed.
        :param start_node_id: Node ID of the start node.
        :param rel_type: Relation type
        :return: Node ID (integer) of the end Node, or False.
        """
        logging.debug("Find End Node. Start node ID: {node_id}, Relation Type: {rel_type}"
                      .format(node_id=start_node_id, rel_type=rel_type))
        # First get Node from end node ID
        start_node = self.node(start_node_id)
        if start_node:
            # Then get relation to end node.
            try:
                rel = next(item for item in self.graph.match(start_node=start_node, rel_type=rel_type))
            except StopIteration:
                logging.warning("No end node found for start node ID {nid} and relation {rel}"
                                .format(nid=start_node_id, rel=rel_type))
            else:
                # Check if there are more elements in the iterator.
                if len([item for item in self.graph.match(start_node=start_node, rel_type=rel_type)]) > 1:
                    logging.warning("More than one end node found for start node ID {nid} and relation {rel},"
                                    " returning first".format(nid=start_node_id, rel=rel_type))
                end_node_id = self.node_id(rel.end_node())
                return end_node_id
        else:
            logging.error("Non-existing start node ID: {start_node_id}".format(start_node_id=start_node_id))
            return False

    def get_end_nodes(self, start_node_id=None, rel_type=None):
        """
        This method will calculate all end nodes from a start Node ID and a relation type. If relation type is not
        specified then any relation type will do.
        The purpose of the function is to find all end nodes.
        :param start_node_id: Node ID of the start node.
        :param rel_type: Relation type
        :return: List with Node IDs (integers) of the end Nodes, or False.
        """
        logging.debug("Find End Nodes. Start Node ID: {node_id}, Relation Type: {rel_type}"
                      .format(node_id=start_node_id, rel_type=rel_type))
        # First get Node from end node ID
        start_node = self.node(start_node_id)
        if start_node.exists:
            # Then get relation to end node.
            node_list = [self.node_id(rel.end_node())
                         for rel in self.graph.match(start_node=start_node, rel_type=rel_type)]
            return node_list
        else:
            logging.error("Non-existing start node ID: {start_node_id}".format(start_node_id=start_node_id))
            return False

    def get_start_node(self, end_node_id=None, rel_type=None):
        """
        This method will calculate the start node from an end Node ID and a relation type. If relation type is not
        specified then any relation type will do.
        The purpose of the function is to find a single start node. If there are multiple start nodes, then a random
        one is returned and an error message will be displayed.
        :param end_node_id: Node nid of the end node.
        :param rel_type: Relation type
        :return: Node nid of the start Node, or False.
        """
        logging.debug("Find Start Node. End Node ID: {node_id}, Relation Type: {rel_type}"
                      .format(node_id=end_node_id, rel_type=rel_type))
        # First get Node from end node ID
        end_node = self.node(end_node_id)
        if end_node:
            # Then get relation to end node.
            try:
                rel = next(item for item in self.graph.match(end_node=end_node, rel_type=rel_type))
            except StopIteration:
                logging.warning("No start node found for end node ID {nid} and relation {rel}"
                                .format(nid=end_node_id, rel=rel_type))
            else:
                # Check if there are more elements in the iterator.
                if len([item for item in self.graph.match(end_node=end_node, rel_type=rel_type)]) > 1:
                    logging.warning("More than one start node found for end node ID {nid} and relation {rel},"
                                    " returning first".format(nid=end_node_id, rel=rel_type))
                start_node_id = self.node_id(rel.start_node())
                return start_node_id
        else:
            logging.error("Non-existing end node ID: {end_node_id}".format(end_node_id=end_node_id))
            return False

    def get_start_nodes(self, end_node_id=None, rel_type=None):
        """
        This method will calculate all start nodes from an end Node ID and a relation type. If relation type is not
        specified then any relation type will do.
        The purpose of the function is to find all start nodes.
        :param end_node_id: Node nid of the end node.
        :param rel_type: Relation type
        :return: List with Node IDs (integers) of the start Node, or False.
        """
        logging.debug("Find Start Nodes. End Node ID: {node_id}, Relation Type: {rel_type}"
                      .format(node_id=end_node_id, rel_type=rel_type))
        # First get Node from end node ID
        end_node = self.node(end_node_id)
        if end_node:
            # Then get relation to end node.
            node_list = [self.node_id(rel.start_node())
                         for rel in self.graph.match(end_node=end_node, rel_type=rel_type)]
            return node_list
        else:
            logging.error("Non-existing end node ID: {end_node_id}".format(end_node_id=end_node_id))
            return False

    def init_graph(self, **node_params):
        """
        This method will initialize the graph. It will set indeces and create nodes required for the application
        (on condition that the nodes do not exist already).
        :return:
        """
        stmt = "CREATE CONSTRAINT ON (n:{0}) ASSERT n.{1} IS UNIQUE"
        self.graph.cypher.execute(stmt.format('Location', 'city'))
        self.graph.cypher.execute(stmt.format('Person', 'name'))
        self.graph.cypher.execute(stmt.format('RaceType', 'name'))
        self.graph.cypher.execute(stmt.format('OrgType', 'name'))

        # RaceType
        hoofdwedstrijd = self.graph.merge_one("RaceType", "name", "Hoofdwedstrijd")
        bijwedstrijd = self.graph.merge_one("RaceType", "name", "Bijwedstrijd")
        deelname = self.graph.merge_one("RaceType", "name", "Deelname")
        hoofdwedstrijd['beschrijving'] = node_params['hoofdwedstrijd']
        bijwedstrijd['beschrijving'] = node_params['bijwedstrijd']
        deelname['beschrijving'] = node_params['deelname']
        # Weight factor is used to sort the types in selection lists.
        hoofdwedstrijd['weight'] = 10
        bijwedstrijd['weight'] = 20
        deelname['weight'] = 100
        hoofdwedstrijd.push()
        bijwedstrijd.push()
        deelname.push()
        # OrgType
        wedstrijd = self.graph.merge_one("OrgType", "name", "Wedstrijd")
        org_deelname = self.graph.merge_one("OrgType", "name", "Deelname")
        wedstrijd['beschrijving'] = node_params['wedstrijd']
        org_deelname['beschrijving'] = node_params['o_deelname']
        wedstrijd.push()
        org_deelname.push()
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
            return True
        else:
            logging.error("No node found for NID {nid}".format(nid=nid))
            return False

    def relations(self, nid):
        """
        This method will check if node with ID has relations. Returns True if there are relations, returns False
        otherwise.
        :param nid: ID of the object to check relations
        :return: Number of relations - if there are relations, False - there are no relations.
        """
        logging.debug("In method relations for nid {node_id}".format(node_id=nid))
        obj_node = self.node(nid)
        if obj_node:
            if obj_node.degree():
                logging.debug("Relations found")
                return obj_node.degree()
            else:
                logging.debug("No Relations found")
        else:
            logging.error("ID {id} cannot be bound to a node".format(id=nid))
        return False

    def remove_date(self, ds):
        """
        This method will verify if a date can be removed. Day must have more than only 'DAY' relation, Month should have
        more than only "MONTH" relation and Year should have more than only incoming "YEAR" relation.
        You need to find all nodes (day, month, year) before attempting to remove them. calender.date function will
        create them in all cases. Compare with method clear_date(), that will scan the database and remove all days,
        months and years that are no longer used.
        :param ds: Datestamp of the Date (YYYY-MM-DD, as provided by Day.Key)
        :return:
        """
        day_node = self.calendar.date(ds.year, ds.month, ds.day).day
        day_node_id = self.node_id(day_node)
        month_node = self.calendar.date(ds.year, ds.month, ds.day).month
        month_node_id = self.node_id(month_node)
        year_node = self.calendar.date(ds.year, ds.month, ds.day).year
        year_node_id = self.node_id(year_node)
        if self.relations(day_node_id) == 1:
            self.remove_node_force(day_node_id)
            if self.relations(month_node_id) == 1:
                self.remove_node_force(month_node_id)
                if self.relations(year_node_id) == 1:
                    self.remove_node_force(year_node_id)
        return

    def remove_node(self, nid):
        """
        This method will remove node with ID node_id. Nodes can be removed only if there are no relations attached to
        the node.
        :param nid:
        :return: True if node is deleted, False otherwise
        """
        if self.relations(nid):
            logging.error("Request to delete node nid {node_id}, but relations found. Node not deleted"
                          .format(node_id=nid))
            return False
        else:
            query = "MATCH (n) WHERE n.nid={nid} DELETE n"
            self.graph.run(query, nid=nid)
            return True

    def remove_node_force(self, nid):
        """
        This method will remove node with ID node_id. The node and the relations to/from the node will also be deleted.
        Use 'remove_node' to remove nodes only when there should be no relations attached to it.
        :param nid: nid of the node
        :return: True if node is deleted, False otherwise
        """
        logging.debug("Trying to remove node with nid {nid}".format(nid=nid))
        query = "MATCH (n) WHERE n.nid={nid} DETACH DELETE n"
        self.graph.run(query, nid=nid)
        return True

    def remove_relation(self, start_nid=None, end_nid=None, rel_type=None):
        """
        This method will remove the relation rel_type between Node with nid start_nid and Node with nid end_nid.
        Relation is of type rel_type.
        :param start_nid: Node nid of the start node.
        :param end_nid: Node nid of the end node.
        :param rel_type: Type of the relation
        :return:
        """
        query = """
            MATCH (start_node)-[rel_type:{rel_type}]->(end_node)
            WHERE start_node.nid='{start_nid}'
              AND end_node.nid='{end_nid}'
            DELETE rel_type
        """.format(rel_type=rel_type, start_nid=start_nid, end_nid=end_nid)
        logging.debug("Remove Relation: {q}".format(q=query))
        self.graph.run(query)
        return
