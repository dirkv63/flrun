"""
This module is a wrapper for py2neo functions.
"""
import logging
import sys
from lib import neostore

from py2neo import Graph, Node, batch, Relationship
from py2neo.ext.calendar import GregorianCalendar


def get_start_node(end_node_id=None, rel_type=None):
    """
    This method will calculate the start node from an end Node ID and a relation type. If relation type is not specified
    then any relation type will do.
    The purpose of the function is to find a single start node. If there are multiple start nodes, then a random one
    is returned and an error message will be displayed.
    :param end_node_id: Node ID of the end node. This needs to be an integer.
    :param rel_type: Relation type
    :return: Node ID (integer) of the start Node, or False.
    """
    logging.debug("Find Start Node. End Node ID: {node_id}, Relation Type: {rel_type}"
                  .format(node_id=end_node_id, rel_type=rel_type))
    # First get Node from end node ID
    end_node = graph.node(end_node_id)
    if end_node.exists:
        # Then get relation to end node.
        try:
            rel = next(item for item in graph.match(end_node=end_node, rel_type=rel_type))
        except StopIteration:
            logging.warning("No start node found for end node ID {nid} and relation {rel}"
                            .format(nid=end_node_id, rel=rel_type))
        else:
            # Check if there are more elements in the iterator.
            if len([item for item in graph.match(end_node=end_node, rel_type=rel_type)]) > 1:
                logging.warning("More than one start node found for end node ID {nid} and relation {rel},"
                                " returning first".format(nid=end_node_id, rel=rel_type))
            start_node_id = node_id(rel.start_node)
            return start_node_id
    else:
        logging.error("Non-existing end node ID: {end_node_id}".format(end_node_id=end_node_id))
        return False


def get_start_nodes(end_node_id=None, rel_type=None):
    """
    This method will calculate all start nodes from an end Node ID and a relation type. If relation type is not
    specified then any relation type will do.
    The purpose of the function is to find all start nodes.
    :param end_node_id: Node ID of the end node. This needs to be an integer.
    :param rel_type: Relation type
    :return: List with Node IDs (integers) of the start Node, or False.
    """
    logging.debug("Find Start Nodes. End Node ID: {node_id}, Relation Type: {rel_type}"
                  .format(node_id=end_node_id, rel_type=rel_type))
    # First get Node from end node ID
    end_node = graph.node(end_node_id)
    if end_node.exists:
        # Then get relation to end node.
        node_list = [node_id(rel.start_node) for rel in graph.match(end_node=end_node, rel_type=rel_type)]
        return node_list
    else:
        logging.error("Non-existing end node ID: {end_node_id}".format(end_node_id=end_node_id))
        return False


def get_end_node(start_node_id=None, rel_type=None):
    """
    This method will calculate the end node from an start Node ID and a relation type. If relation type is not specified
    then any relation type will do.
    The purpose of the function is to find a single end node. If there are multiple end nodes, then a random one
    is returned and an error message will be displayed.
    :param start_node_id: Node ID of the start node. This needs to be an integer.
    :param rel_type: Relation type
    :return: Node ID (integer) of the end Node, or False.
    """
    logging.debug("Find End Node. Start node ID: {node_id}, Relation Type: {rel_type}"
                  .format(node_id=start_node_id, rel_type=rel_type))
    # First get Node from end node ID
    start_node = graph.node(start_node_id)
    if start_node.exists:
        # Then get relation to end node.
        try:
            rel = next(item for item in graph.match(start_node=start_node, rel_type=rel_type))
        except StopIteration:
            logging.warning("No end node found for start node ID {nid} and relation {rel}"
                            .format(nid=start_node_id, rel=rel_type))
        else:
            # Check if there are more elements in the iterator.
            if len([item for item in graph.match(start_node=start_node, rel_type=rel_type)]) > 1:
                logging.warning("More than one end node found for start node ID {nid} and relation {rel},"
                                " returning first".format(nid=start_node_id, rel=rel_type))
            end_node_id = node_id(rel.end_node)
            return end_node_id
    else:
        logging.error("Non-existing start node ID: {start_node_id}".format(start_node_id=start_node_id))
        return False


