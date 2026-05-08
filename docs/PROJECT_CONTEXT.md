# Project Context

## Goal

The project is a backend system for organizers of a national football
competition. It should support a league-style championship and a cup tournament
within seasons, while keeping schedules, teams, players, stadiums, referees,
match protocols, ticket prices, standings, and player statistics consistent.

## Football Competition Description

The system stores clubs, their players and stadiums, seasons, tournaments, and
matches. A season can contain both a championship and a cup. The championship
uses home and away matches. The cup is a short knockout tournament with
semifinals and a final.

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
- Calendar limits include both championship and cup matches.
- A referee cannot officiate parallel matches.
- Ticket price depends on stadium capacity and the teams' previous season
  places.
- Ticket price can be changed manually for a specific match.
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

The current iteration creates only the backend architecture skeleton. It includes
FastAPI setup, settings, database connection, SQLAlchemy models, Pydantic
schemas, Alembic configuration, repository and service placeholders, Docker
Compose for PostgreSQL, healthcheck test, and project documentation.
