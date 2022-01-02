FROM python:3.9-slim

RUN pip install pipenv

ADD Pipfile /Pipfile
ADD Pipfile.lock /Pipfile.lock
ADD main.py /main.py
ADD okteto-stack.yaml /okteto-stack.yaml
ADD .env /.env

RUN pipenv install --system --deploy

EXPOSE 8080

COPY ./app app
COPY ./static static

CMD ["python", "main.py"]