# Development Log

## 2026-05-09

### Automatic Standings And Statistics Refresh

- Added automatic season statistics refresh after protocol-based match finish
  and random result generation.
- Championship standings now refresh automatically after finished championship
  matches, while finished cup matches update player statistics without changing
  league standings.
- Kept manual standings/statistics recalculation endpoints intact by sharing the
  same non-committing rebuild logic with match-finishing services.
- Added tests for championship finish refresh, cup finish behavior, random
  result refresh, and repeated finish/generation duplicate prevention.
- Changed files: `backend/app/api/v1/endpoints/protocol.py`,
  `backend/app/api/v1/endpoints/random_results.py`,
  `backend/app/services/match_protocol_service.py`,
  `backend/app/services/random_result_service.py`,
  `backend/app/services/standings_service.py`,
  `backend/app/services/statistics_service.py`,
  `backend/tests/test_match_protocol.py`, and
  `backend/tests/test_random_results.py`.
- Next steps: add schedule filters, polish cup team selection by previous season
  place, or add CI.

### Automatic Lineup Generation

- Added authenticated lineup generation endpoint through
  `/matches/{match_id}/lineups/generate`.
- Extended `LineupService` to generate a lineup for one match participant team,
  honor preferred players, skip suspended preferred players, fill open slots
  with eligible teammates, and optionally replace an existing team lineup.
- Added lineup tests for successful generation, replacement of a suspended
  preferred player, existing-lineup conflicts, explicit replacement, wrong-team
  preferred players, not enough eligible players, and JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/lineups.py`,
  `backend/app/services/lineup_service.py`,
  `backend/app/repositories/match_lineup.py`,
  `backend/app/schemas/match_lineup.py`, and `backend/tests/test_lineups.py`.
- Next steps: add automatic standings/statistics recalculation after match
  finish or polish schedule filters/CI/demo data.

### Random Result Generation

- Added authenticated random result endpoint through
  `/matches/{match_id}/generate-random-result`.
- Implemented `RandomResultService` to generate bounded scores, goals, assists
  through `assist_player_id`, saves, yellow cards, and red cards, then finish
  the match in one transaction.
- Added safeguards so random generation requires players for both teams,
  refuses finished/cancelled matches, refuses matches with existing protocol
  events, and avoids drawn generated results for cup semifinals/finals.
- Added random result tests for successful generation, protocol consistency,
  caps, missing players, existing protocol conflicts, finished-match rejection,
  missing matches, cup no-draw behavior, and JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/random_results.py`,
  `backend/app/api/v1/router.py`,
  `backend/app/services/random_result_service.py`,
  `backend/app/repositories/player.py`,
  `backend/app/schemas/random_result.py`, and
  `backend/tests/test_random_results.py`.
- Next steps: implement automatic lineup generation/replacement for suspended
  players or automatic standings/statistics recalculation after finish.

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

### Match CRUD And Scheduling Rules

- Added authenticated CRUD endpoints for matches, plus action endpoints for
  referee assignment, rescheduling, and manual ticket price changes.
- Implemented `MatchService`, calendar validation, referee parallel-match
  validation, and default ticket price calculation.
- Added match tests for successful creation, missing related entities, calendar
  conflicts, referee conflicts, manual ticket price override, rescheduling, and
  JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/matches.py`,
  `backend/app/services/match_service.py`,
  `backend/app/services/schedule_service.py`,
  `backend/app/services/ticket_price_service.py`,
  `backend/app/services/validation_service.py`,
  `backend/app/repositories/match.py`, `backend/app/repositories/team.py`,
  `backend/app/schemas/match.py`, `backend/app/utils/datetime_utils.py`,
  and `backend/tests/test_matches.py`.
- Next steps: implement lineup management and match protocol submission.

### Match Lineup Management

- Added authenticated lineup endpoints for listing and adding players through
  `/matches/{match_id}/lineups`, and reading, updating, deleting lineup entries
  through `/lineups/{lineup_id}`.
- Implemented `LineupService` with validation for match existence, participant
  teams, player-team membership, duplicate players, duplicate team numbers, and
  basic red-card/five-yellow-card suspension checks.
- Added lineup repository helpers and event lookup helpers used by suspension
  validation.
- Added lineup tests for CRUD, invalid teams, wrong-team players, duplicate
  players, duplicate numbers, suspended players, and JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/lineups.py`,
  `backend/app/api/v1/router.py`, `backend/app/services/lineup_service.py`,
  `backend/app/repositories/match_lineup.py`,
  `backend/app/repositories/match_event.py`, `backend/app/repositories/match.py`,
  `backend/app/schemas/match_lineup.py`, and `backend/tests/test_lineups.py`.
- Next steps: implement match protocol submission so events can be entered
  through the API instead of direct persistence helpers.

