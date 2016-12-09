"""
This script will dump a Neo4J database to an sqlite database. The sqlite database has a components table, with all
components and every attribute for each component. The relations table shows all relations.
This script can be used as a backup-tool or to get a snapshot during tests.
In this script the nid is used as a unique reference.
"""

from competition import neostore
from lib import my_env, datastore

if __name__ == "__main__":
    my_env.init_loghandler(__file__, "c:\\temp\\log", "info")
    ns = neostore.NeoStore()
    dumpfile = "C:\\Development\\python\\FlaskRun\\neo_dump.sqlite3"
    ds = datastore.DataStore(dumpfile)
    ds.remove_tables()
    ds.create_tables()
    # First handle all nodes
    nodes = ns.get_nodes()
    all_attribs = []
    all_labels = []
    node_cnt = len(nodes)
    for node in nodes:
        # First get all attributes to create a component record.
        rec = {}
        for key in node.keys():
            rec[key] = node[key]
            if key not in all_attribs:
                all_attribs.append(key)
        # Load record in components table
        # Remove field "id" first, since this is not required.
        ds.insert_row("components", rec)
        # Then get all labels, add label and nid to labels table
        rec = {"nid": node["nid"]}
        labels = node.labels()
        for label in labels:
            rec["label"] = label
            if label not in all_labels:
                all_labels.append(label)
            # Load label record
            ds.insert_row("labels", rec)
    # Then handle all relations
    rec = {}
    fields = ["from_nid", "rel", "to_nid"]
    res = ns.get_relations()
    for line in res:
        for field in fields:
            rec[field] = line[field]
        ds.insert_row("relations", rec)
    ds.close_connection()
