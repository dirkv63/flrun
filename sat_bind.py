"""
sat_bind: Stand-Alone Test - bind
Script that will run in stand-alone mode and allows to test specific functionality.
"""
import competition.models_graph as mg

node_id = 25
loc_node = mg.graph.node(node_id)
if loc_node.exists:
    print("Node ID {node_id} exists".format(node_id=node_id))
else:
    print("Node ID {node_id} does not exist".format(node_id=node_id))
