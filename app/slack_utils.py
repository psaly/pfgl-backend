from enum import Enum

class SlackChannel(Enum):
    PFGL = (None, None)
    KWP = ('b9dpA3duAR2GWr9mHOClpgQL', 'TRSTAS2GJ')
    
    def __init__(self, token, team_id) -> None:
        self.token = token
        self.team_id = team_id

def valid_request(slack_form, channel: SlackChannel):
    return slack_form['token'] == channel.token and slack_form['team_id'] == channel.team_id
    
    
def build_slack_response(
        team_scoring: list[dict], 
        tourney_name: str, 
        in_channel=True, 
        show_player_scores=True,
        bonus=False
) -> dict:
    scores_string = ''
    breakdown_string = ''
    
    for s in team_scoring:
        scores_string += f'*{s["manager_name"]}*: `{_display_score_to_par(s["team_score"])}`\n'
        breakdown_string += f'*{s["manager_name"]}*\n'
        
        for p in s["player_scores"]:
            breakdown_string += f'>{p["player_name"]}: `{_display_score_to_par(p["kwp_score_to_par"])}` thru {p["thru"]}\n'
                
        breakdown_string += '\n'

    if bonus:
        scores_string += '_Bonus: ON_'
    else:
        scores_string += '_Bonus: OFF_'
    
    slack_res = {
        "blocks": [   
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": tourney_name
                }
		    },
            {
                "type": "divider"
            },
		    {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": scores_string
                }
		    },
            {
                "type": "divider"
            }
	    ]
    }
    
    # WITH BUTTONS!
    # slack_res = {
    #     "blocks": [   
    #         {
    #             "type": "header",
    #             "text": {
    #                 "type": "plain_text",
    #                 "text": tourney_name
    #             }
	# 	    },
    #         {
    #             "type": "divider"
    #         },
	# 	    {
    #             "type": "section",
    #             "text": {
    #                 "type": "mrkdwn",
    #                 "text": scores_string
    #             }
	# 	    },
    #         {
    #             "type": "actions",
    #             "elements": [
    #                 {
    #                     "type": "button",
    #                     "text": {
    #                         "type": "plain_text",
    #                         "text": "Show Bonus"
    #                     },
    #                     "style": "primary",
    #                     "value": "show"
    #                 },
    #                 {
    #                     "type": "button",
    #                     "text": {
    #                         "type": "plain_text",
    #                         "text": "Hide Bonus"
    #                     },
    #                     "value": "hide"
    #                 }
    #             ]
	# 	    },
    #         {
    #             "type": "divider"
    #         },
	#     ]
    # }
    
    if show_player_scores:
        slack_res["blocks"].extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": breakdown_string
                }
		    },
            {
                "type": "divider"
            }
        ])
    
    if in_channel:
        slack_res["response_type"] = "in_channel"
        
    return slack_res


def build_field_response(
        field: list[dict], 
        tourney_name: str, 
        in_channel=True
) -> dict:
    summary_string = ''
    team_strings = ['', '', '', '']
    
    print(field)
    
    for i, t in enumerate(field):
        summary_string += f'*{t["manager_name"]}*: `{t["count"]}`\n'
        team_strings[i] += f'*{t["manager_name"]}*\n'
        
        for p in t["players"]:
            team_strings[i] += f'>{p["name"]}: '
            if p["playing"]: 
                team_strings[i] += ":white_check_mark:"
            else:
                team_strings[i] += ":x:"
            team_strings[i] += '\n'
    
    slack_res = {
        "blocks": [   
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{tourney_name} Field" 
                }
		    },
            {
                "type": "divider"
            },
		    {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": summary_string
                }
		    },
            {
                "type": "divider"
            }
	    ]
    }
    

    for ts in team_strings:
        slack_res["blocks"].extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ts
                }
		    },
            {
                "type": "divider"
            }
        ])
    
    if in_channel:
        slack_res["response_type"] = "in_channel"
    
    print(slack_res)
    
    return slack_res

def _display_score_to_par(score: int) -> str:
    """
    Convert 0 to E and add '+' for over par scores
    """
    if score > 0:
        return '+' + str(score)
    elif score == 0:
        return 'E'
    return str(score)
