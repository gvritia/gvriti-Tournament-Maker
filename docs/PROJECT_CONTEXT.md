# Project Context

## Goal

The project is a backend system for organizers of a national football
competition. It should support a league-style championship and a cup tournament
within seasons, while keeping schedules, teams, players, stadiums, referees,
match protocols, ticket prices, standings, and player statistics consistent.
Each organizer works in an isolated data scope: one user's seasons, teams,
tournaments, matches, lineups, protocol events, standings, and statistics are
not visible or mutable by another user.

## Football Competition Description

The system stores clubs, their players and stadiums, seasons, tournaments, and
matches. A season can contain both a championship and a cup. The championship is
double round-robin: every team plays every other team twice, once at home and
once away. The cup is a short knockout tournament with semifinals and a final.

The schedule must prevent unrealistic overload: a team cannot play multiple
matches in one day and cannot play more than two matches in one week. These
checks must include both championship and cup matches.

## Main Entities

- `User`: organizer account with nickname, email, password hash, role, and
  creation timestamp.
- `Season`: competition period with name, dates, and status.
- `Team`: football club with city, address, manager, and previous season place.
  Teams can also store an optional `emblem_url` for the club badge.
- `TeamSeasonStats`: recalculated seasonal team standings data.
- `Player`: player connected to a team through `team_id`.
- `Stadium`: venue with capacity and optional home team.
- `Referee`: match official.
- `Tournament`: championship or cup inside a season.
- `Match`: scheduled or finished game with home team, away team, stadium,
  optional referee, score, ticket price, ticket sales, and income.
- `MatchLineup`: player participation and starting lineup for a match.
- `MatchEvent`: match protocol event such as goal, assist, save, yellow card, or
  red card.
- `PlayerSeasonStats`: recalculated player totals by season.
- New organizer accounts receive starter LaLiga team, player, and home-stadium
  data with club emblem URLs so the workspace is usable immediately. Demo seed
  data can also be imported from parsed LaLiga CSV files for clubs and squads.

All subject-area entities except `User` are owned by one organizer through
`owner_id`. API reads and writes always resolve these entities through the
current authenticated user.

## Business Constraints

- Domain data is isolated per authenticated user.
- Lists return only entities owned by the current user.
- Reading, updating, or deleting another user's entity returns missing-resource
  behavior instead of exposing the entity.
- Creating linked entities validates all referenced IDs inside the current
  user's data scope.
- Season names and team names are unique per user, not globally. Stadium names
  and referee names are also unique per user, and tournament names are unique
  inside one user's season.
- A team cannot play more than one match per day.
- A team cannot play more than two matches per week.
- A week is counted from Monday through Sunday.
- Calendar limits include both championship and cup matches.
- Championship schedule generation creates a double round-robin set of matches:
  every selected team plays every other selected team twice, one home match and
  one away match.
- Championship schedule generation uses a team's home stadium when available;
  otherwise the organizer must provide a team stadium mapping or fallback
  stadium.
- Season schedule views can be filtered by team, tournament, and inclusive date
  range.
- A referee cannot officiate parallel matches.
- Ticket price is calculated when a match is created and stays fixed unless the
  organizer changes it manually.
- Ticket price formula:
  `total_price = (base_price + capacity_factor) * club_coefficient`.
- `club_coefficient` is based on the participating clubs' table tier from the
  previous season: top third is `2.0`, middle third is `1.5`, bottom third is
  `1.1`.
- For a match, the default club coefficient uses the highest coefficient among
  the home and away teams.
- The current capacity factor tiers are `0.00` for stadiums below 10,000 seats,
  `5.00` from 10,000 seats, `10.00` from 30,000 seats, and `15.00` from 60,000
  seats.
- Ticket price can be changed manually for a specific match.
- Finished matches are immutable through normal match edit workflows: they
  cannot be patched, rescheduled, assigned a referee, have ticket price changed,
  or be deleted. Matches must be finished through the protocol finish workflow
  or through random result generation.
- Players with five accumulated yellow cards or a red card miss the next match.
- Match lineups can include only players from one of the match participant
  teams, and a player cannot be added to the same match lineup twice.
- A team lineup for one match cannot contain duplicate shirt numbers.
- Automatic lineup generation creates a lineup for one match participant team,
  can prioritize preferred players, skips suspended preferred players, and fills
  open slots with eligible teammates where possible.
