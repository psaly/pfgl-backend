import uvicorn
from decouple import config

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="0.0.0.0", port=8080, reload=config('UVICORN_RELOAD', cast=bool))