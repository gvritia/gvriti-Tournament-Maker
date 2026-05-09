# Tournament Maker Backend

Backend for a study project that manages a national football championship and a
cup tournament. This iteration contains only the backend architecture skeleton:
FastAPI app, SQLAlchemy models, Pydantic schemas, Alembic config, PostgreSQL
Docker Compose config, and a healthcheck endpoint.

Frontend is intentionally not created in this iteration.

## Requirements

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL, started through `docker-compose.yml`

## First Run

From the repository root:

```powershell
docker compose up -d db
```

The PostgreSQL container is exposed on host port `55432` to avoid conflicts with
locally installed PostgreSQL services. The container still uses port `5432`
internally.

From the backend directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

If you use an already existing virtual environment, install dependencies into
that active environment first:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The app requires `pydantic-settings`, `SQLAlchemy`, `psycopg`, `python-jose`,
and the other packages listed in `requirements.txt`.

Healthcheck:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```json
{"status": "ok", "service": "Tournament Maker Backend"}
```

## Demo Data

After PostgreSQL is running and migrations are applied, seed the demo LaLiga
dataset from the parsed CSV files:

```powershell
cd backend
python -m app.scripts.seed_demo_data `
  --clubs-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_clubs.csv" `
  --squads-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_squads.csv"
```

The seed command creates a demo season, championship and cup tournaments, teams,
home stadiums, players, referees, and cup semifinal fixtures. It can be run
again safely for the same dataset. Add `--generate-championship-schedule` to
also create a full double round-robin championship schedule.

## Alembic

Apply migrations and check for schema drift:

```powershell
cd backend
alembic upgrade head
alembic check
```

## Tests and Formatting

```powershell
cd backend
pytest
ruff check .
black .
```

## API Status Codes

- `GET`: `200 OK`
- create `POST`: `201 Created`
- action `POST`, including login: `200 OK`
- `PATCH`/`PUT`: `200 OK`
- `DELETE`: `204 No Content`
- invalid payload: `422 Unprocessable Entity`
- invalid or missing JWT: `401 Unauthorized`
- forbidden action: `403 Forbidden`
- missing resource: `404 Not Found`
- duplicate or scheduling conflict: `409 Conflict`

## Project Layout

```text
app/core          settings, security, constants, exceptions
app/db            SQLAlchemy base and session
app/models        SQLAlchemy ORM models
app/schemas       Pydantic v2 API schemas
app/api           FastAPI routers and dependencies
app/repositories  database access layer
app/services      business logic layer
app/utils         shared helpers
alembic           migration environment
tests             pytest tests
```