- Automatic lineup generation guarantees exactly one starting goalkeeper when
  an eligible goalkeeper exists; if that valid starting lineup cannot be formed,
  generation returns a clear conflict.
- Automatic lineup generation does not overwrite an existing team lineup unless
  the organizer explicitly asks to replace it.
- Match protocol events can be recorded only for match participant teams and
  their players.
- A match can be finished only when the submitted final score matches recorded
  goal events.
- Championship standings are recalculated from finished championship matches.
  Cup matches do not affect league standings.
- Standings order uses points, goal difference, goals scored, and then `team_id`
  as a stable final tie-breaker.
- Player season statistics are recalculated from events in finished matches.
- Finishing a match through protocol submission or random result generation
  automatically refreshes player season statistics for that season.
- Finishing a championship match through protocol submission or random result
  generation automatically refreshes championship standings for that season.
- Finishing a cup match refreshes player season statistics, but does not affect
  championship standings.
- Assist totals include explicit `assist` events and `assist_player_id` recorded
  on goal events.
- Automatic lineup generation must replace unavailable players with eligible
  teammates where possible.
- Random match result generation must use realistic limits so scores and cards
  stay plausible.
- Random match result generation is an explicit generate-and-finish workflow for
  the current MVP: it creates goal, save, yellow-card, and red-card protocol
  events, then marks the match as finished with a matching final score.
- Random match result generation requires both teams to have players, does not
  overwrite existing protocol events, and cannot run for finished or cancelled
  matches.
- Protocol generation is available for a single match and for a whole season.
  Protocol generation auto-fills missing referee assignment and both teams'
  starting lineups, uses lineup players for generated events, and sets the final
  score/status. Season simulation generates remaining clean matches in one
  transaction, skipping finished matches, cancelled matches, and matches that
  already have protocol events. It refreshes standings/statistics once and
  rolls back if any remaining generated match lacks an available referee or
  cannot form valid lineups.
- Randomly generated scores are capped at five goals per team. Generated cards
  are capped at five yellow cards and one red card per team, and saves are
  capped at ten per team.
- Randomly generated cup semifinal/final results must have a clear winner.
- The cup consists of semifinals and a final.
- The cup can use the first four teams by `previous_season_place`. If previous
  season places are missing, the organizer selects teams manually.
- Cup semifinal generation accepts exactly four unique teams, creates seeded
  pairings `1 vs 4` and `2 vs 3`, and assigns stadiums through home stadiums,
  explicit team mapping, or a fallback stadium for the two home seeds.
- Cup semifinal generation treats submitted datetimes as preferred start slots:
  if a selected team is already busy that day or has reached the weekly match
  limit, the service searches forward for the nearest valid date at the same
  time instead of failing immediately.
- Cup final generation requires two finished semifinals with clear winners.
  Drawn semifinals must be resolved before the final can be created.
- Cup bracket view returns semifinal matches, final match when created, match
  winners, and champion after the final is finished.
- Players are stored through `Player.team_id`, not as arrays inside a team.
- Match participants are stored as `home_team_id` and `away_team_id`.
- Match lineups and match protocol events are stored in separate tables.
- Team and player statistics should be recalculated by services, not manually
  duplicated across unrelated entities.

## MVP

- Organizer registration and JWT login.
- CRUD for teams, players, stadiums, referees, seasons, and tournaments.
- Optional club emblem URLs on teams.
- Championship creation.
- Cup tournament creation for four teams, either manually or from previous
  season places.
- Automatic championship schedule generation.
- Home and away match accounting.
- Match moving with calendar validation.
- Referee assignment with parallel-match validation.
- Match lineup management.
- Ticket price calculation and manual override.
- Player suspension checks for lineups.
- Random match result generation with realistic bounds.
- Match protocol submission with score, goals, assists, saves, and cards.
- Standings recalculation.
- Player statistics and leaderboards for goals, assists, saves, yellow cards,
  and red cards.
- Match schedule and stadium schedule views, including season schedule filters
  by team, tournament, and date range.
- Cup bracket view.
- Demo data seeding from parsed club and squad CSV files.
- Starter team, player, and home-stadium data after organizer registration.
- Season rollover that creates a next season and optionally copies tournaments
  while reusing the organizer's teams, players, stadiums, and referees.
