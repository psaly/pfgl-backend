import json

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
from decouple import config, Csv

from app.database import get_all_teams, get_tournament_details, get_team_starting_lineups, update_active_event, compile_weekly_results, get_kwp_field
from app.database import get_player_score_by_name, insert_player_scores, update_field_this_week, get_matchups, get_team_total_scores_to_par
from app.web_utils import scrape_live_leaderboard, get_field_json, send_slack_bonus_request, update_webflow_team
import app.slack_utils as slack_utils

TIE_IMAGE = "https://cdn.vox-cdn.com/thumbor/guM-FItrKThQmkwjcLbrKw8AejA=/46x0:551x337/1400x1400/filters:focal(46x0:551x337):format(jpeg)/cdn.vox-cdn.com/uploads/chorus_image/image/52322037/beamer.0.0.jpeg"
TIE_TEXT = "Tied!"

# Our app
app = FastAPI()

origins = config('ALLOWED_HOSTS', cast=Csv())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# expose static files (js)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Intervals for scheduled tasks (in mins)
leaderboard_scrape_interval = config("LEADERBOARD_SCRAPE_INTERVAL", cast=int)
field_update_interval = config("FIELD_UPDATE_INTERVAL", cast=int)

# For displaying old tournament leaderboard
display_old_tournament_leaderboard = config(
    "DISPLAY_OLD_TOURNAMENT_LEADERBOARD", cast=bool)
old_tournament_name = config("OLD_TOURNAMENT_NAME")
old_tournament_url = config("OLD_TOURNAMENT_URL")

# tasks to start immediately when app starts up and run every {SCRAPE_INTERVAL} minutes


@app.on_event("startup")
@repeat_every(seconds=60 * leaderboard_scrape_interval)
def leaderboard_scraper() -> None:
    """
    Scheduled task to be run in fastapi threadpool. 
    Scrapes ESPN leaderboard and adds scores to player_scores collection in database.
    """
    output_task_name = "LEADERBOARD SCRAPER"
    print(f"{output_task_name} RUNNING (every {leaderboard_scrape_interval} mins).")
    update_player_scores_in_db = config("UPDATE_PLAYER_SCORES_DB", cast=bool)
    if update_player_scores_in_db:
        if display_old_tournament_leaderboard:
            print(
                f"{output_task_name} ALERT: USING OLD TOURNAMENT: {old_tournament_name}.")
            player_scores = scrape_live_leaderboard(url=old_tournament_url)
        else:
            player_scores = scrape_live_leaderboard()
        insert_result = insert_player_scores(player_scores)
        print(
            f"{output_task_name} DONE: Successfully inserted {insert_result['scores_successfully_inserted']} scores.")
        if not insert_result["success"]:
            print(
                f"{output_task_name} ERROR: Could not insert the following {len(insert_result['errors_inserting'])} scores: {insert_result['errors_inserting']}.")
    else:
        print(f"{output_task_name} ALERT: DB UPDATING IS PAUSED!")


@app.on_event("startup")
@repeat_every(seconds=60 * field_update_interval)
def field_updater() -> None:
    """
    Scheduled task to be run in fastapi threadpool. 
    Update field and save to db
    """
    output_task_name = "FIELD UPDATER"
    print(f"{output_task_name} RUNNING (every {field_update_interval} mins).")
    update_field = config("UPDATE_FIELD", cast=bool)
    if update_field:
        player_field = get_field_json()
        message = update_field_this_week(player_field)
        print(f"{output_task_name} DONE: {message}")
    else:
        print(f"{output_task_name} ALERT: FIELD UPDATING IS PAUSED!")

    # set old tourney as active!!!!!
    if display_old_tournament_leaderboard:
        update_active_event(old_tournament_name)


@app.on_event("startup")
def publish_rosters():
    """
    Update webflow rosters collection.
    """
    if config("PUBLISH_ROSTERS", cast=bool):
        print("PUBLISHING ROSTERS:")
        for team in get_all_teams():
            update_webflow_team(team)


# ROUTES
@app.get("/", tags=["Home"])
def get_root():
    return {
        "message": "Welcome to the PFGL!"
    }


@app.get("/api/v1/standings")
async def standings():
    """
    PFGL standings page backend endpoint.
    rank, player, team, record, pct, lsw, tstp
    """
    output = {"standings": []}

    total_scores_dict = get_team_total_scores_to_par()

    for team in get_all_teams():
        data = {}
        data["manager_name"] = team["manager_name"]
        data["team_name"] = team["team_name"]
        data["record"] = team["record"]
        record = team["record"].split("-")
        wins = int(record[0])
        losses = int(record[1])
        data["pct"] = f'{wins/(wins+losses):.3f}'
        data["lowest_score_weeks"] = int(team["overall_weekly_wins"])
        data["total_score_to_par"] = int(total_scores_dict[team["manager"]])

        output["standings"].append(data)

    # sort standings: tiebreaker is total_score_to_par (works because 'sort' is stable!)
    output["standings"].sort(key=lambda x: x["total_score_to_par"])
    output["standings"].sort(key=lambda x: x["pct"], reverse=True)

    for i, row in enumerate(output["standings"]):
        row["rank"] = i + 1
    
    return output


