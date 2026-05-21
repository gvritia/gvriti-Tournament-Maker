# Acceptance Cases

This file captures the acceptance checklist for the next stabilization pass.
Use it before rewriting the frontend: backend behavior should be made explicit
and covered by tests first, then the frontend can be rebuilt against stable
contracts.

## Auth And Startup

- `AC-AUTH-01`: A user can register with nickname, email, and password.
- `AC-AUTH-02`: A user can log in with email/password and receive a JWT.
- `AC-AUTH-03`: Invalid credentials return a clear error without breaking the
  UI.
- `AC-AUTH-04`: Logout clears the token and user-scoped data.
- `AC-AUTH-05`: Protected API endpoints and protected frontend pages are not
  accessible without JWT credentials.
- `AC-ENV-01`: The full project starts with `docker compose up --build` from
  the repository root.
- `AC-ENV-02`: The frontend is available at `http://127.0.0.1:5173`, and the
  backend is available at `http://127.0.0.1:8000`.
- `AC-ENV-03`: Demo seed creates a demo user and complete demo data for manual
  verification.

## User Isolation

- `AC-OWNER-01`: A user sees only their own seasons, teams, players, matches,
  standings, and statistics.
- `AC-OWNER-02`: A user cannot create or update a resource using another user's
  team, stadium, tournament, player, referee, lineup, event, or season.
- `AC-OWNER-03`: Opening another user's resource returns missing/forbidden
  behavior without leaking data.
- `AC-OWNER-04`: After logout and login as another user, stale user-scoped data
  is not visible in the UI.

## CRUD

- `AC-CRUD-01`: Seasons CRUD works end to end.
- `AC-CRUD-02`: Teams CRUD works end to end.
- `AC-CRUD-02A`: A team can store an optional club emblem URL, and invalid
  emblem URLs are rejected.
- `AC-CRUD-03`: Players CRUD works end to end, and every player is linked
  through `team_id`.
- `AC-CRUD-04`: Stadiums CRUD works end to end, including optional home-team
  assignment.
- `AC-CRUD-05`: Referees CRUD works end to end.
- `AC-CRUD-06`: Tournaments CRUD works end to end.
- `AC-CRUD-07`: Unique conflicts are displayed clearly.
- `AC-CRUD-08`: Large tables do not silently show only the first 100 rows;
  they use pagination, filters, or full paged loading where appropriate.

## Season Rollover

- `AC-SEASON-ROLL-01`: A user can create a next season from one of their own
  seasons without re-entering teams, players, stadiums, or referees.
- `AC-SEASON-ROLL-02`: Teams, players, stadiums, and referees remain shared
  organizer workspace data and are not cloned during rollover.
- `AC-SEASON-ROLL-03`: When tournament copy is enabled, source tournaments are
  copied into the new season with the same name/type and planned status.
- `AC-SEASON-ROLL-04`: When tournament copy is disabled, only the new season is
  created.
- `AC-SEASON-ROLL-05`: A user cannot roll over another user's season.
- `AC-SEASON-ROLL-06`: Duplicate target season names return a clear conflict.

## Matches And Ticket Prices

- `AC-MATCH-01`: A match can be created only with season, tournament, home team,
  away team, stadium, and datetime.
- `AC-MATCH-02`: Home team and away team cannot be the same team.
- `AC-MATCH-03`: Backend calculates `ticket_price` immediately when a match is
  created.
- `AC-MATCH-04`: Generated matches also have calculated `ticket_price`.
- `AC-MATCH-05`: Frontend shows ticket price in match list and match detail.
- `AC-MATCH-06`: Ticket price can be manually changed.
- `AC-MATCH-07`: Rescheduling a match preserves a manually set ticket price.
- `AC-MATCH-08`: A match cannot be created directly with `finished` status.
- `AC-MATCH-09`: A finished match cannot be edited or deleted unless there is an
  explicit supported workflow.

## Calendar Constraints

- `AC-SCHED-01`: A team cannot play more than one match per day.
- `AC-SCHED-02`: A team cannot play more than two matches per week.
- `AC-SCHED-03`: Championship and cup matches both count toward calendar
  limits.
- `AC-SCHED-04`: A referee cannot be assigned to parallel matches.
- `AC-SCHED-05`: Calendar/referee conflicts return `409 Conflict`.

## Championship Schedule Generation

- `AC-CH-SCHED-01`: A user can select a championship tournament and teams.
- `AC-CH-SCHED-02`: Schedule generation creates a double round-robin: each team
  plays every other team at home and away.
- `AC-CH-SCHED-03`: For `N` teams, generation creates `N * (N - 1)` matches.
- `AC-CH-SCHED-04`: Each round receives a valid scheduled datetime.
- `AC-CH-SCHED-05`: A team's home stadium is used automatically when present.
- `AC-CH-SCHED-06`: If a home stadium is missing, explicit team-stadium mapping
  or fallback stadium is used.
- `AC-CH-SCHED-07`: If generation cannot satisfy calendar limits, it rolls back
  and does not create partial garbage.
- `AC-CH-SCHED-08`: Frontend shows a clear reason when generation fails.
- `AC-CH-SCHED-09`: There is a clear function to generate the full schedule,
  not only one match.

## Lineups

- `AC-LINEUP-01`: Manual lineup entry can include only players from the match
  participant teams.
- `AC-LINEUP-02`: A player cannot be added twice to the same match lineup.
- `AC-LINEUP-03`: One team cannot have duplicate shirt numbers in one match.
- `AC-LINEUP-04`: A suspended player cannot be added to a lineup.
- `AC-LINEUP-05`: Automatic lineup generation creates the requested lineup
  size.
