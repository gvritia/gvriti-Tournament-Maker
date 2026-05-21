# Development Log

## 2026-05-21

### Generation Smoke Stabilization And Regression Tests

- Frontend API requests now support per-action timeouts. Long-running generation
  actions use longer timeouts:
  - one-match protocol generation: 30 seconds;
  - championship schedule and cup semifinal generation: 60 seconds;
  - full-season protocol generation: 120 seconds.
- This fixes the UI symptom where full-season generation could show a false
  connection error while the backend continued and finished the operation.
- Verified the running demo API returns 8 demo referees for `demo@example.com`.
- Added backend regression coverage for:
  - season generation skipping cancelled matches;
  - next-match protocol generation using substitute players after a red-card
    suspension;
  - invalid existing lineups blocking protocol generation clearly;
  - missing goalkeepers blocking protocol generation clearly;
  - missing referees blocking full-season generation without partial protocol
    writes.
- Verification:
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_random_results.py -q`
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py backend/tests/test_random_results.py -q`
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_lineups.py backend/tests/test_cups.py -q`
  - `.venv\Scripts\python.exe -m ruff check backend/app backend/tests`
  - `.venv\Scripts\python.exe -m black --check backend/tests/test_random_results.py`
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`
- Note: full `black --check backend/app backend/tests` still reports
  pre-existing formatting drift in `backend/tests/test_crud.py`; this slice did
  not reformat that unrelated file.

### Match Detail Protocol Generation Error UX

- No backend changes in this slice. Static analysis only:
  - `RandomResultService` continues to auto-assign an available referee,
    auto-generate missing starting lineups with exactly one goalkeeper, and
    refuse only finished/cancelled/already-protocolled matches when called as
    single-match generation.
  - `RandomResultService._should_generate_in_season` continues to skip
    finished, cancelled, and already-protocolled matches during full-season
    simulation.
  - `CupService._find_available_match_datetime` continues to search forward
    up to 120 days for a free `match_datetime` so a same-day or weekly limit
    conflict shifts the semifinal forward rather than failing.
  - `LineupService._select_players_for_generated_lineup` continues to drop
    suspended players and refill from eligible teammates.
  - `StarterDataService` continues to seed 18 players per team (2 GK + 16
    field) but does not seed starter referees. Demo seed seeds 8 referees via
    `_upsert_referees`.
- Frontend UX changes (see `docs/FRONTEND_DEVELOPMENT_LOG.md`) make a
  starter user's missing-referee state visible before the failing backend
  call, and surface the `400/409` protocol generation errors on
  `/app/matches/:matchId` instead of swallowing them.
- Verification:
  - static analysis only;
  - `.venv\Scripts\python.exe -m pytest`, `ruff`, and `black` were not run
    in this slice because the slice did not change backend code; the user
    should still run the standard backend command set after pulling to be
    safe.

## 2026-05-17

### Starter Squad Depth For Protocol Generation

- Expanded starter player data for newly registered organizers from 11 to 18
  players per team.
- Each starter team now receives two goalkeepers and sixteen field players, so
  protocol generation still has enough eligible field players after normal
  one-match suspensions from red cards or accumulated yellow cards.
- Backfilled the running Docker PostgreSQL starter/test accounts that had 20
  starter teams and 220 players up to 360 players. Demo data with 675 imported
  real squad players was left unchanged.
- Verified:
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py -q`
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_random_results.py -q`
  - `.venv\Scripts\python.exe -m ruff check backend/app/services/starter_data_service.py backend/tests/test_auth.py`
  - `.venv\Scripts\python.exe -m black --check backend/app/services/starter_data_service.py backend/tests/test_auth.py`
  - `docker compose build --pull=false backend`
  - `docker compose up -d --no-build backend`
  - live Docker API smoke: newly registered user received 360 players, a
    second match protocol generated successfully after a red-card suspension in
    the previous match, and the suspended player was not selected; the
    temporary user was deleted.

### Season Simulation Remaining Matches

- Changed full-season protocol generation so it can continue after some season
  matches are already finished.
- Season simulation now skips finished matches, cancelled matches, and matches
  that already have protocol events, then generates protocols/results only for
  the remaining clean matches in one transaction.
- Existing one-match generation remains strict: it still rejects finished,
  cancelled, or already-protocolled matches.
- Updated the championship UI confirmation/success text so users see that the
  action generates remaining unfinished matches and leaves existing results
  unchanged.
- Added regression tests for skipping finished matches and skipping matches
  with existing protocol events while still generating the rest.
