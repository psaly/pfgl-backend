__author__ = 'piercesaly'

import requests
from requests.structures import CaseInsensitiveDict
from bs4 import BeautifulSoup
from decouple import config

PFGL_CUT_PENALTY = 5
KWP_CUT_PENALTY = 2

# Bonuses for 1-2-3-4-5 place finishes
KWP_BONUSES = [10,5,3,2,1]
PFGL_WIN_BONUS = 5

WEBFLOW_BASE_URL = "https://api.webflow.com/"

def get_field_json() -> list[dict]:
    """
    Get this week's field from dg. Return list [{player_obj}, etc.]
    """
    r = requests.get("https://api.datagolf.ca/dg-api/v1/model_probs")
    r.raise_for_status()
    return r.json()

def scrape_live_leaderboard(url="https://www.espn.com/golf/leaderboard") -> list:
    """
    Scrape ESPN leaderboard and return list containing all player scores:
    [keys: "tournament_name", "player_name", "position", "score_to_par": "thru"}, ...]
    """
    # make request and check status
    r = requests.get(url)
    r.raise_for_status()

    soup = BeautifulSoup(r.content, 'html.parser')

    # Get tournament name
    tourney_name = soup.select_one('.Leaderboard__Event__Title').text
    
    # Check if the tournament is final because the formatting changes
    status = soup.find('div', class_='status')
    final = True if status and status.findChild() and 'Final' in status.findChild().text and 'Round' not in status.findChild().text else False

    # for storing parsed player data
    all_players = []
    
    worst_score = -1000  # placeholder

    pos_offset = 1  # will be changed to 2 if we see there are movement arrows in the table
    # loop through all tds
    tds = soup.select('td')
    for i in range(len(tds)):
        try:
            for child in tds[i].findChildren():
                if child.has_attr('class') and child['class'][0] == 'MovementArrow':
                    pos_offset = 2
                if child.has_attr('class') and len(child['class']) > 1 and child['class'][1] == 'leaderboard_player_name':
                    pos = None
                    score = None
                    thru = 'F' if final else tds[i+3].text
                    today = tds[i+5].text if final else tds[i+2].text
                    player = child.text
                    kwp_bonus = 0
                    pfgl_bonus = 0
                    
                    score_text = tds[i+1].text
                    
                    if score_text == 'E':
                        score = 0
                    else:
                        try:
                            score = int(score_text)
                            worst_score = max(worst_score, score)

                        # if not an integer, will be CUT/WD/DQ etc. -- ESPN does this weird
                        except ValueError:
                            pos = score_text

                    # get position if we haven't already and store bonuses
                    if pos is None:
                        pos = tds[i-pos_offset].text
                    try:
                        pos_int = int(pos.lstrip("T"))
                        if pos_int == 1:
                            pfgl_bonus = PFGL_WIN_BONUS
                        if pos_int < 6:
                            kwp_bonus = KWP_BONUSES[pos_int - 1]
                            
                    except ValueError:
                        pass
                    
                    
                    # add to players list
                    # score could be None still if we need to fill in with worst score
                    # Maybe create an object here?
                    all_players.append({
                                        "tournament_name": tourney_name,
                                        "player_name": player, 
                                        "position": pos, 
                                        "score_to_par": score, 
                                        "pfgl_bonus": pfgl_bonus,
                                        "kwp_score_to_par": score,
                                        "kwp_bonus": kwp_bonus,
                                        "today": today,
                                        "thru": thru
                                        })                                  
        except KeyError:
            print(f"**WEIRD ERROR** {tds[i]}")
        except IndexError:
            print(f"**INDEX ERROR--tournament is probably not live** {tds[i]}")
    
    
    # update all players who MC/WD/DQ score to the cut placeholder
    for player in all_players:
        if player["score_to_par"] is None:
            player["score_to_par"] = worst_score + PFGL_CUT_PENALTY
            player["kwp_score_to_par"] = worst_score + KWP_CUT_PENALTY
    
    return all_players


def send_slack_bonus_request(url: str, content: dict) -> int:
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"

    data = {
        "replace_original": "true",
        "blocks": content
    }

    
    
    resp = requests.post(url, headers, data)
    return (resp.status_code)


def update_webflow_team(roster_data):
    webflow_collection_id = config("WEBFLOW_TEAM_COLLECTION_ID")
    webflow_auth_token = config("WEBFLOW_AUTH_TOKEN")
    
    url = "https://reqbin.com/echo/patch/json"
    
    

    # headers = {}

    # headers["Accept"] = "application/json"
    # headers["Content-Type"] = "application/json"
    # headers["Authorization"] = f"Bearer {webflow_auth_token}"
    # headers["accept-version"] = "1.0.0"

    # data = """
    # {
    # "Id": 12345,
    # "Customer": "John Smith",
    # "Quantity": 1,
    # "Price": 10.00
    # }
    # """


    # resp = requests.patch(url, headers=headers, data=data)

    # print(resp.status_code)
            
    

