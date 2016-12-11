"""
Temporary script to add 'MF' Nodes and replace all 'mf' attributes with Relations.
Note: manually run the command 'match (n:Person) remove n.mf return n' to remove 'mf' attribtue.
"""

from competition import neostore
from lib import my_env

if __name__ == "__main__":
    my_env.init_loghandler(__file__, "c:\\temp\\log", "info")
    ns = neostore.NeoStore()
    label = "MF"
    props = dict(name="Dames")
    dames = ns.create_node(label, **props)
    props["name"] = "Heren"
    heren = ns.create_node(label, **props)
    label = "Person"
    props = dict(mf="vrouw")
    nodes = ns.get_nodes(label, **props)
    for node in nodes:
        ns.create_relation(node, "mf", dames)
    props = dict(mf="man")
    nodes = ns.get_nodes(label, **props)
    for node in nodes:
        ns.create_relation(node, "mf", heren)
