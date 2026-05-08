# Development Log

## 2026-05-08

### Backend Skeleton

- Created FastAPI backend structure, SQLAlchemy models, Pydantic schemas,
  Alembic setup, PostgreSQL Docker Compose config, healthcheck, and project
  documentation.
- Added `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, and `backend/README.md`.
- Next steps at the time: JWT auth and initial migration.

### JWT Auth

- Added registration, login, and current-user endpoints.
- Added bcrypt password hashing, JWT Bearer dependency, session rollback
  behavior, and auth tests.
- Pinned compatible `bcrypt` version for `passlib`.
- Next steps at the time: initial database migration.

### Initial Migration

- Added `requirements.txt` and `requirements-dev.txt`.
- Added initial Alembic migration for current ORM models.
- Changed Docker PostgreSQL host port to `55432` to avoid local Postgres
  conflicts.
- Applied migration to PostgreSQL and verified auth against the real database.
- Next steps at the time: CRUD for core entities.

### Core CRUD

- Added authenticated CRUD for seasons, teams, players, and stadiums.
- Added service-layer validation for duplicates, missing related teams, season
  dates, and duplicate player numbers.
- Added CRUD tests and verified PostgreSQL smoke flow.
- Next steps at the time: CRUD for referees and tournaments.

### Referee And Tournament CRUD

- Added authenticated CRUD for referees and tournaments.
- Added validation for duplicate referees, missing seasons, and duplicate
  tournament names inside one season.
- Updated project context with agreed future business rules for ticket pricing,
  weekly limits, double round-robin championship, suspensions, and random match
  generation.
- Added architecture notes for current layers and planned domain services.
- Next steps: implement match creation with basic validations, ticket price
  calculation, and referee assignment.
