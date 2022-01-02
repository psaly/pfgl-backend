__author__ = 'piercesaly'

import requests
from bs4 import BeautifulSoup


def scrape_live_leaderboard() -> dict:
    # url = "https://www.espn.com/golf/leaderboard/_/tournamentId/401353202" # 2021-22 RSM
    url = "https://www.espn.com/golf/leaderboard/_/tournamentId/401243418" # 2020-21 PGA Champ

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

    # loop through all tds
    tds = soup.select('td')
    for i in range(len(tds)):
        # might not need to check this every time but why not for now
        pos_offset = 1
        try:
            for child in tds[i].findChildren():
                if child.has_attr('class') and child['class'][0] == 'MovementArrow':
                    pos_offset = 2
                if child.has_attr('class') and len(child['class']) > 1 and child['class'][1] == 'leaderboard_player_name':
                    pos = None
                    score = None
                    thru = 'F' if final else tds[i+3].text
                    player = child.text
                    
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

                    # get position if we haven't already
                    if pos is None:
                        pos = tds[i-pos_offset].text

                    # add to players list
                    # score could be None still if we need to fill in with worst score
                    # Maybe create an object here?
                    all_players.append({
                                        "name": player, 
                                        "position": pos, 
                                        "score_to_par": score, 
                                        "thru": thru
                                        })                                  
        except KeyError:
            print("**WEIRD ERROR**", tds[i])
    
    cut_score = worst_score + 5
    
    # update all players who MC/WD/DQ score to the cut placeholder
    for player in all_players:
        if player["score_to_par"] is None:
            player["score_to_par"] = cut_score
        
    return {
        "tournament_name": tourney_name,
        "live_scores": all_players,
    }
            
    
