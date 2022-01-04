from pymongo import MongoClient
from decouple import config
from bson.json_util import dumps

mongo_connection_details = config("DB_HOST")

client = MongoClient(mongo_connection_details)

database = client.pfgl

teams_collection = database.get_collection('teams')
player_scores_collection = database.get_collection('player_scores')
tournament_collection = database.get_collection('tournaments')


def get_all_teams():
    """
    Return list of team objects or None if something goes terribly wrong
    """
    return teams_collection.find({}, {"_id": 0})

def get_team_by_manager(manager_name: str):
    """
    return roster object from db or None if manager_name does not exist
    """
    return teams_collection.find_one({"manager": manager_name}, {"_id": 0})
    


def get_team_starting_lineups() -> list:
    """
    Return list of teams with only starting players included
    """
    return teams_collection.aggregate(
        [{
            "$project": {
                "_id": 0,
                "manager": 1,
                "manager_name": 1,
                "team_name": 1,
                "roster": {
                    "$filter": {
                        "input": "$roster", 
                        "as": "player", 
                        "cond": {
                            "$eq": ["$$player.starter", True]
                        }
                    }
                }
            }
        }]
    )


def get_player_score_by_name(player_name: str, tourney_name: str) -> dict:
    return player_scores_collection.find_one({"player_name": player_name, "tournament_name": tourney_name}, {"_id": 0})
     
    

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



def get_tournament_name():
    tourney = tournament_collection.find_one({"active": True}, {"_id": 0})
    if tourney:
        return tourney["tournament_name"]

# def _parse_team_data(team) -> dict:
#     """
#     helper for rosters collection to parse internal mongo ObjectId
#     """
#     # roster is optional right now
#     roster = []
#     try:
#         roster = team["roster"]
#     except KeyError as e:
#         pass
    
#     return {
#         # parse mongo internal ObjectId
#         "id": str(team["_id"]),
#         "manager": team["manager"],
#         "manager_name": team["manager_name"],
#         "team_name": team["team_name"],
#         "roster": team["roster"]
#     }
    