def get_end_nodes(start_node_id=None, rel_type=None):
    """
    This method will calculate all end nodes from a start Node ID and a relation type. If relation type is not
    specified then any relation type will do.
    The purpose of the function is to find all end nodes.
    :param start_node_id: Node ID of the start node. This needs to be an integer.
    :param rel_type: Relation type
    :return: List with Node IDs (integers) of the end Nodes, or False.
    """
    logging.debug("Find End Nodes. Start Node ID: {node_id}, Relation Type: {rel_type}"
                  .format(node_id=start_node_id, rel_type=rel_type))
    # First get Node from end node ID
    start_node = graph.node(start_node_id)
    if start_node.exists:
        # Then get relation to end node.
        node_list = [node_id(rel.end_node) for rel in graph.match(start_node=start_node, rel_type=rel_type)]
        return node_list
    else:
        logging.error("Non-existing start node ID: {start_node_id}".format(start_node_id=start_node_id))
        return False


def relations(nid):
    """
    This method will check if node with ID has relations. Returns True if there are relations, returns False otherwise.
    :param nid: ID of the object to check relations
    :return: Number of relations - if there are relations, False - there are no relations.
    """
    logging.debug("In method relations for id {node_id}".format(node_id=nid))
    obj_node = graph.node(nid)
    if obj_node.exists:
        if obj_node.degree:
            logging.debug("Relations found")
            return obj_node.degree
        else:
            logging.debug("No Relations found")
    else:
        logging.error("ID {id} cannot be bound to a node".format(id=nid))
    return False


def clear_locations():
    """
    This method will check if there are orphan locations. These are locations without relations. These locations can be
    removed.
    :return:
    """
    # Note that you could DETACH DELETE location nodes here, but then you miss the opportunity to log what is removed.
    query = """
        MATCH (loc:Location) WHERE NOT (loc)--() RETURN id(loc) as loc_id, loc.city as city
    """
    res = graph.cypher.execute(query)
    for locs in res:
        logging.info("Remove location {city} with ID {loc_id}".format(city=locs.city, loc_id=locs.loc_id))
        remove_node(locs.loc_id)
    return


def remove_date(ds):
    """
    This method will verify if a date can be removed. Day must have more than only 'DAY' relation, Month should have
    more than only "MONTH" relation and Year should have more than only incoming "YEAR" relation.
    You need to find all nodes (day, month, year) before attempting to remove them. calender.date function will create
    them in all cases. Compare with method clear_date(), that will scan the database and remove all days, months and
    years that are no longer used.
    :param ds: Datestamp of the Date (YYYY-MM-DD, as provided by Day.Key)
    :return:
    """
    day_node = calendar.date(ds.year, ds.month, ds.day).day
    day_node_id = node_id(day_node)
    month_node = calendar.date(ds.year, ds.month, ds.day).month
    month_node_id = node_id(month_node)
    year_node = calendar.date(ds.year, ds.month, ds.day).year
    year_node_id = node_id(year_node)
    if relations(day_node_id) == 1:
        remove_node_force(day_node_id)
        if relations(month_node_id) == 1:
            remove_node_force(month_node_id)
            if relations(year_node_id) == 1:
                remove_node_force(year_node_id)
    return


def remove_node(nid):
    """
    This method will remove node with ID node_id. Nodes can be removed only if there are no relations attached to the
    node.
    :param nid:
    :return: True if node is deleted, False otherwise
    """
    if relations(nid):
        logging.error("Request to delete node ID {node_id}, but relations found. Node not deleted"
                      .format(node_id=nid))
        return False
    else:
        query = "MATCH (n) WHERE id(n)={node_id} DELETE n"
        graph.cypher.execute(query.format(node_id=nid))
        return True


def remove_relation(start_nid, end_nid, rel_type):
    """
    This method will remove the relation rel_type between Node with ID start_nid and Node with ID end_id. Relation is
    of type rel_type.
    :param start_nid: Node ID of the start node.
    :param end_nid: Node ID of the end node.
    :param rel_type: Type of the relation
    :return:
    """
    query = """
        MATCH (start_node)-[rel_type:{rel_type}]->(end_node)
        WHERE id(start_node)={start_nid}
          AND id(end_node)={end_nid}
        DELETE rel_type
    """.format(rel_type=rel_type, start_nid=start_nid, end_nid=end_nid)
    logging.debug("Remove query looks like: {query}".format(query=query))
    graph.cypher.execute(query)
    return


def create_relation(start_node=None, end_node=None, rel_type=None):
    """
    This method will create the relation rel_type between Start Node and End Node. Relation is of type rel_type.
    :param start_node: Start node.
    :param end_node: End Node.
    :param rel_type: Type of the relation
    :return:
    """
    logging.debug("Creating relation from start {sn} to end {en} relation type {rt}"
                  .format(sn=start_node, en=end_node, rt=rel_type))
    graph.create(Relationship(start_node, rel_type, end_node))
    return
