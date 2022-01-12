from pymongo import MongoClient
from decouple import config
from bson.json_util import dumps

mongo_connection_details = config("DB_HOST")

client = MongoClient(mongo_connection_details)

database = client.pfgl

teams_collection = database.get_collection('teams')
player_scores_collection = database.get_collection('player_scores')
tournament_collection = database.get_collection('tournaments')
field_collection = database.get_collection('field')
matchup_collection = database.get_collection('matchups')

def get_matchups(segment: int, week: int) -> list[dict]:
    """
    segment 1-3
    week 0-8
    """
    matchups = []
    for matchup in matchup_collection.find({"segment": segment, "week": week}, {"_id": 0}):
        matchups.append(matchup)
    
    return matchups


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
    

# Players have optional {dg_name} attribute for matching with datagolf
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
                "logo_url": 1,
                "record": 1,
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
    success_message = {"success": True, "scores_successfully_inserted": 0, "errors_inserting": []}
    for score in player_scores:
        update_result = player_scores_collection.replace_one({"tournament_name": score["tournament_name"], "player_name": score["player_name"]}, score, upsert=True)
        if update_result.acknowledged:
            success_message["scores_successfully_inserted"] += 1
        else:
            success_message["success"] = False
            success_message["errors_inserting"].append(score)
    
    return success_message



def get_tournament_name() -> str:
    """
    Return name of current active tournament
    """
    tourney = tournament_collection.find_one({"active": True}, {"_id": 0})
    if tourney:
        return tourney["tournament_name"]


def get_tournament_details() -> dict:
    tourney = tournament_collection.find_one({"active": True}, {"_id": 0})
    if tourney:
        return tourney


def update_field_this_week(players: list[dict]) -> str:
    """
    Insert players from this week's field and activate current event
    """
    field_size = len(players)
    if field_size > 0:
        # PULL TOURNEY NAME FROM DG JSON (FOR NOW... ENDPOINT COULD BE GONE AT ANY TIME)
        tourney_name = players[0]["event_name"]
        # activate this event
        update_active_event(tourney_name)
        
        # wipe this week's field and re-insert
        field_collection.delete_many({"event_name": tourney_name})
        insert_result = field_collection.insert_many(players)
        return f"{tourney_name}: Field size {field_size}.\nSuccessfully inserted {len(insert_result.inserted_ids)} players."
    
    return "COULD NOT INSERT PLAYERS! DG API JSON WAS EMPTY!?!?!"

def update_active_event(tourney_name: str) -> dict:
    """
    Makes {tourney_name} the only current active event in the database
    """
    # deactivate current active event
    tournament_collection.update_many({"active": True}, {"$set": { "active": False}})
    # activate tourney_name event
    success = tournament_collection.update_one({"tournament_name": tourney_name}, {"$set": {"active": True}}, upsert=True)
    print(f"CURRENT ACTIVE TOURNAMENT UPDATE: {tourney_name}.")
    return success
    
    

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
    