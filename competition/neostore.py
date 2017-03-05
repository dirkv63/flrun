"""
This class consolidates functions related to the neo4J datastore.
"""

import logging
import os
import sys
import uuid
from datetime import datetime, date
from pandas import DataFrame
from py2neo import Graph, Node, Relationship, NodeSelector
from py2neo.database import DBMS
from py2neo.ext.calendar import GregorianCalendar
# from py2neo import watch


# watch("neo4j.http")


class NeoStore:

    def __init__(self):
        """
        Method to instantiate the class in an object for the neostore.
        @return: Object to handle neostore commands.
        """
        self.graph = self.connect2db()
        # self.graph = self.connect2graphene()
        self.calendar = GregorianCalendar(self.graph)
        self.selector = NodeSelector(self.graph)
        return

    @staticmethod
    def connect2db():
        """
        Internal method to create a database connection. This method is called during object initialization.
        @return: Database handle and cursor for the database.
        """
        neo4j_params = {
            'user': "neo4j",
            'password': "_m8z8IpJUPyR",
            'db': "stratenloop17.db"
        }
        neo4j_config = {
            'user': neo4j_params['user'],
            'password': neo4j_params["password"],
        }
        # Connect to Graph
        graph = Graph(**neo4j_config)
        # Check that we are connected to the expected Neo4J Store - to avoid accidents...
        dbname = DBMS().database_name
        if dbname != neo4j_params['db']:    # pragma: no cover
            logging.fatal("Connected to Neo4J database {d}, but expected to be connected to {n}"
                          .format(d=dbname, n=neo4j_params['db']))
            sys.exit(1)
        return graph

    @staticmethod
    def connect2graphene():
        graphenedb_url = os.environ.get("GRAPHENEDB_URL")
        graph = Graph(graphenedb_url, bolt=False)
        return graph

    def clear_locations(self):
        """
        This method will check if there are orphan locations. These are locations without relations. These locations
        can be removed.
        @return:
        """
        # Note that you could DETACH DELETE location nodes here, but then you miss the opportunity to log what is
        # removed.
        query = """
            MATCH (loc:Location) WHERE NOT (loc)--() RETURN loc.nid as loc_nid, loc.city as city
        """
        res = self.graph.run(query).data()
        for locs in res:
            logging.info("Remove location {city} with nid {loc_nid}".format(city=locs['city'], loc_nid=locs['loc_nid']))
            self.remove_node(locs['loc_nid'])
        return

    def create_node(self, *labels, **props):
        """
        Function to create node. The function will return the node object.
        Note that a 'nid' attribute will be added to the node. This is a UUID4 unique identifier. This is a temporary
        solution cause there seems to be no other way to extract the node ID from a node.
        :param labels: Labels for the node
        :param props: Value dictionary with values for the node.
        :return: Node that has been created.
        """
        props['nid'] = str(uuid.uuid4())
        component = Node(*labels, **props)
        self.graph.create(component)
        return component

    def create_node_no_nid(self, *labels, **props):     # pragma: no cover
        """
        Function to create node. The function will return the node object.
        Note that in this case a 'nid' attribute will not be added to the node. This is for restoring a previous dump
        of this database.
        @param labels: Labels for the node
        @param props: Value dictionary with values for the node.
        @return: Node that has been created.
        """
        component = Node(*labels, **props)
        self.graph.create(component)
        return component

    def create_relation(self, from_node=None, rel=None, to_node=None):
        """
        Function to create relationship between nodes.
        @param from_node: Start node for the relation
        @param rel: Relation type
        @param to_node: End node for the relation
        @return:
        """
        rel = Relationship(from_node, rel, to_node)
        self.graph.merge(rel)
        return

    def clear_date_node(self, label):
        """
        This method will clear every date node as specified by label. Label can be Day, Month or Year. The node will be
        deleted if not used anymore. So it can have only one incoming relation: DAY - MONTH or YEAR.
        Therefore find all relations. If there is only one, then the date node can be deleted.
        @param label: Day, Month or Year
        @return:
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
        @return:
        """
        # First Remove Days
        self.clear_date_node("Day")
        self.clear_date_node("Month")
        self.clear_date_node("Year")
        return

    def clear_store(self):      # pragma: no cover
        """
        This method will remove all nodes and relations in a datastore. It should be used during tests only.
        :return:
        """
        query = "MATCH (n) DETACH DELETE n"
        self.graph.run(query)
        return

    def date_node(self, ds):
        """
        This method will get a datetime.date timestamp and return the associated node. The calendar module will
        ensure that the node is created if required.
        @param ds: datetime.date representation of the date, or Calendar key 'YYYY-MM-DD'.
        @return: node associated with the date, of False (ds could not be formatted as a date object).
        """
        # If date format is string, convert to datetime object
        if isinstance(ds, str):
            try:
                ds = datetime.strptime(ds, '%Y-%m-%d').date()
            except ValueError:
                return False
        if isinstance(ds, date):
            date_node = self.calendar.date(ds.year, ds.month, ds.day).day   # Get Date (day) node
            # Check if a new node has been created and nid is set
            self.get_nodes_no_nid()
            return date_node
        else:
            return False

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
        # First get Node from end node ID
        start_node = self.node(start_node_id)
        if start_node:
            # Then get relation to end node.
            try:
                rel = next(item for item in self.graph.match(start_node=start_node, rel_type=rel_type))
            except StopIteration:
                logging.warning("No end node found for start node ID: {nid} and relation: {rel}"
                                .format(nid=start_node_id, rel=rel_type))
                return False
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

    def get_cat4part(self, part_nid):
        """
        This method will return category for the participant. Category will be 'Dames' or 'Heren'.
        @param part_nid: Nid of the participant node.
        @return: Category (Dames or Heren), or False if no category could be found.
        """
        query = "MATCH (n:Participant {nid:{p}})<-[:is]-()-[:mf]->(c:MF) RETURN c.name as name"
        res = self.graph.run(query, p=part_nid)
        try:
            rec = res.next()
        except StopIteration:
            return False
        return rec["name"]

    def get_end_nodes(self, start_node_id=None, rel_type=None):
        """
        This method will calculate all end nodes from a start Node ID and a relation type. If relation type is not
        specified then any relation type will do.
        The purpose of the function is to find all end nodes.
        @param start_node_id: Node ID of the start node.
        @param rel_type: Relation type
        @return: List with Node IDs (integers) of the end Nodes, or False.
        """
        # First get Node from end node ID
        start_node = self.node(start_node_id)
        if start_node:
            # Then get relation to end node.
            node_list = [self.node_id(rel.end_node())
                         for rel in self.graph.match(start_node=start_node, rel_type=rel_type)]
            # Convert to set to remove duplicates
            node_set = set(node_list)
            # Then return the list
            return list(node_set)
        else:
            logging.error("Non-existing start node ID: {start_node_id}".format(start_node_id=start_node_id))
            return False

    def get_main_race_id(self, race_id):
        """
        This function will find the main race associated with a race_id. Race_id needs to be the nid of a
        'Bijwedstrijd'. There is no verification if nid is from race_id, type Bijwedstrijd.
        @param race_id: nid of the Bijwedstrijd
        @return: nid of the Hoofdwedstrijd.
        """
        query = """
            MATCH (n:Race {nid:{race_nid}})<-[:has]-(:Organization)-[:has]->(r:Race),
                  (r)-[:type]->(t:RaceType {name:'Hoofdwedstrijd'})
            RETURN r.nid as nid
            """
        res = self.graph.run(query, race_nid=race_id)
        try:
            rec = res.next()
        except StopIteration:
            return False
        return rec["nid"]

    def get_nr_participants(self, race_id, cat):
        """
        This function will calculate the number of participants of category cat in race with nid race_id. It is used
        to calculate points for participants in 'Bijwedstrijd'.
        :param race_id: nid of the race
        :param cat: Category name
        :return: Number of participants. 0 is a valid response.
        """
        query = """
            MATCH (n:Race {nid:{race_nid}})<-[:participates]-(:Participant)<-[:is]-(p:Person),
                  (p)-[:mf]->(c:MF {name:{cat}})
            RETURN count(p) as cnt
        """
        res = self.graph.run(query, race_nid=race_id, cat=cat)
        try:
            rec = res.next()
        except StopIteration:
            return False
        return rec["cnt"]

    def get_node(self, *labels, **props):
        """
        This method will select a single (or first) node that have labels and properties
        @param labels:
        @param props:
        @return: node that fulfills the criteria
        """
        nodes = self.get_nodes(*labels, **props)
        if not nodes:
            logging.info("Expected 1 node for label {l} and props {p}, found none.".format(l=labels, p=props))
            return False
        elif len(nodes) > 1:
            logging.error("Expected 1 node for label {l} and props {p}, found many {m}."
                          .format(l=labels, p=props, m=len(nodes)))
        return nodes[0]

    def get_nodes(self, *labels, **props):
        """
        This method will select all nodes that have labels and properties
        @param labels:
        @param props:
        @return: list of nodes that fulfill the criteria
        """
        nodes = self.selector.select(*labels, **props)
        return list(nodes)

    def get_nodes_no_nid(self):
        """
        This method will select all nodes that have no nid. These should be limited to Calendar nodes. A nid will be
        added since this is used as unique reference for the node in relations
        @return: count of number of nodes that have been updated.
        """
        query = "MATCH (n) WHERE NOT EXISTS (n.nid) RETURN id(n) as node_id"
        res = self.graph.run(query)
        cnt = 0
        for rec in res:
            self.set_node_nid(node_id=rec["node_id"])
            cnt += 1
        return cnt

    def get_organization(self, **org_dict):
        """
        This method searches for the organization based on organization name, location and datestamp. If found,
        then organization attributes will be set using method set_organization. If not found, 'False' will be returned.
        @param org_dict: New set of properties for the node. These properties are: name, location, datestamp and
         org_type. Datestamp needs to be in format 'YYYY-MM-DD', this is the key for date as generated by the calendar
         method.
        @return: True if organization is found, False otherwise.
        """
        query = """
        MATCH (day:Day {key: {datestamp}})<-[:On]-(org:Organization {name: {name}}),
              (org)-[:In]->(loc:Location {city: {location}})
        RETURN org
        """
        if not isinstance(org_dict["datestamp"], str):
            org_dict["datestamp"] = org_dict["datestamp"].strftime("%Y-%m-%d")
        cursor = self.graph.run(query, name=org_dict["name"], location=org_dict["location"],
                                datestamp=org_dict["datestamp"])
        org_list = nodelist_from_cursor(cursor)
        if len(org_list) == 0:
            # No organization found on this date for this location
            return False
        elif len(org_list) == 1:
            # Organization node found, return ID of the organization node
            org_node = org_list.pop()
            return org_node["nid"]
        else:
            tot_len = len(org_list)
            logging.error("Expected to find 0 or 1 organization, found {tot_len} (Organization: {name}, "
                          "Location: {loc}, Date: {date}"
                          .format(tot_len=tot_len, name=org_dict["name"], loc=org_dict["location"],
                                  date=org_dict["datestamp"]))
            return False

    def get_organization_from_id(self, org_id):
        """
        This method will get an organization ID and search for the organization details.
        @param org_id: nid of the organization Node.
        @return: Dictionary with organization details: date, day, month, year, org (organization label) and city
        """
        query = """
            MATCH (date:Day)<-[:On]-(org:Organization)-[:In]->(loc:Location)
            WHERE org.nid = '{org_id}'
            RETURN date.day as day, date.month as month, date.year as year, date.key as date,
                   org.name as org, loc.city as city
        """.format(org_id=org_id)
        org_array = DataFrame(self.graph.run(query).data())
        df_length = org_array.index
        if len(df_length) == 0:
            logging.error("No organization found for nid {nid}".format(nid=org_id))
            return False
        elif len(org_array) > 1:
            logging.error("Multiple organizations found for nid {nid}, using first one.".format(nid=org_id))
        org_row = org_array.iloc[0].to_dict()
        return org_row

    def get_organization_list(self):
        """
        This method will get a list of all organizations. Each item in the list is a dictionary with fields date,
        organization, city, id (for organization nid) and type.

        :return:
        """
        query = """
            MATCH (day:Day)<-[:On]-(org:Organization)-[:In]->(loc:Location),
                  (org)-[:type]->(ot:OrgType)
            RETURN day.key as date, org.name as organization, loc.city as city, org.nid as id, ot.name as type
            ORDER BY day.key ASC
        """
        res = self.graph.run(query).data()
        # Convert date key from YYYY-MM-DD to DD-MM-YYYY
        for rec in res:
            rec["date"] = datetime.strptime(rec["date"], "%Y-%m-%d").strftime("%d-%m-%Y")
        return res

    def get_participant_in_race(self, pers_id=None, race_id=None):
        """
        This function will for a person get the participant node in a race, or False if the person did not
        participate in the race according to current information in the database.
        @param pers_id:
        @param race_id:
        @return: participant node, or False
        """
        query = """
            MATCH (pers:Person)-[:is]->(part:Participant)-[:participates]->(race:Race)
            WHERE pers.nid='{pers_id}' AND race.nid='{race_id}'
            RETURN part
        """.format(pers_id=pers_id, race_id=race_id)
        res = self.graph.run(query)
        nodes = nodelist_from_cursor(res)
        if len(nodes) > 1:
            logging.error("More than one ({nr}) Participant node for Person {pnid} and Race {rnid}"
                          .format(pnid=pers_id, rnid=race_id, nr=len(nodes)))
        elif len(nodes) == 0:
            return False
        return nodes[0]

    def get_participant_seq_list(self, race_id):
        """
        This method will return a list of participant nodes in sequence of arrival for a particular race.
        @param race_id:
        @return: Node list
        """
        query = """
            MATCH race_ptn = (race)<-[:participates]-(participant),
                  participants = (participant)<-[:after*0..]-()
            WHERE race.nid = '{race_id}'
            WITH COLLECT(participants) AS results, MAX(length(participants)) AS maxLength
            WITH FILTER(result IN results WHERE length(result) = maxLength) AS result_coll
            UNWIND result_coll as result
            RETURN nodes(result)
        """.format(race_id=race_id)
        # Get the result of the query in a recordlist
        cursor = self.graph.run(query)
        try:
            rec = cursor.next()
        except StopIteration:
            return False
        return rec["nodes(result)"]

    def points_per_category(self, cat):
        """
        This query will for the specified category collect every participation and points that go with the participation
        for every person in the category.
        :param cat:
        :return: A cursor with records having the name, nid and points for each participation on every race.
        """
        query = "match (c:MF {name:{cat}})<-[:mf]-(n:Person)-[:is]->(p) " \
                "return n.name as name, n.nid as nid, p.points as points"
        res = self.graph.run(query, cat=cat)
        return res

    def get_race_in_org(self, org_id, racetype_id, name):
        """
        This function will find a race of a specific type in an organization. It will return the race attributes if a
        race has been found, false otherwise.

        :param org_id: nid of the Organization node.

        :param racetype_id: nid of the RaceType node.

        :param name: label (name) of the race (e.g. 10 km).

        :return: tuple with race nid and organization name, or False if race not found.
        """
        query = """
        MATCH (org:Organization)-->(race:Race)-->(racetype:RaceType)
        WHERE org.nid='{org_id}'
          AND racetype.nid='{racetype}'
          AND race.name='{name}'
        RETURN race.nid as race_nid, org.name as org_name
        """.format(org_id=org_id, racetype=racetype_id, name=name)
        race_cursor = self.graph.run(query)
        try:
            race_data = next(race_cursor)
        except StopIteration:
            return False
        else:
            return race_data["race_nid"], race_data["org_name"]

    def get_race_label(self, race_id):
        """
        This method will return the dictionary that allows to create the race label.
        @param race_id: nid of the race.
        @return: Dictionary with the Race information. Fields: race, org, city, day, month, year.
        """
        query = """
            MATCH (race:Race)<-[:has]-(org)-[:On]->(date),
                  (org)-[:In]->(loc),
                  (type:RaceType)<-[:type]-(race)
            WHERE race.nid='{race_id}'
            RETURN race.name as race, org.name as org, loc.city as city, date.day as day,
                   date.month as month, date.year as year, type.name as type
        """.format(race_id=race_id)
        recordlist = self.graph.run(query).data()
        if len(recordlist) == 0:
            logging.error("Expected to find a Race Label, but no match... ({nid})".format(nid=race_id))
            return False
        elif len(recordlist) > 1:
            logging.error("Found multiple races for Race ID {nid}".format(nid=race_id))
        return recordlist[0]

    def get_race_list(self, org_id):
        """
        This function will get an organization nid and return the Races associated with the Organization.
        The races will be returned as a list of dictionaries with fields race (racename), type (racetype) and nid of the
        race.
        @param org_id: nid of the Organization.
        @return: List of dictionaries, or empty list which evaluates to False.
        """
        query = """
            MATCH (org:Organization)-[:has]->(race:Race)-[:type]->(racetype:RaceType)
            WHERE org.nid = '{org_id}'
            RETURN race.name as race, racetype.name as type, race.nid as race_id
            ORDER BY racetype.weight, race.name
        """.format(org_id=org_id)
        res = self.graph.run(query).data()
        return res

    def get_race4person(self, person_id):
        """
        This method will get a list of participant information for a  person, sorted on date. The information will be
        provided in a list of dictionaries. The dictionary values are the corresponding node dictionaries.

        :param person_id:

        :return: list of Participant (part),race, date, organization (org) and racetype Node dictionaries in date
        sequence.
        """
        race4person = []
        query = """
            MATCH (person:Person)-[:is]->(part:Participant)-[:participates]->(race:Race),
                  (race)<-[:has]-(org:Organization)-[:On]->(day:Day),
                  (race)-[:type]->(racetype:RaceType),
                  (org)-[:In]->(loc:Location)
            WHERE person.nid='{pers_id}'
            RETURN race, part, day, org, racetype, loc
            ORDER BY day.key ASC
        """.format(pers_id=person_id)
        cursor = self.graph.run(query)
        while cursor.forward():
            rec = cursor.current()
            res_dict = dict(part=dict(rec['part']),
                            race=dict(rec['race']),
                            date=dict(rec['day']),
                            org=dict(rec['org']),
                            racetype=dict(rec['racetype']),
                            loc=dict(rec['loc']))
            race4person.append(res_dict)
        return race4person

    def get_relations(self):
        """
        This method will return all relations in the database as a list of dictionaries with keys from_nid, rel, to_nid.
        @return: cursor with every possible relation. A cursor is an generator, so only a single pass in a for-loop is
         possible. Access the fields from_nid, rel and to_nid as dictionary items.
        """
        query = "match (n)-[r]->(m) return n.nid as from_nid, type(r) as rel, m.nid as to_nid"
        res = self.graph.run(query)
        return res

    def get_start_node(self, end_node_id=None, rel_type=None):
        """
        This method will calculate the start node from an end Node ID and a relation type. If relation type is not
        specified then any relation type will do.
        The purpose of the function is to find a single start node. If there are multiple start nodes, then a random
        one is returned and an error message will be displayed.
        @param end_node_id: Node nid of the end node.
        @param rel_type: Relation type
        @return: Node nid of the start Node, or False.
        """
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
        @param end_node_id: Node nid of the end node.
        @param rel_type: Relation type
        @return: List with Node IDs (integers) of the start Node, or False.
        """
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

    def get_wedstrijd_type(self, org_id, racetype):
        """
        This query will find if organization has races of type racetype. It will return the number of races (True)
        in case that there are races of type racetype, False otherwise
        @param org_id: NID of the organization
        @param racetype:
        @return: Number of races for this type (True), or False if no races.
        """
        query = """
        MATCH (org:Organization)-[:has]->(race:Race)-[:type]->(rt:RaceType)
        WHERE org.nid='{org_id}'
          AND rt.name='{racetype}'
        RETURN org, race, rt
        """.format(org_id=org_id, racetype=racetype)
        res = DataFrame(self.graph.run(query).data())
        if res.empty:
            return False
        else:
            return len(res.index)

    def init_graph(self):
        """
        This method will initialize the graph. It will set indices and create nodes required for the application
        (on condition that the nodes do not exist already).
        @return:
        """
        stmt = "CREATE CONSTRAINT ON (n:{0}) ASSERT n.{1} IS UNIQUE"
        self.graph.run(stmt.format('Location', 'city'))
        self.graph.run(stmt.format('Person', 'name'))
        self.graph.run(stmt.format('RaceType', 'name'))
        self.graph.run(stmt.format('OrgType', 'name'))
        nid_labels = ['Participant', 'Person', 'Race', 'Organization', 'Location', 'RaceType', 'OrgType']
        stmt = "CREATE CONSTRAINT ON (n:{nid_label}) ASSERT n.nid IS UNIQUE"
        for nid_label in nid_labels:
            self.graph.run(stmt.format(nid_label=nid_label))

        # RaceType
        """
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
        """
        return

    def node(self, nid):
        """
        This method will get a node ID and return a node, (or false in case no Node can be associated with the ID.
        The current release of py2neo 3.1.2 throws a IndexError in case a none-existing node ID is requested.)
        Note that since there seems to be no way to extract the Node ID of a node, the nid attribute is used. As a
        consequence, it is not possible to use the node(nid).
        @param nid: ID of the node to be found.
        @return: Node, or False (None) in case the node could not be found.
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

        @param node_obj: Node object
        @return: ID of the node (integer), or False.
        """
        # First check if my object is a node (not sure it is a node, but I am sure it is a sub-graph)
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
        @param nid: nid of the node required
        @return: Dictionary of the node properties
        """
        my_node = self.node(nid)
        if my_node:
            return dict(my_node)
        else:
            logging.error("Could not bind ID {node_id} to a node.".format(node_id=nid))
            return False

    def node_update(self, **properties):
        """
        This method will update the node's properties with the properties specified. Modified properties will be
        updated, new properties will be added and removed properties will be deleted.
        nid needs to be part of the properties dictionary.
        @param properties: Dictionary of the property set for the node. 'nid' property is mandatory.
        @return: True if successful update, False otherwise.
        """
        try:
            my_node = self.node(properties["nid"])
        except KeyError:
            logging.error("Attribute 'nid' missing, required in dictionary.")
            return False
        if my_node:
            curr_props = self.node_props(properties["nid"])
            # Remove properties
            remove_props = [prop for prop in curr_props if prop not in properties]
            for prop in remove_props:
                # Set value to None to remove a key.
                del my_node[prop]
            # Modify properties and add new properties
            # So I'm sure that nid is still in the property dictionary
            for prop in properties:
                my_node[prop] = properties[prop]
            # Now push the changes to Neo4J database.
            self.graph.push(my_node)
            return True
        else:
            logging.error("No node found for NID {nid}".format(nid=properties["nid"]))
            return False

    def relations(self, nid):
        """
        This method will check if node with ID has relations. Returns True if there are relations, returns False
        otherwise. Do not use graph.degree, because there seems to be a strange error when running on graphenedb...
        :param nid: ID of the object to check relations
        :return: Number of relations - if there are relations, False - there are no relations.
        """
        # obj_node = self.node(nid)
        query = "MATCH (n)--(m) WHERE n.nid='{nid}' return m.nid as m_nid".format(nid=nid)
        res = self.graph.run(query).data()  # This will return the list of dictionaries with results.
        if len(res):
            return len(res)
        else:
            return False

    def remove_node(self, nid):
        """
        This method will remove node with ID node_id. Nodes can be removed only if there are no relations attached to
        the node.
        @param nid:
        @return: True if node is deleted, False otherwise
        """
        obj_node = self.node(nid)
        if not obj_node:
            return False
        elif self.relations(nid):
            logging.error("Request to delete node nid {node_id}, but relations found. Node not deleted"
                          .format(node_id=nid))
            return False
        else:
            query = "MATCH (n) WHERE n.nid='{nid}' DELETE n".format(nid=nid)
            self.graph.run(query)
            return True

    def remove_node_force(self, nid):
        """
        This method will remove node with ID node_id. The node and the relations to/from the node will also be deleted.
        Use 'remove_node' to remove nodes only when there should be no relations attached to it.
        @param nid: nid of the node
        @return: True if node is deleted, False otherwise
        """
        query = "MATCH (n) WHERE n.nid='{nid}' DETACH DELETE n".format(nid=nid)
        self.graph.run(query)
        return True

    def remove_relation(self, start_nid=None, end_nid=None, rel_type=None):
        """
        This method will remove the relation rel_type between Node with nid start_nid and Node with nid end_nid.
        Relation is of type rel_type.
        @param start_nid: Node nid of the start node.
        @param end_nid: Node nid of the end node.
        @param rel_type: Type of the relation
        @return:
        """
        query = """
            MATCH (start_node)-[rel_type:{rel_type}]->(end_node)
            WHERE start_node.nid='{start_nid}'
              AND end_node.nid='{end_nid}'
            DELETE rel_type
        """.format(rel_type=rel_type, start_nid=start_nid, end_nid=end_nid)
        self.graph.run(query)
        return

    def set_node_nid(self, node_id):
        """
        This method will set a nid for node with node_id. This should be done only for calendar functions.
        :param node_id: Neo4J ID of the node
        :return: nothing, nid should be set.
        """
        query = "MATCH (n) WHERE id(n)={node_id} SET n.nid='{nid}' RETURN n.nid"
        self.graph.run(query.format(node_id=node_id, nid=str(uuid.uuid4())))
        return


def nodelist_from_cursor(cursor):
    """
    The py2neo Cursor will return a result list that is not necessarily unique. This function gets a cursor from
    a query where the cypher return argument is a single node. The function will return the list of unique nodes.
    @param cursor:
    @return: list of unique nodes, or empty list if there are no nodes.
    """
    node_list = set()
    while cursor.forward():
        current = cursor.current()
        (node, ) = current.values()
        node_list.add(node)
    return list(node_list)


def validate_node(node, label):
    """
    BE CAREFUL: has_label does not always work for unknown reason.
    This function will check if a node is of a specific type, so it will check if the node has the label.
    @param node: Node to check
    @param label: Label that needs to be in the node.
    @return: True, if label is in the node. False for all other reasons (e.g. node is not a node.
    """
    if type(node) is Node:
        return node.has_label(label)
    else:
        return False
