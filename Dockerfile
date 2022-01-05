FROM python:3.9-slim

ENV DB_HOST=mongodb://mongodb:27017
ENV UVICORN_RELOAD=False
ENV ALLOWED_HOSTS="https://pfgl.webflow.io, http://pfgl.webflow.io"
ENV COUNTING_SCORES=4
ENV UPDATE_PLAYER_SCORES_DB=False
ENV LEADERBOARD_SCRAPE_INTERVAL=120
ENV UPDATE_FIELD=False
ENV FIELD_UPDATE_INTERVAL=180
ENV DISPLAY_OLD_TOURNAMENT_LEADERBOARD=True
ENV OLD_TOURNAMENT_URL="https://www.espn.com/golf/leaderboard/_/tournamentId/401243418"
ENV OLD_TOURNAMENT_NAME="PGA Championship"

RUN pip install pipenv

ADD Pipfile /Pipfile
ADD Pipfile.lock /Pipfile.lock
ADD main.py /main.py

RUN pipenv install --system --deploy

EXPOSE 8080

COPY ./app app
COPY ./static static

CMD ["python", "main.py"]