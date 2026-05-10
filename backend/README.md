# Tournament Maker Backend

Backend for a study project that manages a national football championship and a
cup tournament. The backend includes JWT auth, user-scoped tournament data,
CRUD endpoints, schedule generation, cup bracket flow, match lineups, match
protocols, random results, standings, player statistics, Alembic migrations,
and demo data seeding.

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
alembic upgrade head
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
home stadiums, players, referees, and cup semifinal fixtures for the default
demo user `demo@example.com` / `DemoPass123`. It can be run again safely for the
same dataset. Add `--generate-championship-schedule` to also create a full
double round-robin championship schedule.

The demo user can be changed with `--owner-email`, `--owner-nickname`, and
`--owner-password`.

## API Defense Flow

1. Start PostgreSQL, install dependencies, run `alembic upgrade head`, and start
   `uvicorn app.main:app --reload`.
2. Seed demo data with `python -m app.scripts.seed_demo_data ...`.
3. Log in and save the JWT token:

```powershell
$token = (Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"demo@example.com","password":"DemoPass123"}').access_token

$headers = @{ Authorization = "Bearer $token" }
```

4. Show the main protected flow:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/v1/seasons/ -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/v1/teams/ -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/v1/matches/ -Headers $headers
```

5. Create a second user and repeat the same list calls with the second user's
   token. The second user receives only their own empty or newly created data,
   and direct requests for the demo user's entity IDs return `404 Not Found`.

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
