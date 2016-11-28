"""
This script will stop the Neo4J server, remove current database stratenloop15.db, restore the original stratenloop15.db
and restart the server.
"""
import neokit
import shutil
import zipfile


orig_file = "C:\\neo4j_3_db\\databases\\stratenloop15.zip"
path2store = "C:\\neo4j_3_db\\databases"
path2remove = "C:\\neo4j_3_db\\databases\\stratenloop15.db"

home = "C:\\neo4j-community-3.0.4"
gs = neokit.GraphServer(home=home)
print("Stop Neo4J Server")
gs.stop()
shutil.rmtree(path2remove)
zip_obj = zipfile.ZipFile(orig_file)
zip_obj.extractall(path2store)
print("Start Neo4J Server")
gs.start()
print("Neo4J Server up and running")