@app.get("/api/v1/scoreboard")
async def scoreboard():
    """
    PFGL scoring page backend endpoint.
    """
    team_lineups = get_team_starting_lineups()
    tourney_details = get_tournament_details()
    tourney_name = tourney_details["tournament_name"]

    response = {"teams": [], "matchup_base_ids": {},
                "matchup_winning": {}, "tournament_details": tourney_details}
    team_scores = {}
    team_logo_urls = {}

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
                    "score_to_par": 0,
                    "thru": '???'
                })
        player_scores.sort(key=lambda x: x["score_to_par"])
        counting_scores = config("COUNTING_SCORES", cast=int)
        team_score = sum([x["score_to_par"]
                         for x in player_scores[:counting_scores]])

        del team["roster"]
        team["players"] = player_scores
        team["team_score"] = team_score

        team_scores[team["manager"]] = team_score
        team_logo_urls[team["manager"]] = team["logo_url"]

        response["teams"].append(team)

    for i, matchup in enumerate(get_matchups(config("SEGMENT", cast=int), config("WEEK", cast=int))):
        # determine who is winning
        if team_scores[matchup["managers"][0]] < team_scores[matchup["managers"][1]]:
            response["matchup_winning"][f"m{i}"] = {
                "name": matchup["managers"][0],
                "logo_url": team_logo_urls[matchup["managers"][0]]
            }

        # TIED!
        elif team_scores[matchup["managers"][0]] == team_scores[matchup["managers"][1]]:
            response["matchup_winning"][f"m{i}"] = {
                "name": TIE_TEXT,
                "logo_url": TIE_IMAGE
            }

        else:
            response["matchup_winning"][f"m{i}"] = {
                "name": matchup["managers"][1],
                "logo_url": team_logo_urls[matchup["managers"][1]]
            }

        # build string prefixes for identifying matchup divs
        for j, manager in enumerate(matchup["managers"]):
            response["matchup_base_ids"][manager] = f"m{i}-p{j}"

    return response


# Slack endpoints
@app.post('/api/v1/kwp/scores')
async def kwp_scores(req: Request):
    form = await req.form()

    if not slack_utils.valid_request(form, slack_utils.SlackChannel.KWP):
        raise HTTPException(status_code=400, detail="Invalid token.")

    response_in_channel = False if "-h" in form["text"] else True
    bonus = True if "-b" in form["text"] else False

    tourney_details = get_tournament_details()
    tourney_name = tourney_details["tournament_name"]

    team_scores = _get_kwp_scores(tourney_name, bonus)

    return slack_utils.build_slack_response(
        team_scores,
        tourney_name,
        in_channel=response_in_channel,
        show_player_scores=True,
        bonus=bonus
    )


@app.post('/api/v1/kwp/leaderboard')
async def kwp_leaderboard(req: Request):
    form = await req.form()

    if not slack_utils.valid_request(form, slack_utils.SlackChannel.KWP):
        raise HTTPException(status_code=400, detail="Invalid token.")

    response_in_channel = False if "-h" in form["text"] else True
    bonus = True if "-b" in form["text"] else False

    tourney_details = get_tournament_details()
    tourney_name = tourney_details["tournament_name"]

    team_scores = _get_kwp_scores(tourney_name, bonus)

    return slack_utils.build_slack_response(
        team_scores,
        tourney_name,
        in_channel=response_in_channel,
        show_player_scores=False,
        bonus=bonus
    )


@app.post("/api/v1/kwp/field", status_code=200)
async def kwp_field(req: Request):
    form = await req.form()

    if not slack_utils.valid_request(form, slack_utils.SlackChannel.KWP):
        raise HTTPException(status_code=400, detail="Invalid token.")

    response_in_channel = False if "-h" in form["text"] else True

    tourney_details = get_tournament_details()
    tourney_name = tourney_details["tournament_name"]

    return slack_utils.build_field_response(get_kwp_field(), tourney_name, response_in_channel)


@app.post("/api/v1/kwp/bonus", status_code=200)
async def slack_bonus_endpoint(req: Request):
    form = await req.form()

    form_payload = json.loads(form["payload"])

    print(form_payload)

    url = form_payload["response_url"]

    if form_payload["actions"][0]["value"] == 'show':
        form_payload["message"]["blocks"][2]["text"]["text"].replace(
            "Off_", "On_")
    else:
        form_payload["message"]["blocks"][2]["text"]["text"].replace(
            "On_", "Off_")

    status_code = send_slack_bonus_request(
        url, form_payload["message"]["blocks"])
    print(f"Show/hide POST request status_code: {status_code}")

    return {}


# THIS IS REALLY BAD TO HAVE AS A GET BUT IT'S FOR TESTING
@app.get("/api/v1/scraping_test")
def get_live_scores():
    """
    For testing scraping code. DOES NOT ADD TO DATABASE!!!!!
    """
    if display_old_tournament_leaderboard:
        player_scores = scrape_live_leaderboard(url=old_tournament_url)
    else:
        player_scores = scrape_live_leaderboard()

    return player_scores


@app.get("/api/v1/compile_results")
def compile_results():
    """
    Store weekly matchup results in database
    """
    return compile_weekly_results()


def _get_kwp_scores(tournament_name: str, bonus: bool) -> list[dict]:
    team_lineups = get_team_starting_lineups(kwp=True)

    team_scoring = []

    for team in team_lineups:
        player_scores = []
        for player in team["roster"]:
            score = get_player_score_by_name(player["name"], tournament_name)
            if score:
                del score["tournament_name"]
                if bonus:
                    score["kwp_score_to_par"] -= score["kwp_bonus"]

                player_scores.append(score)
            # This player could not be found on the leaderboard
            else:
                player_scores.append({
                    "player_name": player["name"],
                    "position": '???',
                    "kwp_score_to_par": 0,
                    "thru": '???'
                })
        player_scores.sort(key=lambda x: x["kwp_score_to_par"])

        # top 4 count
        team_score = sum([x["kwp_score_to_par"] for x in player_scores[:4]])

        team_scoring.append(
            {"manager_name": team['manager_name'], "team_score": team_score, "player_scores": player_scores})

    team_scoring.sort(key=lambda x: x["team_score"])

    return team_scoring
