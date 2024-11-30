from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Ersetze die URL mit der deines MongoDB-Servers
mongo_uri = "mongodb://localhost:27017/"
client = MongoClient(mongo_uri)

try:
    # Überprüfe die Verbindung
    client.admin.command('ping')
    print("Verbindung zu MongoDB erfolgreich!")
except ConnectionFailure:
    print("Verbindung zu MongoDB fehlgeschlagen.")