# Project Context

## Goal

The project is a backend system for organizers of a national football
competition. It should support a league-style championship and a cup tournament
within seasons, while keeping schedules, teams, players, stadiums, referees,
match protocols, ticket prices, standings, and player statistics consistent.

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

## Business Constraints

- A team cannot play more than one match per day.
- A team cannot play more than two matches per week.
- A week is counted from Monday through Sunday.
- Calendar limits include both championship and cup matches.
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
- Players with five accumulated yellow cards or a red card miss the next match.
- Match lineups can include only players from one of the match participant
  teams, and a player cannot be added to the same match lineup twice.
- A team lineup for one match cannot contain duplicate shirt numbers.
- Match protocol events can be recorded only for match participant teams and
  their players.
- A match can be finished only when the submitted final score matches recorded
  goal events.
- Automatic lineup generation must replace unavailable players with eligible
  teammates where possible.
- Random match result generation must use realistic limits so scores and cards
  stay plausible.
- The cup consists of semifinals and a final.
- The cup uses the first four teams from the previous season. If there is no
  previous season, the organizer selects teams manually.
- Players are stored through `Player.team_id`, not as arrays inside a team.
- Match participants are stored as `home_team_id` and `away_team_id`.
- Match lineups and match protocol events are stored in separate tables.
- Team and player statistics should be recalculated by services, not manually
  duplicated across unrelated entities.

## MVP

- Organizer registration and JWT login.
- CRUD for teams, players, stadiums, referees, seasons, and tournaments.
- Championship creation.
- Cup tournament creation for four teams.
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
- Match schedule and stadium schedule views.
- Cup bracket view.

## Not In MVP

- Online ticket payments.
- Mobile application.
- External sports APIs.
- News, posts, and publishing workflows.
- Complex user role hierarchy.

## Current Iteration

The current backend includes FastAPI setup, settings, database connection,
SQLAlchemy models, Pydantic schemas, Alembic configuration, PostgreSQL Docker
Compose setup, JWT auth, initial schema migration, CRUD for seasons, teams,
players, stadiums, referees, tournaments, matches, and match lineups, plus match
calendar validation, referee assignment validation, ticket price
calculation/manual override, and suspension checks when adding players to
lineups. Match protocol endpoints can record events and finish matches with
score validation against recorded goals.

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
