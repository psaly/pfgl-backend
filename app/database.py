from pymongo import MongoClient
from decouple import config

mongo_connection_details = config("DB_HOST")

client = MongoClient(mongo_connection_details)

database = client.pfgl

teams_collection = database.get_collection('teams')
kwp_teams_collection = database.get_collection('kwpteams')
player_scores_collection = database.get_collection('player_scores')
tournament_collection = database.get_collection('tournaments')
field_collection = database.get_collection('field')
matchup_collection = database.get_collection('matchups')
results_collection = database.get_collection('pfgl_weekly_results')
team_scores_collection = database.get_collection('team_scores')

def get_matchups(segment: int, week: int) -> list[dict]:
    """
    segment 1-3
    week 0-8
    """
    
    return list(matchup_collection.find({"segment": segment, "week": week}, {"_id": 0}))


def get_all_teams():
    """
    Return list of team objects or None if something goes terribly wrong
    """
    return list(teams_collection.find({}, {"_id": 0}))


def get_team_by_manager(manager_name: str):
    """
    return roster object from db or None if manager_name does not exist
    """
    return teams_collection.find_one({"manager": manager_name}, {"_id": 0})
    

# Players have optional {dg_name} attribute for matching with datagolf
def get_team_starting_lineups(kwp=False) -> list:
    """
    Return list of teams with only starting players included
    """
    if not kwp:
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
    else:
        return kwp_teams_collection.aggregate(
            [{
                "$project": {
                    "_id": 0,
                    "manager": 1,
                    "manager_name": 1,
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
    
    
def compile_weekly_results():
    tourney_name = get_tournament_name()
    scoreboard = results_collection.find_one({"tournament_details.tournament_name": tourney_name})
    matchups_with_ids = get_matchups(config("SEGMENT", cast=int), config("WEEK", cast=int))
    
    team_results = []
        
    opponents = {}
    for matchup in matchups_with_ids:
        opponents[matchup["managers"][0]] = matchup["managers"][1]
        opponents[matchup["managers"][1]] = matchup["managers"][0]
        
    scores = {}
    for team in scoreboard["teams"]:
        team_score_with_bonus = team["team_score"] - sum([p["pfgl_bonus"] for p in team["players"]])
        team_score_without_bonus = team["team_score"]
        scores[team["manager"]] = [team_score_with_bonus, team_score_without_bonus]
        
        team_results.append({
            "manager": team["manager"], 
            "segment": config("SEGMENT", cast=int),
            "week": config("WEEK", cast=int),
            "score_with_bonus": team_score_with_bonus,
            "score_without_bonus": team["team_score"],
            "opponent": opponents[team["manager"]]
        })
    
    for res in team_results:
        res["opponent_score_with_bonus"] = scores[res["opponent"]][0]
        res["opponent_score_without_bonus"] = scores[res["opponent"]][1]
    
    team_scores_collection.insert_many(team_results)
    
    return {"message": "success!"}

def get_kwp_field():
    team_rosters = list(kwp_teams_collection.find({}, {"manager_name": 1, "players": "$roster.name", "_id": 0}))
    
    player_field = set([p["name"] for p in list(field_collection.find({"event_name": get_tournament_details()["tournament_name"]}, {"name": "$player_name", "_id": 0}))])
    
    field = []
    
    for team in team_rosters:
        manager = team["manager_name"]
        team_field = {"manager_name": manager, "count": 0, "players": []}
        for player in team["players"]:
            if player in player_field:
                team_field["players"].append({"name": player, "playing": True})
                team_field["count"] += 1
            else:
                team_field["players"].append({"name": player, "playing": False})
        field.append(team_field)
    
    return field


def get_team_total_scores_to_par() -> dict:
    return {
        s["_id"]: s["total_score_to_par"] for s in list(
            team_scores_collection.aggregate([{
                "$group": {
                    "_id": "$manager", 
                    "total_score_to_par": {
                        "$sum": "$score_with_bonus"
                    }
                }
            }])
        )
    }
