"""
sat_rels: Stand-Alone Test - Relations
Script that will run in stand-alone mode and allows to test specific functionality.
"""
import competition.models_graph as mg
from py2neo import Path

node_id = 101
node_stan = mg.graph.node(node_id)
if node_stan.degree:
    print("There are relations!")
else:
    print("There are no relations!")

