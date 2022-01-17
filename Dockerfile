FROM python:3.9-slim

ENV DB_HOST=mongodb://mongodb:27017
ENV UVICORN_RELOAD=False
ENV ALLOWED_HOSTS="https://pfgl.webflow.io, http://pfgl.webflow.io"
ENV COUNTING_SCORES=4
ENV UPDATE_PLAYER_SCORES_DB=True
ENV LEADERBOARD_SCRAPE_INTERVAL=1000
ENV UPDATE_FIELD=False
ENV FIELD_UPDATE_INTERVAL=60
ENV DISPLAY_OLD_TOURNAMENT_LEADERBOARD=True
ENV OLD_TOURNAMENT_URL="https://www.espn.com/golf/leaderboard/_/tournamentId/401353203"
ENV OLD_TOURNAMENT_NAME="Sentry Tournament of Champions"
ENV SEGMENT=1
ENV WEEK=0
ENV WEBFLOW_TEAM_COLLECTION_ID="619c368b7c5d456d6f173d98"
ENV WEBFLOW_AUTH_TOKEN="cbb0f0444d29e4a70267af4a5c178eff5372ee8633cc79cedb32c5008229ae98"


RUN pip install pipenv

ADD Pipfile /Pipfile
ADD Pipfile.lock /Pipfile.lock
ADD main.py /main.py

RUN pipenv install --system --deploy

EXPOSE 8080

COPY ./app app
COPY ./static static

CMD ["python", "main.py"]