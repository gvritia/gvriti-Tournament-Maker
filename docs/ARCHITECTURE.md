# Architecture

## Backend Layers

- `api`: FastAPI routers, dependencies, and HTTP error mapping.
- `schemas`: Pydantic request and response contracts.
- `services`: business rules and transaction orchestration.
- `repositories`: database queries and persistence through SQLAlchemy sessions.
- `models`: SQLAlchemy ORM tables and relationships.

Endpoints should stay thin. They validate HTTP inputs, call services, and map
domain exceptions to HTTP status codes. Business rules belong in services.

## Current Decisions

- CRUD endpoints require JWT authentication.
- Database writes are committed in services after repository operations.
- Domain errors use app-level exceptions:
  - `NotFoundError` -> `404`
  - `ConflictError` -> `409`
  - `BusinessRuleError` -> `400`
- PostgreSQL is exposed on host port `55432` to avoid local PostgreSQL conflicts.
- Alembic is the only supported way to change the database schema.
- `MatchService` owns match creation, updates, deletion, rescheduling, referee
  assignment, and manual ticket price changes.
- `ScheduleService` validates team match limits across all tournaments using
  Monday-through-Sunday weeks.
- `ValidationService` checks referee availability for parallel matches at the
  same scheduled datetime.
- `TicketPriceService` calculates the default match ticket price once at match
  creation. The current formula uses a base price of `20.00`, stadium capacity
  factors, and the highest club coefficient among the two teams.

## Implemented Domain Services

- `MatchService`: match CRUD, rescheduling, referee assignment, and manual
  ticket price updates.
- `ScheduleService`: calendar validation for one match per day and two matches
  per Monday-through-Sunday week.
- `TicketPriceService`: default ticket pricing.
- `ValidationService`: referee availability checks.

## Planned Domain Services

- `ScheduleService`: double round-robin generation.
- `LineupService`: lineup editing, suspension checks, and replacement selection.
- `MatchProtocolService`: match events and protocol submission.
- `RandomResultService`: bounded random match result and event generation.
- `StandingsService`: team table recalculation.
- `StatisticsService`: player statistics and leaderboards.

## Agreed Business Rules For Upcoming Work

- Championship schedule is double round-robin: home and away.
- Weekly calendar limits use Monday through Sunday.
- Ticket price is calculated once for a match and remains fixed unless manually
  changed.
- Ticket price formula:
  `total_price = (base_price + capacity_factor) * club_coefficient`.
- Club coefficient tiers:
  - top third of previous season table: `2.0`
  - middle third: `1.5`
  - bottom third: `1.1`
- Five yellow cards or one red card suspend a player for the next match.
- Automatic lineup generation should replace suspended players with eligible
  players from the same team.
- Random result generation must use realistic caps for scorelines and cards.