- User-scoped data isolation for all domain entities and derived tables.

## Not In MVP

- Online ticket payments.
- Mobile application.
- External sports APIs.
- News, posts, and publishing workflows.
- Complex user role hierarchy.

## Current Iteration

The current backend includes FastAPI setup, settings, database connection,
SQLAlchemy models, Pydantic schemas, Alembic configuration, PostgreSQL Docker
Compose setup with optional backend service, JWT auth, initial schema migration,
CRUD for seasons, teams,
players, stadiums, referees, tournaments, matches, and match lineups, plus match
calendar validation, referee assignment validation, ticket price
calculation/manual override, and suspension checks when adding players to
lineups. Match protocol endpoints can record events and finish matches with
score validation against recorded goals. Standings endpoints can recalculate and
return the championship table for a season. Player statistics endpoints can
recalculate season totals and return leaderboards for goals, assists, saves,
yellow cards, and red cards. Schedule endpoints can generate double round-robin
championship matches, return stadium match schedules, and return season match
schedules filtered by team, tournament, and date range. Cup endpoints can
generate semifinals from four selected teams or automatically from the top four
teams by previous season place, generate the final from finished semifinal
winners, and return a bracket view. Random result generation can create bounded
protocol events and finish scheduled matches automatically. Lineup endpoints can
also generate an eligible match lineup automatically.
Finishing a match through either protocol submission or random result generation
automatically refreshes player statistics for the season and refreshes
championship standings when the match belongs to the championship.
Random protocol generation is exposed both for one match and for a full-season
simulation action that fills all existing season match protocols/results in one
transaction, including missing referees and generated lineups when valid data is
available.
Season rollover is available for organizers who need to start a new season
without re-entering the same workspace data. Teams, players, stadiums, and
referees remain user-scoped reusable resources; the rollover action creates a
new season and can copy the source season's tournaments into it with planned
status.
All domain repositories, services, and endpoints now operate in the current
user's `owner_id` scope, including linked-resource validation and derived
standings/statistics reads.
The backend also includes starter data creation for newly registered organizers:
20 LaLiga teams are created with home stadiums, previous-season places, manager
names, `emblem_url` logo links, and 18 starter players per team. The starter
players include two goalkeepers and sixteen field players so roster pages,
lineup generation, protocol generation, and follow-up matches after
disciplinary suspensions can be tested immediately. The demo seed
command imports parsed LaLiga club and squad CSV files, creates or reuses a demo
organizer account, and attaches the demo season, championship, cup, teams,
stadiums, players, referees, and cup semifinal fixtures to that user, with an
optional full championship schedule. The demo CSV importer accepts
semicolon-delimited or tab-delimited files, handles UTF-8 and common legacy
single-byte CSV encodings, and maps the source `logo` column into
`Team.emblem_url`.
Local frontend origins on ports `3000` and `5173` are allowed through CORS for
the next development stage.

The frontend now exists as a Vite/React/TypeScript single-page application in
`frontend/`. It uses React Router, TanStack Query, a shared API client for
`http://127.0.0.1:8000/api/v1`, JWT token persistence, protected routes, and a
dark-only Tournify-inspired interface. The first frontend pass includes auth,
dashboard, CRUD screens, match schedule/detail workflows, lineups, protocol
events, match finishing/random result actions, championship standings and
leaderboards, championship schedule generation, cup semifinal/final generation,
and a cup bracket view. Docker Compose can now run PostgreSQL, backend, and the
frontend dev server together from the repository root.

The next agreed work should continue frontend polish in small verified layers:
finish human-friendly validation/error states for remaining workflows, then run
a focused mobile smoke after each visible layout change.

## API Conventions

- Successful reads: `200 OK`.
- Successful resource creation: `201 Created`.
- Successful login/action without new resource: `200 OK`.
- Successful deletion: `204 No Content`.
- Validation errors: `422 Unprocessable Entity`.
- Missing or invalid JWT: `401 Unauthorized`.
- Authenticated but forbidden action: `403 Forbidden`.
- Missing entity: `404 Not Found`.
- Duplicate entity or violated calendar/resource conflict: `409 Conflict`.
- Other malformed business request: `400 Bad Request`.
