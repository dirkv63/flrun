"""
Temporary script to simulate the issue with removing an organization.
"""

import os, sys
(pp, cd) = os.path.split(os.getcwd())
sys.path.append(pp)

import logging
# from lib import my_env
from py2neo import Graph, watch
# from py2neo.ext.calendar import GregorianCalendar

watch("neo4j.http")
watch("neo4j.bolt")


def connect2db():
    logging.debug("In connect2db")
    # Heroku DB
    """
    graphenedb_url = "http://hobby-dijdihliojekgbkedhfallol.dbs.graphenedb.com:24786"
    graphenedb_user = "app60885199-gphiRm"
    graphenedb_pass = "0Y5Up4HMgKGNRP5ImVdw"
    host = "hobby-dijdihliojekgbkedhfallol.dbs.graphenedb.com"
    # OLSE DB
    """
    graphenedb_url = "http://hobby-oolcgnlnojekgbkeoiaeopol.dbs.graphenedb.com:24786"
    graphenedb_user = "olse"
    graphenedb_pass = "FVWA4dSmZRiiO35lYbq4"
    host = "hobby-oolcgnlnojekgbkeoiaeopol.dbs.graphenedb.com"
    http_port = 24789
    graph = Graph(graphenedb_url, host=host, user=graphenedb_user, password=graphenedb_pass, bolt=False, secure=False,
                  http_port=http_port)
    logging.debug("Connected to DB with object {g}".format(g=graph))
    # logging.info("Connecting to URL {g}".format(g=graphenedb_url))
    return graph


if __name__ == "__main__":
    # my_env.init_loghandler(__file__, "c:\\temp\\log", "debug")
    logging.debug("Connect to DB")
    g = connect2db()
    # logging.debug("Create Node")
    # g.run("CREATE (n:Person {name:'Bob'})")
    logging.debug("Try to get result")
    result = g.run("MATCH (n:Person) RETURN n")
    for record in result:
        print(record)
    # cal = GregorianCalendar(g)
