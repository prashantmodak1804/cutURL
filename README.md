# cutURL

- **Author:** Prashant Modak
- **Roll number:** 25051775
- **Track:** A (Ship It)
- **Program:** GFG KIIT Student Chapter, Cloud & DevOps Domain

## What the app does

cutURL is a small URL shortener. You paste a long link into a web page, the app generates a 6-character code, stores the pair in a PostgreSQL database, and gives you a short link. Opening the short link redirects you to the original URL. A `/healthz` endpoint returns 200 only when the database is reachable, and the app logs the client IP taken from the `X-Forwarded-For` header.

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Front-end page with the shorten form |
| `/shorten` | POST | Stores a URL and returns its short link |
| `/<short_code>` | GET | Redirects to the original URL (404 if unknown) |
| `/healthz` | GET | 200 if the database is reachable, 500 otherwise |

## Architecture diagram

Not added yet.

## Tech stack

- Python 3.12, Flask 3.1, psycopg 3 (binary), gunicorn
- PostgreSQL 17.11
- Docker Engine (multi-stage image, base `python:3.12.14-slim-bookworm`)
- Ubuntu Server virtual machine (key-only SSH, UFW firewall)

## Current status

- Stage 1: Ubuntu Server VM built. Done.
- Stage 2: Linux administration and networking. Done.
- Stage 3: Application containerised. Done. The image is 57.7 MB, runs as a non-root user, has a healthcheck, and uses a pinned base image.
- Stages 4 to 7 and the track layer: not started.

## Run it locally

The app needs a PostgreSQL database reachable under the hostname in `DB_HOST`. The steps below run both as Docker containers on one network.

```bash
git clone https://github.com/prashantmodak1804/cutURL.git
cd cutURL
cp .env.example .env

docker network create cuturl-net

docker run -d --name db --network cuturl-net \
  -e POSTGRES_USER=cuturl_user \
  -e POSTGRES_PASSWORD=cuturl_pass \
  -e POSTGRES_DB=cuturl \
  postgres:17.11

docker build -t cuturl:dev .

docker run -d --name cuturl --network cuturl-net --env-file .env -p 8000:8000 cuturl:dev
```

Then open `http://localhost:8000` or check `curl -i localhost:8000/healthz`.

To stop and clean up:

```bash
docker rm -f cuturl db
docker network rm cuturl-net
```

## Environment variables

Copy `.env.example` to `.env` (the real `.env` is git-ignored). Values in `.env.example` are dummies.

| Variable | Example | Meaning |
|---|---|---|
| `DB_HOST` | `db` | Hostname of the PostgreSQL server. Must match the database container's name on the Docker network |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `cuturl` | Database name |
| `DB_USER` | `cuturl_user` | Database user |
| `DB_PASS` | `cuturl_pass` | Database password |
| `PORT` | `8000` | Optional. Only used when running `python app.py` directly; gunicorn in the image always listens on 8000 |

## Live URL

Not deployed yet.

## CI status

No workflow yet.
