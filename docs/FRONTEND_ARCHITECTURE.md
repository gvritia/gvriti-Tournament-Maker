# Frontend Architecture

## Decision

The current `frontend/` directory is a draft and will be removed after explicit
user confirmation. The architecture below describes the replacement frontend,
not the current implementation.

## Stack

- Vite
- React
- TypeScript
- React Router
- TanStack Query
- `lucide-react`
- Plain CSS
- Dark-only UI
- Docker Compose frontend service preserved

Do not add a frontend framework or component library unless the user explicitly
asks for it.

## High-Level Structure

```text
frontend
  public
  src
    app
      layouts
      providers
      router
      styles
    pages
      public-preview
      auth
      dashboard
      seasons
      teams
      team-detail
      players
      stadiums
      referees
      tournaments
      matches
      match-detail
      championship
      cup
    widgets
      app-shell
      data-table
      filters
      action-panel
      confirm-dialog
      match-summary
      lineup-editor
      protocol-timeline
      standings-table
      leaderboard
      cup-bracket
      team-profile
    features
      auth
      preview
      crud
      matches
      lineups
      protocol
      championship
      cup
    entities
      user
      season
      team
      player
      stadium
      referee
      tournament
      match
      lineup
      match-event
      standings
      statistics
    shared
      api
      config
      lib
      ui
      types
```

Folder names may be adjusted during implementation, but the separation should
remain: app composition, pages, reusable widgets, domain features, entity
types/helpers, and shared infrastructure.

## Routing

Public routes:

- `/` public read-only preview landing into the app shell preview.
- `/preview/dashboard`
- `/preview/teams`
- `/preview/teams/:teamId`
- `/preview/matches`
- `/preview/matches/:matchId`
- `/preview/championship`
- `/preview/cup`
- `/login`
- `/register`

Authenticated routes:

- `/app`
- `/app/seasons`
- `/app/teams`
- `/app/teams/:teamId`
- `/app/players`
- `/app/stadiums`
- `/app/referees`
- `/app/tournaments`
- `/app/matches`
- `/app/matches/:matchId`
- `/app/championship`
- `/app/cup`

The public preview route tree must never call protected backend endpoints or
perform mutations. It may use local sample data to show layout and tabs.

## Auth And Access Control

The app has two modes:

- `preview`: unauthenticated, read-only, static/sample data, no mutations.
- `workspace`: authenticated, JWT-backed, real user-scoped data.

Access rules:

- Protected workspace routes require a valid JWT.
- The API client attaches `Authorization: Bearer <token>` only in workspace
  mode.
- `401` clears auth state and query cache, then redirects to login.
- Logout clears token, current user, and the whole TanStack Query cache.
- Preview mode cannot create fake local changes that look persisted.
- Preview action buttons are disabled or point to login/register.

## API Layer

`src/shared/api` owns:

- API base URL from `VITE_API_BASE_URL`;
- request helper;
- auth header injection;
- response parsing;
- error normalization;
- paged list helper for endpoints capped at `limit=100`.

Backend errors should be normalized into:

- `status`;
- `message`;
- optional field errors for `422`;
- optional backend detail for developer logging only.

Normal UI must not display raw API URLs.

## Server State

Use TanStack Query for all authenticated backend data.

Query key examples:

- `['me']`
- `['seasons', filters]`
- `['teams', filters]`
- `['team', teamId]`
- `['players', filters]`
- `['matches', filters]`
- `['match', matchId]`
- `['lineups', matchId]`
- `['events', matchId]`
- `['standings', seasonId]`
- `['leaders', seasonId, metric]`
- `['cupBracket', tournamentId]`

Mutations should invalidate narrow affected keys. Finishing or generating a
match affects match detail, match list, lineups/events, standings, statistics,
and possibly cup bracket.

## UI Architecture

### App Shell

Authenticated workspace:

- left sidebar on desktop;
- top header with current user and logout;
- mobile drawer;
- active route state;
- compact content density.

Preview shell:

- same visual navigation shape;
- clear login/register entry;
- no destructive or mutating controls enabled.

### Tables

Tables are core UI, not secondary decoration.

Requirements:

- column headers;
- filters above the table;
- loading, empty, error states;
- row actions as icon buttons with tooltips;
- internal horizontal scroll for wide tables;
- no page-level horizontal overflow on mobile;
- pagination or full paged loading where needed.

### Forms

Forms live in modals, drawers, or page panels depending on complexity.

Requirements:

- required field hints;
- disabled submit while invalid or loading;
- backend `422` field mapping where possible;
- form-level backend message where field mapping is not possible;
- no submit in preview mode.

### Action Panels

Workflow-heavy screens use action panels:

- championship schedule generation;
- season simulation;
- cup semifinal/final generation;
- match reschedule;
- referee assignment;
- ticket price update;
- protocol generation.

Dangerous or irreversible actions require confirmation.

## Page Responsibilities

### Dashboard

Loads the main workspace overview:

- counts;
- nearest matches;
- recent results;
- quick actions;
- setup warnings;
- optional compact standings/leaderboard snippets.

### Teams

Team list supports:

- name/city filters;
- emblem preview;
- open team detail;
- create/edit/delete;
- clear conflicts for duplicate team names.

### Team Detail

Team detail supports:

- profile header with emblem;
- metadata;
- player roster;
- home stadium relation;
- upcoming/recent matches;
- related standing/stat snippet when available;
- edit team and add player actions.

Preview version is read-only.

### Matches

Match list supports:

- filters;
- create match;
- open match detail;
- status-aware actions;
- ticket price visibility.

### Match Detail

Match detail supports:

- summary;
- schedule/actions;
- lineups manual/generate;
- protocol events;
- generate protocol;
- finish/random workflow;
- disabled normal edits for finished matches.

### Championship

Championship supports:

- full schedule generation;
- schedule table;
- standings;
- player stats and leaderboards;
- full-season simulation.

### Cup

Cup supports:

- semifinal generation;
- final generation;
- bracket;
- champion display;
- open cup match detail;
- generate protocol for cup matches.

## Styling

Use plain CSS with tokens:

- color tokens;
- spacing scale;
- typography scale;
- table layout tokens;
- status colors;
- z-index rules for header/sidebar/dialogs.

Avoid:

- frontend marketing hero layout;
- gradient-heavy or one-color-purple theme;
- nested cards;
- visible in-app instructions explaining obvious UI;
- oversized text inside dense admin panels.

## Verification Plan

After the new frontend is implemented:

- `cmd /c npm run build`
- `cmd /c npm audit`
- Docker Compose full stack check with `docker compose up --build`
- Browser smoke flow:
  - public preview navigation and disabled actions;
  - register/login/logout;
  - dashboard;
  - team detail;
  - CRUD;
  - matches list/detail;
  - championship generation/simulation;
  - cup bracket/generation;
  - mobile no horizontal overflow.
