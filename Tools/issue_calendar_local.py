"""
Script to simulate the issue with calendar.
"""

from py2neo import Graph, watch
from py2neo.ext.calendar import GregorianCalendar

watch("neo4j.bolt")
watch("neo4j.http")

def connect2db():
    user = "neo4j"
    passwd = "_m8z8IpJUPyR"
    # passwd = "localpwd"
    graph = Graph(user=user, password=passwd, bolt=True, secure=False)
    return graph


if __name__ == "__main__":
    g = connect2db()
    cal = GregorianCalendar(g)
