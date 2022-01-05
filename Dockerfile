FROM python:3.9-slim

ENV DB_HOST=mongodb://mongodb:27017
ENV UVICORN_RELOAD=False
ENV ALLOWED_HOSTS="https://pfgl.webflow.io, http://pfgl.webflow.io"
ENV COUNTING_SCORES=4
ENV UPDATE_PLAYER_SCORES_DB=False
ENV HARDCODED_LEADERBOARD_URL=True


RUN pip install pipenv

ADD Pipfile /Pipfile
ADD Pipfile.lock /Pipfile.lock
ADD main.py /main.py

RUN pipenv install --system --deploy

EXPOSE 8080

COPY ./app app
COPY ./static static

CMD ["python", "main.py"]