# Frontend Context

## Decision

The existing `frontend/` implementation is a draft. It was useful as the first
API-backed experiment, but it is not the target UI. Do not polish or extend the
current draft. After the user explicitly confirms the next step, delete
`frontend/` and rebuild the frontend from scratch.

The new frontend must be a dark organizer workspace for Tournament Maker. It is
not a public tournament page, not a Tournify-inspired clone, and not a marketing
landing page.

## Goal

Build a Vite + React + TypeScript single-page application for football
tournament organizers. The app must reflect the real backend:

- JWT auth: register, login, current user, logout.
- User-scoped domain data.
- CRUD for seasons, teams, players, stadiums, referees, and tournaments.
- Team `emblem_url` support.
- Starter players for newly registered organizers.
- Match CRUD and manual schedule editing.
- Championship full schedule generation.
- Match protocol generation for one match.
- Full-season protocol/result simulation.
- Manual lineups and generated lineups.
- Championship standings and player leaderboards.
- Cup semifinals, final, bracket, and cup match protocol generation.

Backend validation is the source of truth. The frontend should prevent obvious
empty submissions and guide the user, but it must not duplicate the full backend
business rules.

## Visual Direction

The new UI should feel like a reliable operations desk:

- dark-only interface;
- compact, calm, and readable;
- table-first information design;
- clear filters and action panels;
- modest color accents for status and actions;
- no decorative hero sections;
- no public-site news, social, ads, or marketing blocks;
- no visible technical API URLs for normal users.

Suggested design feel:

- base background: near black;
- surfaces: dark graphite;
- borders: subtle low-contrast lines;
- primary action: restrained blue;
- success: green;
- warning: amber;
- danger: red;
- text: high-contrast white/gray scale;
- radius: mostly 6-8px;
- icons: `lucide-react`.

## Public Preview For Unauthenticated Users

Unauthenticated users may inspect how the product looks, but they must not be
able to perform any real action.

Rules:

- Public users can open a read-only preview shell and switch between preview
  tabs/pages to understand the interface structure.
- Public preview uses static sample data or empty visual states, not protected
  backend data.
- Public users cannot create, update, delete, generate, simulate, finish,
  assign, reschedule, or submit anything.
- All action buttons in preview mode are disabled or redirect to login/register.
- Forms in preview mode are non-submittable.
- The real authenticated workspace remains protected by JWT.
- Logout clears token and TanStack Query cache before returning to public mode.

This means a non-authorized visitor can see the dashboard shape, navigation,
tables, match detail layout, championship area, cup bracket layout, and team
detail page layout, but cannot change anything.

## Authenticated Workspace

After login, the user enters the real organizer workspace. All data is loaded
from the current user's backend scope. No cached data from a previous account
may remain visible after logout/login.

Main navigation:

- Dashboard
- Seasons
- Teams
- Players
- Stadiums
- Referees
- Tournaments
- Matches
- Championship
- Cup

## Primary Workflows

1. Register or login.
2. Review dashboard summary and quick actions.
3. Create a season and tournaments.
4. Manage teams, team detail, players, stadiums, and referees.
5. Create matches manually or generate the full championship schedule.
6. Open match detail to manage schedule, referee, ticket price, lineups, and
   protocol.
7. Generate a match protocol or simulate a season.
8. Review standings, leaderboards, and cup bracket.
9. Logout safely.

## Core Screens

### Auth

Login/register screens should be simple and dark. They should not look like a
public marketing hero. Backend errors must be shown clearly.

### Dashboard

Dashboard should prioritize organizer status:

- active seasons and tournaments;
- teams count;
- scheduled and finished matches;
- nearest matches;
- recent results;
- quick actions;
- warnings for missing setup such as no referees or no stadiums.

### CRUD Sections

CRUD pages use dense tables, filters, and forms. Large lists require
pagination, filters, or internal scroll.

Entities:

- seasons;
- teams;
- players;
- stadiums;
- referees;
- tournaments.

Delete actions require confirmation.

### Team Detail

Each team needs a dedicated detail page.

The page should show:

- emblem or fallback initials;
- team name, city, address, manager, previous season place;
- optional home stadium;
- player roster table;
- recent and upcoming matches for the team;
- team-related championship standing row when available;
- quick actions for editing team data, adding a player, and opening related
  matches.

For unauthenticated preview mode, this page is visible with sample read-only
content and disabled actions.

### Matches

Matches are the densest operational screen:

- filters by season, tournament, team, status, and date range;
- match table with date, teams, score/status, stadium, referee, ticket price,
  and actions;
- create match form;
- edit/reschedule/assign referee/change ticket price actions;
- clear disabled state for finished matches.

Finished matches cannot be edited through normal actions.

### Match Detail

Match detail should be split into clear sections:

- Summary
- Schedule and actions
- Lineups
- Protocol events
- Result generation / finish workflow

The generate protocol action is explicit: it fills referee, lineups, events,
score, status, standings, and statistics according to backend behavior.

### Championship

The championship screen should include:

- full schedule generation action;
- schedule filters;
- standings table with separate columns:
  `played`, `wins`, `draws`, `losses`, `goals_scored`,
  `goals_conceded`, `goal_difference`, `points`;
- one-click season simulation;
- player statistics and leaderboards.

### Cup

The cup screen should include:

- generate semifinals;
- generate final;
- bracket view;
- cup match actions;
- protocol generation for cup matches;
- champion display after final completion.

## Error UX

Show backend errors in human language:

- `400`: invalid business request.
- `401`: login required or session expired.
- `403`: no access to this action.
- `404`: resource not found.
- `409`: conflict, usually calendar/resource/domain conflict.
- `422`: invalid form fields.

Do not show raw stack traces or technical API URLs to normal users.

## Implementation Boundary

Do not delete `frontend/` yet. Do not create the new frontend yet. The next
step after this documentation update is to wait for explicit user confirmation
to delete the draft frontend and scaffold the replacement.
