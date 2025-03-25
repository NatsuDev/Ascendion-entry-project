FROM python:3.10.12-slim

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

RUN apt update && apt install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv --no-cache-dir

COPY Pipfile /usr/src/app
COPY Pipfile.lock /usr/src/app
RUN pipenv install --deploy --ignore-pipfile

COPY src/ /usr/src/app/src/
COPY env/ /usr/src/app/env/
COPY migrations/ /usr/src/app/migrations/

CMD ["pipenv", "run", "python", "src/main.py"]
