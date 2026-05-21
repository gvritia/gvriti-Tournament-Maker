# Frontend Bugs And Rebuild Risks

## Current Status

The current `frontend/` directory is a draft. It will be deleted after explicit
user confirmation and replaced with a new frontend. Bugs in the draft are kept
here only as historical lessons for the rebuild.

Do not spend time polishing the current draft UI.

## Fixed In Current Draft

### FE-DRAFT-014: Full-season generation showed a false connection error

Status: fixed in the current frontend, must not regress.

The frontend API client aborted every request after 8 seconds. Full-season
protocol generation can take longer than that, so the browser displayed a
connection-style error while the backend continued processing and saved the
generated results. A second attempt could then surface a conflict or no-op
state because the first request had actually succeeded.

Expected behavior:

- long-running generation actions use longer frontend timeouts;
- timeout/network errors do not mention raw backend internals to normal users;
- after a successful full-season generation, the UI waits for the response,
  invalidates championship reads, and shows a success message.

### FE-DRAFT-015: Referee empty-state appeared while referees were still loading

Status: fixed in the current frontend, must not regress.

On match detail, the missing-referee notice was based on `referees.length === 0`
without checking whether the referees query had completed. This made the demo
referee list look absent during loading.

Expected behavior:

- the missing-referee notice appears only after the referee query has finished;
- demo referees load on `/app/referees` and in match-related forms;
- normal users do not see internal text such as `backend scope`.

## Historical Draft Issues

### FE-DRAFT-013: Match-detail Generate protocol errors were silently swallowed

Status: fixed in the current frontend, must not regress.

The match-detail `Generate protocol` action used the shared `submitAction`
helper, which assigned backend errors to `formError`. `formError` is only
rendered inside open action forms (reschedule/referee/ticket). When the user
clicked `Generate protocol` without an open form, any `400/409` from the
backend (missing referee, missing lineups, fewer than ten eligible field
players, existing protocol events, etc.) was stored on the hidden state slot
and never surfaced to the user.

Expected behavior:

- `Generate protocol` errors are displayed above the action panel through
  the workspace-level operation error slot;
- `Assign referee` notice and `Generate protocol` lock when the workspace
  has zero referees and no referee is assigned to the match yet;
- the missing-referee notice points the user at `/app/referees` so a fresh
  starter workspace can fix the missing-referee state without guessing.

### FE-DRAFT-012: Lineup/protocol conflicts show backend English details

Status: fixed in the current frontend, must not regress.

During match-detail error smoke testing, several backend validation details for
lineups, protocol finish, and protocol generation still relied on raw backend
English strings unless the generic fallback caught them.

Expected behavior:

- duplicate lineup player and duplicate lineup number show concise Russian
  messages;
- suspended players show a clear lineup-specific conflict;
- final-score mismatch explains that the submitted score must match protocol
  goal events;
- protocol/random-result generation failures for missing referees, invalid
  lineups, missing players, or existing events are translated for normal users;
- technical URLs and stack details remain hidden from normal users.

### FE-DRAFT-010: Backend validation details leak into form errors

Status: fixed in the current frontend, must not regress.

During error UX smoke testing, known backend business errors such as duplicate
team names and duplicate player shirt numbers were surfaced as raw backend
English `detail` strings. Invalid team emblem URLs were also blocked by native
browser URL validation before the frontend could show its normalized backend
field error.

Expected behavior:

- common `400`, `409`, and `422` business errors render as human-facing UI
  messages;
- normal users do not see raw backend detail strings, stack traces, or API URLs;
- team emblem URL validation is handled by backend validation and displayed as
  a clear field error in the form.

### FE-DRAFT-009: Fresh users do not see why teams already exist

Status: fixed in the current frontend, must not regress.

Fresh organizer accounts receive starter LaLiga teams, home stadiums, and logo
URLs from the backend. During onboarding smoke testing, the dashboard showed 20
teams but did not explain that these are intentionally pre-created starter data
and can be edited.

Expected behavior:

- fresh-user dashboard explains that starter teams, stadiums, and logos already
  exist;
- the same notice points users toward creating a season and tournament before
  scheduling matches.

### FE-DRAFT-008: Implemented CRUD page still says CRUD is future work

Status: fixed in the current frontend, must not regress.

During CRUD smoke testing, the seasons page still described creation and
editing as a future CRUD layer even though the page already supports those
actions.

Expected behavior:

- implemented CRUD pages describe current capabilities, not retired roadmap
  notes;
- users should not see stale implementation-planning copy inside the workspace.

### FE-DRAFT-007: Cup generation actions stay enabled after bracket stages exist

Status: fixed in the current frontend, must not regress.

During cup smoke testing, the page kept `Generate semifinals` enabled after
semifinals already existed and kept `Generate final` enabled after the final
could no longer be generated. Backend rejected duplicate or invalid bracket
operations, but the UI should expose the current workflow state directly.

Expected behavior:

- semifinal generation is disabled after semifinals exist;
- final generation is enabled only when two semifinals are finished with clear
  winners and no final exists yet;
- locked states show a short user-facing reason.

### FE-DRAFT-006: Season simulation lacks confirmation

Status: fixed in the current frontend, must not regress.

