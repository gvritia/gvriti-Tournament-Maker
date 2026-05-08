# AGENTS.md

## Project Summary

This repository contains a study backend for organizing a national football
championship and a cup tournament. The system will manage organizers, teams,
players, stadiums, referees, seasons, tournaments, matches, lineups, match
events, standings, ticket prices, schedules, and player statistics.

## Backend Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 ORM
- Alembic
- Pydantic v2
- JWT authorization
- passlib/bcrypt
- python-jose
- pydantic-settings
- pytest + httpx
- ruff + black
- Docker Compose for PostgreSQL

## Frontend Restriction

Do not create or implement frontend code until the user explicitly asks for it.
Current work should stay inside the backend, docs, and repository configuration.

## Architecture Rules

- Put business logic only in `backend/app/services`.
- Put SQLAlchemy ORM models only in `backend/app/models`.
- Put Pydantic schemas only in `backend/app/schemas`.
- Keep FastAPI endpoints thin: validation, dependency wiring, service calls, and
  response mapping only.
- Access the database through `backend/app/repositories`.
- Manage schema changes through Alembic migrations.
- Do not store arrays of players inside a team. Use `Player.team_id`.
- Do not store ticket price as the main stadium field. Ticket price belongs to
  `Match.ticket_price`.
- Do not store all statistics directly in `Team`. Use seasonal stats tables or
  recalculation services.
- Stadiums do not depend on seasons directly.
- Matches must use `home_team_id` and `away_team_id`.
- Store referees through `Match.referee_id`.
- Store match lineups in `MatchLineup`.
- Store match protocol events in `MatchEvent`.
- Respect domain calendar constraints in services:
  - a team cannot play more than one match per day;
  - a team cannot play more than two matches per week;
  - championship and cup matches both count toward those limits;
  - a referee cannot be assigned to parallel matches.
- When architecture decisions change, update `docs/PROJECT_CONTEXT.md`.

## Commands

Start PostgreSQL from the repository root:

```powershell
docker compose up -d db
```

Run the backend:

```powershell
cd backend
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Run tests and formatters:

```powershell
cd backend
pytest
ruff check .
black .
```

Run migrations:

```powershell
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
