from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from decouple import config, Csv

from app.database import get_tournament_name, get_team_starting_lineups, get_team_by_manager, get_player_score_by_name, insert_player_scores
from app.leaderboard_scraper import scrape_live_leaderboard

from fastapi_utils.tasks import repeat_every
# ESPN website scraping interval in minutes
SCRAPE_INTERVAL = 120 # 120 minutes

# Our app
app = FastAPI()

# expose static files (js)
app.mount("/static", StaticFiles(directory="static"), name="static")

# deployment
origins = config('ALLOWED_HOSTS', cast=Csv())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# task to start immediately when app starts up and run every {SCRAPE_INTERVAL} minutes
@app.on_event("startup")
@repeat_every(seconds=60 * SCRAPE_INTERVAL)  
def update_live_scores_task() -> None:
    """
    Scheduled task to be run in fastapi threadpool. 
    Scrapes ESPN leaderboard and adds scores to player_scores collection in database.
    """
    player_scores = scrape_live_leaderboard()
    insert_result = insert_player_scores(player_scores)
    if not insert_result["success"]:
        print("LEADERBOARD SCRAPER: Could not insert the following scores:", insert_result["errors_inserting"])
    else:
        print("LEADERBOARD SCRAPER: All scores inserted successfully.")
    



# ROUTES
@app.get("/", tags=["Home"])
def get_root():
    return {
        "message": "Welcome to the PFGL!"
    }


@app.get("/api/v1/scoreboard")
async def scoreboard():
    team_lineups = get_team_starting_lineups()
    tourney_name = get_tournament_name()
    
    response = {"teams": []}
    
    for team in team_lineups:
        player_scores = []
        for player in team["roster"]:
            score = get_player_score_by_name(player["name"], tourney_name)
            if score:
                del score["tournament_name"]
                player_scores.append(score)
            # This player could not be found on the leaderboard
            else:
                player_scores.append({
                    "player_name": player["name"],
                    "position": '???',
                    "score_to_par": 100,
                    "thru": '???'
                })
        player_scores.sort(key=lambda x:x["score_to_par"])
        counting_scores = config("COUNTING_SCORES", cast=int)
        team_score = sum([x["score_to_par"] for x in player_scores[:counting_scores]])
                
        del team["roster"]
        team["players"] = player_scores
        team["team_score"] = team_score

        response["teams"].append(team)    
    
    return response

 
@app.get("/api/v1/scoreboard_hardcoded")
async def scoreboard_hardcoded():
    return {
        "teams":
            {
                "james":
                    {
                        "players":
                            [
                                {
                                    "name": "Justin Thomas",
                                    "score_to_par": "-14",
                                    "position": "2",
                                    "thru": "F"
                                },
                                {
                                    "name": "Webb Simpson",
                                    "score_to_par": "-9",
                                    "position": "T8",
                                    "thru": "F"
                                },
                                {
                                    "name": "Sungjae Im",
                                    "score_to_par": "-8",
                                    "position": "T12",
                                    "thru": "F"
                                },
                                {
                                    "name": "Sung Kang",
                                    "score_to_par": "E",
                                    "position": "T52",
                                    "thru": "F"
                                },
                                {
                                    "name": "Joel Dahmen",
                                    "score_to_par": "E",
                                    "position": "T52",
                                    "thru": "F"
                                },
                                {
                                    "name": "Guido Migliozzi",
                                    "score_to_par": "+1",
                                    "position": "T58",
                                    "thru": "F"
                                },
                                {
                                    "name": "Mac Carter",
                                    "score_to_par": "+8",
                                    "position": "72",
                                    "thru": "F"
                                }
                            ],
                        "team_score": "-31"
                    }
            }
    }
    
# Pymongo is synchronous! Maybe use Motor driver for async in the future!?
@app.get("/api/v1/team/{manager}")
def team_db_test(manager: str):
    team = get_team_by_manager(manager)
    if team:
        return team
    
    return {"message": "manager does not exist"}

# THIS IS REALLY BAD TO HAVE AS A GET BUT IT'S FOR TESTING
# Use repeated task instead eventually!!!
@app.get("/api/v1/scraping_test")
def update_live_scores():
    """
    For testing scraping code. DOES NOT ADD TO DATABASE!!!!!
    """
    player_scores = scrape_live_leaderboard()
    
    return player_scores
