from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import requests

from app.database import get_roster_by_manager

app = FastAPI()

# expose static files (js)
app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://pfgl.webflow.io",
    "https://pfgl.webflow.io",
    "null" # for testing html locally
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Home"])
def get_root():
    return {
        "message": "Welcome to the PFGL!"
    }

@app.get("/api/v1/request")
async def test_request():
    url = "https://penfield.ai"
    
    r = requests.get(url)
    r.raise_for_status
    
    return {
        "penfield_homepage": r.text
    }
   
 
@app.get("/api/v1/scoreboard")
async def scoreboard():
    
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
@app.get("/api/v1/roster/{manager}")
def roster_db_test(manager: str):
    roster = get_roster_by_manager(manager)
    if roster:
        return roster
    
    return {"message": "manager does not exist"}
    
