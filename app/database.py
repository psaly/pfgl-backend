from pymongo import MongoClient
from bson import ObjectId
from decouple import config

connection_details = config("DB_HOST")
client = MongoClient(connection_details)
database = client.pfgl
rosters_collection = database.get_collection('rosters')

def get_roster_by_manager(manager_name: str):
    roster = rosters_collection.find_one({"manager": manager_name})
    if roster:
        return parse_roster_data(roster)
    
def parse_roster_data(roster):
    return {
        "id": str(roster["_id"]),
        "manager": roster["manager"],
        "players": roster["players"]
    }