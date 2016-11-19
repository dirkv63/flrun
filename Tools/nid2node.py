"""
This script will find all Nodes in a graph and add a nid (uuid(4)) to it. The Neo4J unique identifier for nodes cannot
be used as the identifier will be reused when nodes are replaced. Also py2neo is not very good in supporting the Neo4J
unique identifier.
"""