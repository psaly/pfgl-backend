FROM python:3.9-slim-bullseye

RUN pip install pipenv

WORKDIR /

ADD Pipfile Pipfile.lock main.py /

RUN pipenv install --system --deploy

EXPOSE 8080

COPY ./app app
COPY ./static static

CMD ["python", "main.py"]
