"""
Temporary script to simulate the issue with removing an organization.
"""

import logging
# from lib import my_env
from py2neo import Graph, watch
from py2neo.ext.calendar import GregorianCalendar

watch("neo4j.http")
watch("neo4j.bolt")

def connect2db():
    # graphenedb_url = os.environ.get("GRAPHENEDB_BOLT_URL")
    graphenedb_url = "bolt://hobby-dijdihliojekgbkedhfallol.dbs.graphenedb.com:24786"
    # graphenedb_user = os.environ.get("GRAPHENEDB_BOLT_USER")
    graphenedb_user = "app60885199-gphiRm"
    # graphenedb_pass = os.environ.get("GRAPHENEDB_BOLT_PASSWORD")
    graphenedb_pass = "0Y5Up4HMgKGNRP5ImVdw"
    host = "hobby-dijdihliojekgbkedhfallol.dbs.graphenedb.com"
    bolt_port = 24786
    http_port = 24789
    graph = Graph(graphenedb_url, host=host, user=graphenedb_user, password=graphenedb_pass, bolt=True, secure=False,
                  bolt_port=bolt_port, http_port=http_port)
    # logging.info("Connecting to URL {g}".format(g=graphenedb_url))
    return graph


if __name__ == "__main__":
    # my_env.init_loghandler(__file__, "c:\\temp\\log", "debug")
    g = connect2db()
    cal = GregorianCalendar(g)