### Match Protocol Submission

- Added authenticated protocol endpoints for listing and adding match events
  through `/matches/{match_id}/events`, reading, updating, deleting events
  through `/events/{event_id}`, and finishing matches through
  `/matches/{match_id}/finish`.
- Implemented `MatchProtocolService` with validation for participant teams,
  player-team membership, optional assist players, immutable finished/cancelled
  protocols, and final score consistency with recorded goal events.
- Extended match event schemas and repository helpers for event ordering and
  goal counting.
- Added protocol tests for successful goal/card entry, event correction and
  deletion, invalid teams, wrong-team players, wrong-team assists, successful
  finish, score mismatch, finished-match mutation, and JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/protocol.py`,
  `backend/app/api/v1/router.py`,
  `backend/app/services/match_protocol_service.py`,
  `backend/app/repositories/match_event.py`,
  `backend/app/schemas/match_event.py`, and
  `backend/tests/test_match_protocol.py`.
- Next steps: implement standings recalculation from finished matches.

### Standings Recalculation

- Added authenticated standings endpoints for reading a season table through
  `/standings/seasons/{season_id}` and recalculating it through
  `/standings/seasons/{season_id}/recalculate`.
- Implemented `StandingsService` to rebuild `TeamSeasonStats` from finished
  championship matches, excluding cup matches from league standings.
- Added ranking by points, goal difference, goals scored, and stable `team_id`
  tie-breaker.
- Added standings tests for recalculation, cup exclusion, idempotency, missing
  seasons, and JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/standings.py`,
  `backend/app/services/standings_service.py`,
  `backend/app/repositories/stats.py`, `backend/app/repositories/match.py`, and
  `backend/tests/test_standings.py`.
- Next steps: implement player season statistics and leaderboards from match
  protocol events.

### Player Statistics And Leaderboards

- Added authenticated player statistics endpoints for reading season totals
  through `/statistics/seasons/{season_id}/players`, recalculating them through
  `/statistics/seasons/{season_id}/players/recalculate`, and reading
  leaderboards through `/statistics/seasons/{season_id}/leaders/{metric}`.
- Implemented `StatisticsService` to rebuild `PlayerSeasonStats` from events in
  finished matches.
- Added leaderboard support for goals, assists, saves, yellow cards, and red
  cards.
- Added statistics tests for recalculation, ignoring unfinished matches,
  idempotency, leaderboards, unsupported metrics, missing seasons, and JWT
  requirements.
- Changed files: `backend/app/api/v1/endpoints/statistics.py`,
  `backend/app/services/statistics_service.py`,
  `backend/app/repositories/stats.py`, `backend/app/repositories/match_event.py`,
  and `backend/tests/test_statistics.py`.
- Next steps: implement automatic championship schedule generation and schedule
  views.

### Championship Schedule Generation

- Added authenticated schedule endpoints for generating championship double
  round-robin fixtures through `/schedule/championships/{tournament_id}/generate`
  and reading season/stadium match schedules.
- Extended `ScheduleService` to create all generated matches in one transaction,
  validate existing team calendar limits, assign home stadiums or configured
  fallback stadiums, and calculate default ticket prices.
- Added schedule tests for four-team double round-robin generation, home/away
  pair accounting, non-championship rejection, missing resources, existing
  calendar conflicts, schedule views, and JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/schedule.py`,
  `backend/app/services/schedule_service.py`,
  `backend/app/repositories/match.py`, `backend/app/repositories/stadium.py`,
  `backend/app/schemas/schedule.py`, and `backend/tests/test_schedule.py`.
- Next steps: implement cup creation/bracket flow or random result generation.

### Cup Bracket Flow

- Added authenticated cup endpoints for generating semifinals through
  `/cups/{tournament_id}/semifinals`, generating the final through
  `/cups/{tournament_id}/final`, and reading bracket state through
  `/cups/{tournament_id}/bracket`.
- Implemented `CupService` to validate cup tournaments, accept four unique
  selected teams, create seeded semifinal pairings, derive final participants
  from finished semifinal winners, reject drawn semifinals, and report bracket
  winners/champion.
- Reused existing match calendar constraints and ticket price calculation for
  generated cup matches.
- Added cup tests for the full semifinal/final/bracket flow, missing resources,
  wrong tournament type, duplicate teams, existing calendar conflicts,
  unfinished/drawn semifinals, and JWT requirements.
- Changed files: `backend/app/api/v1/endpoints/cups.py`,
  `backend/app/api/v1/router.py`, `backend/app/services/cup_service.py`,
  `backend/app/repositories/match.py`, `backend/app/schemas/cup.py`, and
  `backend/tests/test_cups.py`.
- Next steps: implement random result generation or automatic lineup generation.