The championship page exposed full-season simulation as a single click. That
action generates protocols and finishes matches, so it must ask for
confirmation before submitting.

Expected behavior:

- the season simulation button opens a confirmation prompt before mutation;
- cancelling the prompt leaves backend state unchanged.

### FE-DRAFT-005: Leaderboards show player ids instead of names

Status: fixed in the current frontend, must not regress.

During championship smoke testing, player leaderboards rendered fallback labels
such as `Player 683` even though the workspace already had player data loaded
elsewhere. This made the leaderboard hard to inspect.

Expected behavior:

- authenticated championship leaderboards join known player ids to player full
  names;
- id fallback remains only for missing or not-yet-loaded player records.

### FE-DRAFT-004: Finished match table actions remain enabled

Status: fixed in the current frontend, must not regress.

During match-detail smoke testing, the main finished-match actions were disabled
after a match was finished, but existing lineup and protocol rows still showed
enabled `Remove` buttons. Backend rejected immutable finished-match mutations,
but the UI should communicate the lock before submission.

Expected behavior:

- finished matches disable normal schedule, referee, ticket, delete, lineup,
  and protocol mutations;
- existing lineup/protocol row removal controls are disabled for finished
  matches.

### FE-DRAFT-003: Season schedule query never resolves

Status: fixed in the draft, must not regress in the rebuild.

The championship workspace used the generic paged-list helper for
`/schedule/seasons/{season_id}/matches`, but that backend endpoint returns a
plain full list and does not apply `offset`/`limit`. This caused the frontend to
keep requesting more pages and show `0 matches` in the championship schedule
even when the backend had generated fixtures.

Expected behavior:

- call the season schedule endpoint as a plain list request;
- reserve paged loading for endpoints that actually support pagination.

### FE-DRAFT-001: First-page-only list loading

Status: fixed in the draft, must not regress in the rebuild.

Backend list endpoints cap `limit` at `100`. The new frontend must either:

- page through all records when a full collection is truly needed; or
- provide real pagination/filtering in the UI.

Large players and matches lists must not silently show only the first 100 rows.

### FE-DRAFT-011: Some backend conflict details bypassed friendly translation

Status: fixed in the draft, must not regress in the rebuild.

The frontend had friendly translations for several backend conflicts, but a few
exact backend strings did not match the translation map. Affected flows included
duplicate referee names, duplicate tournament names, same-team match creation,
parallel referee conflicts, and duplicate cup semifinal generation.

Expected behavior:

- duplicate season/stadium/referee/tournament names show concise Russian
  messages;
- match creation and generation conflicts explain the user action needed;
- cup/championship generation errors do not show raw English backend strings;
- technical URLs and stack details remain hidden from normal users.

### FE-DRAFT-002: Mobile horizontal overflow

Status: fixed in the draft, must not regress in the rebuild.

The new frontend must avoid page-level horizontal overflow on mobile. Wide
tables may scroll inside their own table container, but the page shell itself
must remain within viewport width.

## Risks For The New Frontend

### FE-RISK-001: Preview mode accidentally allows actions

Unauthenticated users may view only a read-only preview. They must not be able
to submit forms, generate schedules, simulate seasons, finish matches, delete
resources, assign referees, reschedule matches, or change ticket prices.

Expected behavior:

- public preview uses static/sample data;
- mutating buttons are disabled or point to login/register;
- protected API calls are not made without JWT.

### FE-RISK-002: User-scoped data leakage after logout

Logout must clear the JWT and TanStack Query cache. A second user must never
see stale data from a previous user session.

### FE-RISK-003: Finished-match actions remain enabled

Finished matches are immutable through normal workflows. The UI must disable or
hide normal edit/delete/reschedule/referee/ticket actions for finished matches
and show a clear reason.

Backend remains authoritative even if the UI misses a case.

### FE-RISK-004: Backend errors are shown too technically

Normal users should not see raw API URLs, stack traces, or low-level network
details. Errors from `400`, `401`, `403`, `404`, `409`, and `422` should be
shown in human language.

### FE-RISK-005: Championship standings columns are wrong

Standings must show separate numeric columns:

- played;
- wins;
- draws;
- losses;
- goals scored;
- goals conceded;
- goal difference;
- points.

Do not show score-like strings inside goals-for/goals-against columns.

### FE-RISK-006: Team detail becomes disconnected from real backend data

The team detail page must be based on real backend entities:

- team;
- players by `team_id`;
- stadium home-team relation where available;
- matches involving the team;
- standings/statistics snippets when available.

Preview mode may use sample data, but authenticated mode must use backend data.

## Verification Checklist For Rebuild

- Public preview can be opened without login.
- Public preview tabs/pages are visible.
- Public preview actions cannot mutate anything.
- Login/register/logout works.
- Query cache clears on logout.
- Dashboard loads real scoped data after login.
- Team detail opens from teams list.
- CRUD pages handle backend validation errors.
- Matches list has filters and ticket price visibility.
- Match detail disables normal edits for finished matches.
- Generate protocol works for one match.
- Simulate season works from championship flow.
- Cup bracket and generation flows work.
- Large lists use pagination/filtering/internal scroll.
- Mobile has no page-level horizontal overflow.