- Verified:
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_random_results.py -q`
  - `.venv\Scripts\python.exe -m ruff check backend/app/services/random_result_service.py backend/tests/test_random_results.py`
  - `.venv\Scripts\python.exe -m black --check backend/app/services/random_result_service.py backend/tests/test_random_results.py`
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false backend frontend`
  - `docker compose up -d --no-build backend frontend`
  - live Docker API smoke: one already-finished match was skipped, one
    remaining match was generated and finished, then the temporary user was
    deleted.

### Cup Semifinal Auto-Scheduling

- Fixed cup semifinal generation so selected semifinal datetimes are treated as
  preferred slots instead of hard failures.
- `CupService` now searches forward from each requested semifinal datetime and
  uses the nearest date at the same time that satisfies the team one-match-per-
  day and two-matches-per-week limits.
- Added regression coverage for moving a semifinal away from a same-day
  conflict and for moving it past a weekly match-limit conflict.
- Added a frontend-friendly translation for the rare case where no available
  cup match date is found during the search window.
- Verified:
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_cups.py -q`
  - `.venv\Scripts\python.exe -m ruff check backend/app/services/cup_service.py backend/tests/test_cups.py`
  - `.venv\Scripts\python.exe -m black --check backend/app/services/cup_service.py backend/tests/test_cups.py`
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false backend frontend`
  - `docker compose up -d --no-build backend frontend`
  - live Docker API smoke: cup semifinal generation returned `201 Created` and
    moved a conflicting preferred semifinal date to the next valid day, then
    the temporary user was deleted.

### Starter Players For New Organizers

- Expanded starter data for newly registered organizers so the backend now
  creates starter players for each starter LaLiga team, in addition to teams,
  stadiums, previous-season places, manager names, and logo URLs.
- Each starter team now receives two goalkeepers and sixteen field players,
  making the players page, lineup generation, and protocol generation usable
  immediately without a separate demo CSV import.
- Updated the auth registration test to verify starter player creation.
- Backfilled the running Docker PostgreSQL test data for existing starter-style
  accounts that had 20 teams and zero players; demo data with imported real
  squads was left unchanged.
- Updated the frontend dashboard onboarding notice so it mentions starter
  players as part of the preloaded workspace data.
- Verified:
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py -q`
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py backend/tests/test_crud.py backend/tests/test_owner_scope.py backend/tests/test_lineups.py backend/tests/test_random_results.py -q`
  - `.venv\Scripts\python.exe -m ruff check backend/app/services/starter_data_service.py backend/tests/test_auth.py backend/tests/test_random_results.py`
  - `.venv\Scripts\python.exe -m black --check backend/app/services/starter_data_service.py backend/tests/test_auth.py backend/tests/test_random_results.py`
  - `docker compose build --pull=false backend`
  - `docker compose up -d --no-build backend`
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`
  - live Docker API smoke: newly registered user received 20 teams and 360
    players, then the temporary user was deleted.

### Backend Acceptance Stabilization

- Added backend protocol-generation endpoints for one-match and full-season
  simulation:
  `/matches/{match_id}/generate-protocol` and
  `/seasons/{season_id}/generate-protocols`.
- Kept the existing one-match random-result endpoint as a compatible alias and
  reused the same generate-and-finish business workflow for protocol generation.
- Expanded protocol generation so it now auto-assigns an available referee when
  missing, generates missing starting lineups for both teams, requires exactly
  one goalkeeper in each starting lineup, and generates events from lineup
  players.
- Added full-season simulation tests that verify all season matches are
  finished with protocol events, standings/statistics refresh, JWT protection,
  and rollback/no partial generation when a match already has protocol events.
- Added optional `emblem_url` support for teams, with HTTP/HTTPS API validation
  and an Alembic migration.
- Added acceptance-focused backend tests for automatic lineup goalkeeper
  selection, finished-match immutability, direct `PATCH status=finished`
  rejection, and cup semifinal stadium resolution.
- Fixed automatic lineup generation so generated starters contain exactly one
  goalkeeper when an eligible goalkeeper exists. Preferred players are still
  honored where possible, but extra goalkeepers are moved out of the starting
  lineup and a goalkeeper is promoted into the starting lineup when needed.
- Fixed normal match edit workflows so finished matches cannot be patched,
  rescheduled, assigned a referee, have ticket price changed, or be deleted.
  Direct generic updates to `status=finished` are rejected; matches must finish
  through protocol finish or random result generation.
- Fixed cup semifinal generation so only the two home seeds in `1 vs 4` and
  `2 vs 3` need stadium resolution. Away seeds no longer need home stadiums for
  those fixtures when no fallback is supplied.
- Resolved the current random-result product decision for the MVP: the backend
  keeps random result as an explicit generate-and-finish action, not a draft
  workflow.
- Verified backend with `.venv\Scripts\python.exe -m pytest`,
  `.venv\Scripts\python.exe -m ruff check .`, and
  `.venv\Scripts\python.exe -m black --check .`.

### Backend Stabilization And Frontend Rebuild Planning

- Added `docs/ACCEPTANCE_CASES.md` with acceptance checks for auth, startup,
  ownership isolation, CRUD, matches, ticket prices, schedule generation,
  lineups, protocol finishing, random results, standings, statistics, cup, and
  frontend UX.
- Added `docs/NEXT_CHAT_PROMPT.md` with a ready prompt for the next Codex chat:
  stabilize backend first with tests, then delete the current frontend draft and
  rebuild a simpler organizer workspace from scratch.
- Captured open product decisions around random-result behavior, mandatory
  lineups/protocol before finishing, starting-lineup rules, and frontend
  rebuild strategy.

## 2026-05-11

### Frontend First Pass

- Added the first React/Vite/TypeScript frontend in `frontend/` with React
  Router, TanStack Query, lucide icons, and dark-only plain CSS inspired by the
  Tournify tournament page reference.
- Added frontend context documents:
  `docs/FRONTEND_CONTEXT.md`, `docs/FRONTEND_ARCHITECTURE.md`,
  `docs/FRONTEND_DEVELOPMENT_LOG.md`, and
  `docs/FRONTEND_REFERENCE_TOURNIFY.md`.
- Implemented JWT auth screens, protected app shell, dashboard, CRUD screens,
  match schedule/detail workflows, lineups, protocol events, championship
  standings/statistics/schedule generation, and cup bracket/generation screens.
- Verified frontend build with `npm run build` and dependency audit with
  `npm audit`.
- Local dev server runs on `http://127.0.0.1:5173`.
- Backend was not running during frontend verification, so the real demo login
  flow remains the next check.

