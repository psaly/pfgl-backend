from pymongo import MongoClient
 
# Okteto deployment MongoClient
# client = MongoClient("mongodb://mongodb:27017")
# Local MongoClient
client = MongoClient("mongodb://localhost:27017")

database = client.pfgl

rosters_collection = database.get_collection('rosters')
player_scores_collection = database.get_collection('player_scores')

def get_roster_by_manager(manager_name: str):
    """
    return roster object from db or None if manager_name does not exist
    """
    roster = rosters_collection.find_one({"manager": manager_name})
    if roster:
        return _parse_roster_data(roster)
    

def insert_player_scores(player_scores: list[dict]) -> dict:
    """
    Insert player scores from live leaderboard scrape into player_scores collection.
    Return {"success": True/False, "errors_inserting": list of uninserted player_scores}
    """
    success_message = {"success": True, "errors_inserting": []}
    for score in player_scores:
        update_result = player_scores_collection.replace_one({"tournament_name": score["tournament_name"], "player_name": score["player_name"]}, score, upsert=True)
        if not update_result.acknowledged:
            success_message["success"] = False
            success_message["errors_inserting"].append(score)
    
    return success_message
    
    
# HELPER FUNCTIONS

def _parse_roster_data(roster) -> dict:
    """
    helper for rosters collection to parse internal mongo ObjectId
    """
    return {
        # parse mongo internal ObjectId
        "id": str(roster["_id"]),
        "manager": roster["manager"],
        "players": roster["players"]
    }
    