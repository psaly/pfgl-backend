from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/", tags=["Home"])
def get_root():
    return {
        "message": "Running on okteto?"
    }

@app.get("/request")
async def make_request():
    url = "https://penfield.ai"
    
    r = requests.get(url)
    r.raise_for_status
    
    return {
        "penfield_homepage": r.text
    }