## 2026-05-10

### Final Backend Polish

- Added a Docker backend service and `backend/Dockerfile` so PostgreSQL and the
  API can run together with `docker compose up --build backend`.
- Added local frontend CORS support through `CORS_ORIGINS` and OpenAPI tag
  descriptions for the implemented API areas.
- Added database-level owner-scoped uniqueness for stadium names, referee names,
  and tournament names inside one owner season.
- Expanded `backend/README.md` with a defense-ready API flow covering login,
  protected reads, random results, standings, statistics, and cross-user
  isolation.
- Verified the real PostgreSQL demo flow with LaLiga CSV seeding, compose
  backend startup, demo login, protected reads, cup bracket, random result,
  standings/statistics refresh, and second-user `404` isolation.
- Changed files: `docker-compose.yml`, `backend/Dockerfile`,
  `backend/.dockerignore`, `backend/app/core/config.py`, `backend/app/main.py`,
  `backend/app/models/referee.py`, `backend/app/models/stadium.py`,
  `backend/app/models/tournament.py`,
  `backend/alembic/versions/4f2a7b91c8e3_add_owner_unique_constraints.py`,
  `backend/tests/test_health.py`, `backend/README.md`, `AGENTS.md`,
  `docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`, and
  `docs/DEVELOPMENT_LOG.md`.
- Next steps: start frontend development against the stable authenticated API.

### User-Scoped Data Isolation

- Added `owner_id` ownership to all subject-area tables: seasons, teams,
  players, stadiums, referees, tournaments, matches, match lineups, match
  events, team season stats, and player season stats.
- Updated repositories, services, and endpoints so all domain reads, writes,
  helper lookups, schedule generation, cup bracket operations, match protocols,
  random results, standings, and statistics run in the current user's scope.
- Changed season/team uniqueness to per-user scope and added an Alembic
  migration that backfills existing data to an owner.
- Updated demo data seeding to create or reuse a demo organizer and attach all
  seeded rows to that user.
- Added ownership tests for cross-user lists, CRUD access, duplicate names per
  user, foreign linked IDs, lineups/events, random results, schedule views,
  standings, statistics, cup brackets, and cup auto-selection.
- Added a README API defense flow for logging in, using the demo token, and
  demonstrating cross-user isolation.
- Changed files: `backend/app/models/*`, `backend/app/repositories/*`,
  `backend/app/services/*`, `backend/app/api/v1/endpoints/*`,
  `backend/alembic/versions/9d3f4e1a6b2c_add_owner_scope.py`,
  `backend/app/scripts/seed_demo_data.py`, `backend/tests/test_owner_scope.py`,
  `backend/tests/test_lineups.py`, `backend/tests/test_seed_demo_data.py`,
  `backend/README.md`, `AGENTS.md`, `docs/PROJECT_CONTEXT.md`,
  `docs/ARCHITECTURE.md`, and `docs/DEVELOPMENT_LOG.md`.
