# Architecture

## Backend Layers

- `api`: FastAPI routers, dependencies, and HTTP error mapping.
- `schemas`: Pydantic request and response contracts.
- `services`: business rules and transaction orchestration.
- `repositories`: database queries and persistence through SQLAlchemy sessions.
- `models`: SQLAlchemy ORM tables and relationships.
- `scripts`: backend utility commands, including demo data import.

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
- `CupService` owns cup semifinal generation, final generation, and bracket
  reads. Cup matches are regular `Match` rows marked with `CupStage`.
- Cup semifinals can be generated from manual team ids or from the top four
  teams ordered by `previous_season_place`; if previous season places are not
  available, manual selection remains the supported path.
- Cup final generation is derived from finished semifinal winners and rejects
  unfinished or drawn semifinals.
- `ScheduleService` validates team match limits across all tournaments using
  Monday-through-Sunday weeks, generates championship double round-robin
  schedules, and exposes season/stadium schedule reads. Season schedule reads
  support optional filters by team, tournament, and inclusive date range.
- Championship schedule generation creates all matches in one transaction and
  rolls back the batch if any generated match violates calendar limits.
- Championship schedule generation resolves stadiums by home team first, then
  by explicit team mapping, then by fallback stadium.
- `ValidationService` checks referee availability for parallel matches at the
  same scheduled datetime.
- `TicketPriceService` calculates the default match ticket price once at match
  creation. The current formula uses a base price of `20.00`, stadium capacity
  factors, and the highest club coefficient among the two teams.
- `LineupService` owns match lineup editing and automatic lineup generation. It
  validates match participation, player-team membership, duplicate players,
  duplicate lineup numbers, and basic red-card/five-yellow-card suspension
  rules.
- Automatic lineup generation can prioritize preferred players, skip suspended
  preferred players, fill open slots with eligible teammates, and optionally
  replace an existing team lineup.
- `MatchProtocolService` owns match event recording and match finishing. It
  validates participant teams, player-team membership, optional assist players,
  mutable match status, and final score consistency with goal events. When a
  match is finished, it refreshes player statistics for the season and refreshes
  championship standings only for championship matches.
- `RandomResultService` owns random match result generation. It creates bounded
  protocol events, rejects matches with existing protocol events, finishes the
  match, and refreshes the same season standings/statistics in one transaction.
- `StandingsService` recalculates `TeamSeasonStats` from finished championship
  matches and orders places by points, goal difference, goals scored, then
  `team_id`. Manual recalculate endpoints remain available, while finish/random
  services can reuse the same rebuild logic inside their own transaction.
- `StatisticsService` recalculates `PlayerSeasonStats` from protocol events in
  finished matches and exposes leaderboards by supported stat metrics. Manual
  recalculate endpoints remain available, while finish/random services can
  reuse the same rebuild logic inside their own transaction.
- GitHub Actions runs backend CI on pushes to `master`/`main` and pull requests:
  tests, `ruff check .`, `black --check .`, and Alembic migration drift checks
  against PostgreSQL.
- `app.scripts.seed_demo_data` imports parsed LaLiga CSV files and creates demo
  season data through ORM sessions. The command is idempotent for its own seeded
  season, teams, stadiums, players, referees, and cup semifinal fixtures.

## Implemented Domain Services

- `MatchService`: match CRUD, rescheduling, referee assignment, and manual
  ticket price updates.
- `CupService`: four-team semifinal generation from manual ids or previous
  season places, final generation from semifinal winners, and bracket reads.
- `ScheduleService`: calendar validation for one match per day and two matches
  per Monday-through-Sunday week, double round-robin championship generation,
  and season/stadium schedule reads with season-level filters.
- `TicketPriceService`: default ticket pricing.
- `ValidationService`: referee availability checks.
- `LineupService`: match lineup listing, creation, update, deletion, automatic
  lineup generation, and suspension validation.
- `MatchProtocolService`: event listing, creation, update, deletion, and
  finishing matches.
- `RandomResultService`: bounded random score and protocol event generation.
- `StandingsService`: championship table recalculation and season standings
  reads.
- `StatisticsService`: player season statistics recalculation and leaderboards.
- `seed_demo_data`: utility script for importing club and squad CSV data into a
  runnable demo dataset.

## Agreed Business Rules For Upcoming Work

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