- `AC-LINEUP-06`: The generated starting lineup must contain exactly one
  goalkeeper when an eligible goalkeeper exists.
- `AC-LINEUP-07`: The generated starting lineup must not contain multiple
  goalkeepers unless there is an explicit accepted rule for that case.
- `AC-LINEUP-08`: If a valid starting lineup cannot be generated, backend
  returns a clear business error.
- `AC-LINEUP-09`: Automatic lineup generation does not overwrite an existing
  team lineup unless `replace_existing=true`.

## Match Protocol And Finish

- `AC-PROTO-01`: A match event can be recorded only for a player from a match
  participant team.
- `AC-PROTO-02`: Assist player must belong to the same team as the scorer.
- `AC-PROTO-03`: A finished match protocol cannot be edited.
- `AC-FINISH-01`: A match cannot be finished without a valid final score.
- `AC-FINISH-02`: Final score must match the number of recorded goal events.
- `AC-FINISH-03`: If protocol or lineup data is required by the agreed rules,
  backend rejects finish until that data exists.
- `AC-FINISH-04`: Frontend disables or blocks finish while required fields are
  missing.
- `AC-FINISH-05`: Backend validates finish independently of frontend checks.

## Random Result

- `AC-RANDOM-01`: Random result cannot run for finished or cancelled matches.
- `AC-RANDOM-02`: Random result cannot run when protocol events already exist.
- `AC-RANDOM-03`: Random result requires players for both teams.
- `AC-RANDOM-04`: Generated scores stay within realistic bounds.
- `AC-RANDOM-05`: Generated protocol events match the generated score.
- `AC-RANDOM-06`: Cup semifinal/final random result must produce a winner.
- `AC-RANDOM-07`: Current MVP decision: random result is an explicit
  generate-and-finish action that immediately marks the match as `finished`.
- `AC-RANDOM-08`: Draft random-result mode is out of scope unless a later
  product decision adds a separate draft endpoint.
- `AC-RANDOM-09`: Backend exposes a clear one-match protocol generation action
  that fills protocol events, final score, referee assignment, generated
  lineups, and finished status.
- `AC-RANDOM-10`: Backend exposes a one-click season simulation action that
  generates protocols/results for every match in a season in one transaction.
- `AC-RANDOM-11`: Season simulation skips finished, cancelled, and
  already-protocolled matches, then generates only the remaining clean matches.
- `AC-RANDOM-12`: Protocol generation uses players from match lineups and
  requires each starting lineup to contain exactly one goalkeeper.

## Championship Standings

- `AC-STAND-01`: Standings are calculated only from finished championship
  matches.
- `AC-STAND-02`: Cup matches do not affect championship standings.
- `AC-STAND-03`: Standings include place, team, played, wins, draws, losses,
  goals for, goals against, goal difference, and points.
- `AC-STAND-04`: Goals-for column shows total scored goals, not a match score
  string.
- `AC-STAND-05`: Goals-against has its own separate column.
- `AC-STAND-06`: Ordering uses points, goal difference, goals for, and then a
  stable tie-breaker.
- `AC-STAND-07`: Standings refresh after protocol finish and random result.

## Player Statistics

- `AC-STATS-01`: Goals are counted from goal events.
- `AC-STATS-02`: Assists are counted from explicit assist events and
  `assist_player_id` on goal events.
- `AC-STATS-03`: Saves are counted from save events.
- `AC-STATS-04`: Yellow and red cards are counted from card events.
- `AC-STATS-05`: Leaderboards refresh after a match is finished.

## Cup

- `AC-CUP-01`: Semifinals can be generated from four selected teams.
- `AC-CUP-02`: Semifinals can be generated from top four teams by previous
  season place when supported by data.
- `AC-CUP-03`: Semifinals cannot be generated again over an existing bracket.
- `AC-CUP-04`: Final can be generated only after two finished semifinals.
- `AC-CUP-05`: A drawn semifinal blocks final generation.
- `AC-CUP-06`: Bracket view shows semifinals, final, winners, and champion.

## Frontend UX

- `AC-UI-01`: Frontend is an organizer workspace, not a public promotional
  tournament page.
- `AC-UI-02`: Main areas are available from navigation: dashboard, seasons,
  teams, players, stadiums, referees, tournaments, matches, championship, and
  cup.
- `AC-UI-03`: Backend errors are displayed with clear user-facing text.
- `AC-UI-04`: Technical API URLs and stack details are not shown to normal
  users.
- `AC-UI-05`: Forms prevent obviously incomplete submissions.
- `AC-UI-06`: Frontend helps users avoid mistakes but does not replace backend
  validation.
- `AC-UI-07`: Mobile layout has no page-level horizontal overflow.
- `AC-UI-08`: Large tables use pagination, filtering, or internal scroll.
- `AC-UI-09`: Match detail is split into clear areas: summary, schedule/actions,
  lineups, protocol, finish/random.
- `AC-UI-10`: Dangerous actions require confirmation.

## Open Product Decisions

- `DEC-01`: Resolved for the current MVP: random result immediately finishes
  the match as an explicit generate-and-finish action.
- `DEC-02`: Are lineups mandatory before match finish?
- `DEC-03`: Are protocol events mandatory before match finish?
- `DEC-04`: What are the minimum starting-lineup rules: exactly one goalkeeper,
  ten field players, full tactical positions, or only one goalkeeper?
- `DEC-05`: Should the existing frontend be deleted and rebuilt from scratch
  after backend stabilization? Current recommendation: yes.
