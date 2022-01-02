from pymongo import MongoClient 
 
# Okteto deployment MongoClient
client = MongoClient("mongodb://mongodb:27017")
# Local MongoClient
# client = MongoClient("mongodb://localhost:27017")

database = client.pfgl

rosters_collection = database.get_collection('rosters')
current_scores_collection = database.get_collection('current_scores')

def get_roster_by_manager(manager_name: str):
    roster = rosters_collection.find_one({"manager": manager_name})
    if roster:
        return parse_roster_data(roster)
    
def parse_roster_data(roster):
    return {
        # parse mongo internal ObjectId
        "id": str(roster["_id"]),
        "manager": roster["manager"],
        "players": roster["players"]
    }