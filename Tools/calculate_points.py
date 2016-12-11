"""
Temporary script to calculate points for the participants in races.
"""

from competition import neostore, models_graph as mg
from lib import my_env

if __name__ == "__main__":
    my_env.init_loghandler(__file__, "c:\\temp\\log", "info")
    ns = neostore.NeoStore()
    # First get all 'Hoofdwedstrijden'
    props = {
            "name": 'Hoofdwedstrijd'
        }
    racetype_node = ns.get_node("RaceType", **props)
    racetype_nid = racetype_node["nid"]
    races = ns.get_start_nodes(end_node_id=racetype_nid, rel_type="type")
    for race_nid in races:
        mg.points_hoofdwedstrijd(race_nid)
    props["name"] = "Bijwedstrijd"
    racetype_node = ns.get_node("RaceType", **props)
    racetype_nid = racetype_node["nid"]
    races = ns.get_start_nodes(end_node_id=racetype_nid, rel_type="type")
    for race_nid in races:
        mg.points_bijwedstrijd(race_nid)
    props["name"] = "Deelname"
    racetype_node = ns.get_node("RaceType", **props)
    racetype_nid = racetype_node["nid"]
    races = ns.get_start_nodes(end_node_id=racetype_nid, rel_type="type")
    for race_nid in races:
        mg.points_deelname(race_nid)