- Next steps: connect the future frontend to the authenticated user flow and
  use the demo seed command for a full defense walkthrough.

## 2026-05-09

### Demo Data Seeding

- Added `python -m app.scripts.seed_demo_data` to import parsed LaLiga club and
  squad CSV files into the backend database.
- The seed command creates a demo season, championship and cup tournaments,
  teams, home stadiums, players, referees, and cup semifinal fixtures.
- Added deterministic player number conflict handling for CSV rows where one
  team has duplicate shirt numbers.
- Added optional `--generate-championship-schedule` support for a full double
  round-robin demo calendar.
- Added tests for CSV parsing, idempotent seeding, duplicate player number
  handling, and cup semifinal generation from seeded previous-season places.
- Changed files: `backend/app/scripts/seed_demo_data.py`,
  `backend/app/scripts/__init__.py`, `backend/tests/test_seed_demo_data.py`,
  `backend/README.md`, `AGENTS.md`, `docs/PROJECT_CONTEXT.md`,
  `docs/ARCHITECTURE.md`, and `docs/DEVELOPMENT_LOG.md`.
- Next steps: add README/API flow for a full defense walkthrough.

### Schedule Filters, Cup Auto-Selection, And CI

- Added season schedule filters to
  `/schedule/seasons/{season_id}/matches`: `team_id`, `tournament_id`,
  `date_from`, and `date_to`.
- Added cup semifinal generation mode using the top four teams by
  `previous_season_place`, while preserving manual four-team selection when
  previous season places are missing.
- Added GitHub Actions backend CI for `pytest`, `ruff check .`,
  `black --check .`, and `alembic check` against PostgreSQL.
- Added tests for schedule filters, invalid schedule filters, cup automatic
  previous-season selection, and manual cup fallback with unranked teams.
- Changed files: `.github/workflows/backend-ci.yml`,
  `backend/app/api/v1/endpoints/schedule.py`,
  `backend/app/repositories/match.py`, `backend/app/repositories/team.py`,
  `backend/app/schemas/cup.py`, `backend/app/services/cup_service.py`,
  `backend/app/services/schedule_service.py`, `backend/tests/test_cups.py`,
  and `backend/tests/test_schedule.py`.
- Next steps: add seed/demo data and README/API flow for defense.

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

### Starter Team Data And Club Logos

- Added starter LaLiga team data for newly registered organizers. Registration
  now creates 20 teams with home stadiums, previous-season places, manager
  names, and `emblem_url` logo links before the registration transaction
  commits.
- Added `StarterDataService` so the starter data stays in the service layer and
  does not overwrite later user edits if invoked for an owner that already has
  teams.
- Extended the demo CSV importer to accept both semicolon-delimited and
  tab-delimited club/squad files.
- Added CSV encoding fallback for local parsed files that are not UTF-8.
- Mapped the demo club CSV `logo` column to `Team.emblem_url` and validate it as
  an HTTP/HTTPS URL.
- Added tests for registration starter teams/stadiums, logo import, and
  tab-delimited club CSV parsing.
- Updated cup and owner-scope tests that need empty organizer data to clear the
  starter teams/stadiums explicitly after registration.
- Changed files: `backend/app/services/auth_service.py`,
  `backend/app/services/starter_data_service.py`,
  `backend/app/scripts/seed_demo_data.py`, `backend/tests/test_auth.py`,
  `backend/tests/test_seed_demo_data.py`, `backend/tests/test_cups.py`, and
  `backend/tests/test_owner_scope.py`.
- Verified:
  - `pytest backend/tests/test_auth.py backend/tests/test_seed_demo_data.py`
  - `pytest backend/tests`
  - local demo seed rerun against Docker PostgreSQL; `demo@example.com` now has
    20 teams with 20 logo URLs.

### Season Rollover

- Added a backend season rollover action that creates a new owner-scoped season
  from an existing source season.
- The rollover can copy source tournaments into the new season; copied
  tournaments keep their name/type and reset to planned status.
- Teams, players, stadiums, and referees are intentionally reused from the
  organizer workspace instead of being cloned.
- Added owner-scope coverage so a user cannot roll over another user's season.
- Changed files: `backend/app/api/v1/endpoints/seasons.py`,
  `backend/app/schemas/season.py`,
  `backend/app/repositories/tournament.py`,
  `backend/app/services/season_rollover_service.py`,
  `backend/tests/test_crud.py`, and `backend/tests/test_owner_scope.py`.
- Verified:
  - `pytest backend/tests/test_crud.py backend/tests/test_owner_scope.py -q`
  - live Docker API smoke for demo rollover, followed by cleanup of temporary
    smoke seasons/tournaments.
