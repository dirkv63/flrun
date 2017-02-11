"""
This script will restore a Neo4J database from a sqlite database. The sqlite database has a components table, with all
components and every attribute for each component. The relations table shows all relations.
This script can be used as a backup-tool or to get a snapshot during tests.
In this script the nid is used as a unique reference.
"""

from competition import neostore
from lib import my_env, datastore

if __name__ == "__main__":
    my_env.init_loghandler(__file__, "c:\\temp\\log", "info")
    ns = neostore.NeoStore()
    dumpfile = "C:\\Development\\python\\FlaskRun\\stratenloop15.sqlite3"
    ds = datastore.DataStore(dumpfile)
    ns.clear_store()
    # First handle all nodes
    # Get all Component rows
    rows = ds.get_records("components")
    key_list = ds.get_key_list("components")
    node_obj = {}
    node_info = my_env.LoopInfo("Nodes", 10)
    for row in rows:
        # Get node label
        node_label = ds.get_label(row["nid"])
        valuedict = {}
        for attrib in key_list:
            if row[attrib]:
                valuedict[attrib.lower()] = row[attrib]
        component = ns.create_node_no_nid(node_label, **valuedict)
        # Remember component for Relation in next step
        node_obj[row["nid"]] = component
        node_info.info_loop()
    node_info.end_loop()

    # Handle relations
    rows = ds.get_records("relations")
    rel_info = my_env.LoopInfo("Relations", 10)
    for row in rows:
        ns.create_relation(node_obj[row["from_nid"]], row["rel"], node_obj[row["to_nid"]])
        rel_info.info_loop()
    rel_info.end_loop()
    # logging.info('End Application')
