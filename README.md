# Ascendion entry project

## Installation & running (non-dev)

**Follow this section if you don't plan to develop this BE.**

### Prerequisites
- Docker with compose plugin.

### Installation & running

- Run `cp env/.env.example .env.dev`.
- Set `DB__HOST='mariadb'` in `.env.dev`.
- Run `cd deploy && docker compose up -d --build` (for some systems `docker-compose` must be used instead).
- Go to: http://localhost:8080/v1/docs.
- You're done reading this README, start testing.

## Installation & running (dev)

### Prerequisites
- macOS or Linux (otherwise remove `uvicorn`, `uvloop` and `orjson` from `Pipfile`)
- Python 3.10.X.
- Pipenv.
- Docker with compose plugin.

### Installation & running

**Follow this section if you are a BE developer.**

- Run `pipenv install --dev`.
- Configure your IDE to recognize `pipenv` environment.
- Run `pipenv shell` if you IDE still does not.
- Run `pre-commit install`.
- Run `cp env/.env.example .env.dev`.
- Run `cp env/.env.example .env.local`.
- Set `DB__HOST='mariadb'` in `.env.dev`.
- Run `cd deploy && docker compose up -d --build` (for some systems `docker-compose` must be used instead).

Kill the created app container and run `pipenv run python3 src/main.py` 
to enable file change watchdog and hot-reload. \
See [Installation & running (non-dev)](#installation--running-non-dev) for docs access.

## Creating migrations
[yoyo docs](https://ollycope.com/software/yoyo/latest/)

1. Create a file `XXXX_{action}_{subject}.py` in `migrations/` 
  (if unclear, refer to [this](https://ollycope.com/software/yoyo/latest/#migration-files)).
2. Open up any of existing files and follow the structure or refer to yoyo docs.
3. Run the project, new migrations will be automatically applied.
