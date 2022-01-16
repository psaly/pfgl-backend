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
    bonus=False) -> dict:
    scores_string = ''
    breakdown_string = ''
    
    for score_data in team_scoring:
        scores_string += '*' + score_data["manager_name"] + '*: `' + _display_score_to_par(score_data["team_score"]) + '`\n'
        breakdown_string += '*' + score_data["manager_name"] + '*\n'
        
        for i, player_data in enumerate(score_data["player_scores"]):
            breakdown_string += ">" + player_data["player_name"] + ': `' \
                + _display_score_to_par(player_data["kwp_score_to_par"]) \
                + '` thru ' + player_data['thru'] + '\n'
                
        breakdown_string += '\n'

    scores_string += '_Bonus: Off_'
    
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


def _display_score_to_par(score: int) -> str:
    """
    Convert 0 to E and add '+' for over par scores
    """
    if score > 0:
        return '+' + str(score)
    elif score == 0:
        return 'E'
    return str(score)
