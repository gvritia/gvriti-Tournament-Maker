# Frontend Development Log

## 2026-05-21

### Visual Polish, SCSS Migration, GitHub Pages Preview Deploy

- Migrated frontend styles from a single `src/styles/global.css` to a
  modular SCSS architecture (Dart Sass, modern `@use` syntax). New files:
  `_tokens.scss` (color/spacing/radius/shadow/animation tokens via CSS
  variables), `_mixins.scss` (focus-ring, surface, breakpoints),
  `_reset.scss`, `_layout.scss` (sidebar/topbar/content + mobile drawer),
  `_panels.scss` (panel, page-intro, KPI cards, section-head),
  `_buttons.scss` (button + variants, mode chips, status badges),
  `_forms.scss` (inputs, selects, field grids, auth panel),
  `_tables.scss` (data-table with sticky thead, hover rows, skeleton row,
  pager), `_notices.scss` (notice variants, form-error, progress panel),
  `_components.scss` (team-emblem, matchup, bracket, meta-grid,
  scoreline). `global.scss` is the new entry; the old `global.css` is
  preserved as a no-op stub so unknown imports do not 404.
- `src/main.tsx` now imports `./styles/global.scss`.
- Added `sass ^1.83` to `frontend/devDependencies` so Vite can compile
  SCSS on `npm install`.
- Visual polish without functional changes:
  - softer dark gradient page background, fixed backdrop;
  - rounded radii bumped to 10/14 px on cards/panels;
  - sticky table headers, hover-row highlight, skeleton shimmer for
    loading rows, tabular numerals in stats tables;
  - new focus ring (`box-shadow: 0 0 0 3px rgba(78,161,255,0.28)`) on
    every interactive element;
  - sidebar: gradient brand mark, active-route left accent stripe and
    background gradient, mobile drawer slides in with a blurred backdrop;
  - topbar: sticky, blurred backdrop, ellipsised title, larger
    min-height;
  - notice cards have a left accent bar by severity (info/success/
    warning/danger);
  - form-error shakes (220 ms) when shown so it gets noticed;
  - inline-form slides in (200 ms) when toggled;
  - cup bracket cards lift on hover, champion-card has an amber tint;
  - native selects get custom caret triangles that match the dark theme;
  - WebKit scrollbars get a thin transparent track + soft thumb;
  - page-fade animation on each route transition (220 ms);
  - status chips now have status-specific border/background pairs for
    planned/active/finished/cancelled/archived.
- No component logic changed. All existing class names are preserved,
  so the React tree did not have to be touched.
- GitHub Pages public preview deploy:
  - `frontend/vite.config.ts` now accepts a configurable `base` via
    `VITE_BASE_PATH` env or `mode === "pages"`. In CI the workflow
    exposes `GITHUB_REPOSITORY`, so the base path is `/${repoName}/`
    automatically.
  - `frontend/.env.pages` sets `VITE_BASE_PATH=/gvriti-Tournament-Maker/`,
    `VITE_USE_HASH_ROUTER=true`, and a placeholder API URL.
  - `frontend/package.json` exposes `npm run build:pages` (Vite mode
    `pages`).
  - `App.tsx` picks `createHashRouter` when `VITE_USE_HASH_ROUTER ===
    "true"` and `createBrowserRouter` otherwise. Hash routing makes every
    deep link reachable on GitHub Pages without a 404.html hack.
  - `frontend/public/404.html` is still added as a belt-and-braces SPA
    fallback that rewrites unknown paths to the hash-based root.
  - `AuthProvider.tsx` skips reading `localStorage` on a public preview
    build so a stale local JWT does not trigger 401 noise against the
    placeholder API.
  - `AuthPage.tsx` swaps the login/register form for a friendly Russian
    notice when running in public preview mode, with a link back to `/`.
  - `.github/workflows/frontend-pages.yml` builds the SPA, uploads it as
    a Pages artifact, and deploys it through `actions/deploy-pages`.
    Concurrency group `pages` prevents overlapping deploys.
  - One-time setup the user must do in GitHub: Settings → Pages →
    "Build and deployment" → Source = "GitHub Actions". After that, every
    push to `master`/`main` that touches `frontend/**` redeploys.
- Verification:
  - static review of every new SCSS module and updated TSX file;
  - `cmd /c npm install` (to pull in `sass`) and `cmd /c npm run build`
    were not run in this slice because the local Linux sandbox cannot
    execute Windows-installed `node_modules`. The user should run both
    locally after pulling. On the first push of this slice the GitHub
    Actions workflow will exercise the build in the cloud.

### Language Toggle And Season Progress Panel

- Added a shared frontend language provider backed by `localStorage`.
- Added a header language button so the app shell can switch between Russian
  and English without logging out.
- Connected the championship workspace to the language provider, covering the
  page intro, setup notices, action labels, schedule form, standings/schedule
  headings, leader metric labels, and table empty states.
- Added an in-page progress panel for full-season protocol generation. The
  panel opens immediately after the confirmation prompt, advances while the
  backend request is pending, then switches to done/error after the response.
- Added small CSS polish for the language control and progress panel, including
  mobile wrapping for the progress metadata.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`
  - browser smoke: the header language toggle switched the public shell to
    English and the checked viewport had no page-level horizontal overflow.
    Authenticated browser login smoke was blocked by the in-app browser
    clipboard bridge, not by application code.

### Generation Timeout And Referee Loading UX

- Added per-request timeout support in the frontend API client and gave
  long-running generation workflows enough time to finish:
  - one-match protocol generation: 30 seconds;
  - championship schedule generation: 60 seconds;
  - cup semifinal/final generation: 60/30 seconds;
  - full-season simulation: 120 seconds.
- Replaced the misleading network fallback copy that told the user to check
  whether the backend was running. Timeout/network failures now use neutral
  user-facing Russian messages without raw API URLs or stack traces.
- Confirmed through live API smoke that the demo account has 8 referees.
- Fixed match-detail referee UX so the "create a referee first" notice appears
  only after the referee query has actually finished. During loading, the UI no
  longer looks like the demo referee list is empty.
- Removed visible system/internal copy such as "backend scope" from the
  dashboard and replaced several backend-facing labels/descriptions with normal
  user-facing Russian text.
- Browser smoke against the Docker-served frontend verified:
  - demo login works;
  - `/app/referees` shows demo referees including Alejandro Hernandez, Ricardo
    de Burgos, Jose Luis Munuera, and Guillermo Cuadra;
  - dashboard no longer contains `backend scope` or raw `backend` wording;
  - `/app/referees` no longer contains raw `backend` wording;
  - mobile viewport `390x844` has no page-level horizontal overflow on
    `/app`.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`

### Match Detail Generate Protocol Error Visibility

- Fixed a UX gap on `/app/matches/:matchId` where backend errors from
  `Generate protocol` were silently lost. The handler used `submitAction`,
  which set `formError`. `formError` is only rendered inside the action forms
  (reschedule/referee/ticket), so when the user clicked `Generate protocol`
  without an open form, any backend error returned `400/409` ("requires a
  referee", "requires lineups", "requires at least ten field players", etc.)
  was set on a hidden state slot and never shown.
- `handleGenerateProtocol` now sets `operationError` directly. That slot is
  rendered above the action panels, so the user sees the translated Russian
  message immediately.
- Added a workspace notice on the match detail page when the current user has
  zero referees, with a link to `/app/referees`. Without this notice the
  registration starter workspace looks like protocol generation should work
  even though there is no referee to auto-assign.
- Disabled the `Generate protocol` button when the user has zero referees and
  the match also has no assigned referee. The notice explains why.
- Russified delete confirmation prompts for match-detail lineups, protocol
  events, and the match delete action, plus the players-CRUD delete prompt.
  Previously those prompts were in English inside an otherwise Russian
  workspace.
- Static analysis pass over the catalog/match/match-detail/championship/cup
  pages confirmed that all generation/simulation/cup workflows already
  surface backend errors through their own `operationError` state. Only the
  match-detail `Generate protocol` path was missing this contract.
- Static analysis of `RandomResultService`, `LineupService`, `CupService`,
  and `StarterDataService` confirmed the existing backend contracts referenced
  by the task hold:
  - season simulation skips finished, cancelled, and already-protocolled
    matches via `_should_generate_in_season`;
  - cup semifinal generation searches forward up to 120 days for a free
    `match_datetime` instead of failing immediately;
  - lineup generation drops suspended players and refills from eligible
    teammates;
  - starter data still seeds 18 players per team (2 GK + 16 field), so the
    "at least ten field players" rule survives one suspension.
- Backend `StarterDataService` does not seed starter referees. Demo seed via
  `seed_demo_data.py` does. A fresh starter/test organizer therefore needs
  to create at least one referee before protocol generation or
  assign-referee works. The new frontend notice tells the user exactly that.
- Verification:
  - static frontend analysis;
  - `cmd /c npm run build` and `cmd /c npm audit` were not run in this slice
    because the local Linux sandbox could not execute the Windows-installed
    `node_modules` Rollup native binary; the user should run both locally
    after pulling.

## 2026-05-19

### Starter Squad Depth For Protocol Generation

- Investigated protocol generation failures that reported fewer than ten
  eligible field players even though starter workspaces had teams and players.
- Found that starter/test teams had exactly 11 players: one goalkeeper and ten
  field players. That was enough for the first generated protocol but left no
  field-player buffer when a player was suspended for the next match.
- Expanded backend starter data to 18 players per team: two goalkeepers and
  sixteen field players.
- Backfilled existing Docker starter/test accounts from 220 to 360 players.
  Demo data with 675 imported LaLiga players was not changed.
- Verification:
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py -q`
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_random_results.py -q`
  - `.venv\Scripts\python.exe -m ruff check backend/app/services/starter_data_service.py backend/tests/test_auth.py`
  - `.venv\Scripts\python.exe -m black --check backend/app/services/starter_data_service.py backend/tests/test_auth.py`
  - `docker compose build --pull=false backend`
  - `docker compose up -d --no-build backend`
  - live Docker API smoke: newly registered user received 360 players, a
    follow-up match protocol generated after a red-card suspension, the
    suspended player was skipped, and the temporary user was deleted.

### Season Simulation Remaining Matches

- Changed the season simulation workflow so organizers can generate the
  remaining matches even when part of the season is already finished.
- Backend season simulation now skips finished matches, cancelled matches, and
  matches that already have protocol events, then generates only the remaining
  clean matches in one transaction.
- Updated the championship confirmation/success text to make the remaining-
  matches behavior explicit.
- Verification:
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

### Cup Semifinal Auto-Scheduling Fix

- Fixed the backend behavior behind the cup UI where semifinal generation could
  fail with "team cannot play more than one match per day" when the selected
  preferred date conflicted with an existing match.
- Cup semifinal generation now searches forward from each requested preferred
  datetime and creates the match on the nearest valid date at the same time.
- Added tests for same-day conflicts and weekly match-limit conflicts.
- Added frontend error translation for the rare no-available-cup-date failure.
- Verification:
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

### Starter Players Data Fix

- Investigated a reported issue where teams loaded for test accounts but the
  players page had no player data.
- Confirmed the live demo user has 675 players through `/api/v1/players/`, but
  several starter/test users had teams and zero players because registration
  previously seeded only teams, stadiums, and logo URLs.
- Fixed the backend starter data source so newly registered organizers receive
  starter players per team.
- Backfilled the running Docker PostgreSQL test data for existing starter-style
  accounts that had 20 teams and zero players; demo data with imported real
  squads was left unchanged.
- Updated the dashboard onboarding notice so it mentions starter players as
  part of the preloaded workspace data.
- Verification:
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

### Lineup And Protocol Error Message Polish

- Ran a focused live API smoke pass against a temporary organizer for
  match-detail validation errors.
- Confirmed backend detail strings for:
  - duplicate lineup player;
  - duplicate lineup shirt number;
  - suspended lineup player;
  - finish score mismatch against recorded goal events;
  - protocol generation without a referee available for automatic assignment.
- Deleted the temporary smoke organizer from PostgreSQL after the check.
- Expanded frontend API error translation for lineup, protocol finish, and
  random/protocol generation conflicts so match-detail forms show concise
  Russian user-facing messages instead of backend English details.
- Browser automation was not available in this environment, so this slice was
  verified through live API responses plus frontend build output rather than a
  click-through UI smoke.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`

### Human-Friendly Error Smoke

- Ran a focused error UX smoke pass against the Docker-served frontend and real
  backend.
- Checked duplicate team name, invalid team emblem URL, and duplicate player
  shirt number.
- Fixed API error normalization so known backend business errors render as
  Russian user-facing messages instead of raw backend English details.
- Fixed team emblem URL forms so invalid URLs reach backend validation instead
  of being blocked by browser-native URL validation before the app can show a
  normalized field error.
- Verified the UI now shows:
  - `Команда с таким названием уже существует.`;
  - `Введите HTTP/HTTPS ссылку на логотип команды.`;
  - `В этой команде уже есть игрок с таким номером.`
- Cleaned up the temporary smoke player created for duplicate-number testing.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`

### Mobile Smoke Pass

- Ran a mobile-width smoke pass at 390px across the Docker-served authenticated
  workspace after the logo and onboarding-notice slices.
- Checked dashboard, teams, players, stadiums, matches, championship, and cup.
- Verified there is no page-level horizontal overflow: document/body
  `scrollWidth` stays within the viewport on the checked routes.
- Verified buttons, mode chips, and notices do not clip their text on the
  checked mobile viewport.
- No frontend code changes were needed for this pass.

### Fresh User Onboarding Smoke

- Ran a browser smoke pass for a newly registered organizer against the
  Docker-served frontend and real backend.
- Verified registration creates a usable starter workspace:
  - 20 starter teams;
  - 20 home stadiums;
  - 20 team logo URLs;
  - 0 seasons, tournaments, and matches before organizer setup.
- Verified fresh-account pages do not show runtime/load errors:
  dashboard, teams, players, stadiums, matches, championship, and cup.
- Confirmed empty/locked states for no season/tournament/match data:
  matches disables match creation until setup is complete, championship shows
  setup-needed plus empty standings/schedule, and cup shows setup/final locks.
- Added a dashboard onboarding notice that tells fresh users starter LaLiga
  teams, home stadiums, and logos already exist and can be edited before they
  create a season and tournament.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`

### CRUD Smoke Polish

- Ran a browser smoke pass for authenticated CRUD workflows against the
  Docker-served frontend and real backend data.
- Verified create/edit/delete flows for:
  - referees;
  - teams;
  - tournaments;
  - seasons;
  - stadiums;
  - players, using a temporary team dependency.
- Cleaned up all temporary smoke entities after verification.
- Fixed stale seasons page copy that still said creation/editing would come in
  a later CRUD slice, even though the workflow is now implemented.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit` was attempted twice but could not reach
    `registry.npmjs.org` because of local DNS `ENOTFOUND`.
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`

### Cup Smoke Polish

- Ran a deeper browser smoke pass on the Docker-served cup workspace.
- Verified the cup bracket view, semifinal cards, match-detail links, final
  generation, cup final protocol generation from match detail, and champion
  display after the final finished.
- Fixed cup generation controls so:
  - semifinal generation is disabled after semifinals already exist;
  - final generation is disabled until two semifinals are finished with clear
    winners;
  - final generation is disabled again after a final already exists.
- Added short user-facing locked-state messages for cup semifinal/final setup.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Team Emblem Fallback Slice

- Added a shared `TeamMark` component for workspace team badges.
- Workspace dashboard, team detail, and teams CRUD now use the shared badge
  renderer.
- Team badges still render `emblem_url` images when available, but fall back to
  team initials if an external logo URL fails to load.
- This supports the new backend starter-team data with external club logo URLs.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Match Detail Team Logos Slice

- Added home and away team emblems to the authenticated match detail hero.
- Match detail now renders each team as `TeamMark + team name` in the selected
  match header, with the status badge kept separate.
- Adjusted responsive CSS so the matchup title wraps cleanly and stacks on
  small screens.
- Fixed the large image badge sizing rule so `TeamMark size="large"` is
  honored for real logo images.
- Browser-verified `/app/matches/10`: the header renders two logo images for
  Leganes and Real Betis.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Matchup Logos Slice

- Added a shared `MatchupInline` component for compact match pair rendering.
- Matches list, championship schedule, and cup bracket cards now show both team
  logos next to the team names.
- Added responsive inline matchup CSS so logos wrap with long team names instead
  of widening the page.
- Browser-verified:
  - `/app/matches`: 50 visible matchup rows with 100 team logo images.
  - `/app/championship`: 50 visible schedule rows with 100 team logo images.
  - `/app/cup`: 3 bracket matchup cards with 6 team logo images.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Team Identity Tables Slice

- Added a shared `TeamInline` component for compact `TeamMark + name` cells.
- Championship standings now show team logos in the team column.
- Match detail lineups and protocol event tables now show team logos in the
  team column when rows exist.
- Browser-verified:
  - `/app/championship`: 20 standings team cells with 20 logo images.
  - `/app/matches/386`: 42 team cells across lineup/protocol tables with 42
    logo images.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Workspace Team Identity Expansion

- Reused `TeamInline` and `MatchupInline` across the remaining workspace
  surfaces that still rendered teams as plain text.
- Players CRUD now shows a logo next to each player's team link.
- Stadiums CRUD now shows a logo next to the home team.
- Cup bracket champion and winner fields now show team logos.
- Dashboard match previews now use the same logo matchup renderer as the match
  list.
- Team detail opponent rows now show opponent logos instead of `Team {id}`
  placeholders when team data is available.
- Browser-verified:
  - `/app`: 8 dashboard matchup rows with 16 logo images.
  - `/app/players`: 50 visible player rows with 50 team logo images.
  - `/app/stadiums`: 28 stadium rows with 28 home-team logo images.
  - `/app/cup`: 5 winner/champion team cells with 5 logo images.
  - `/app/teams/29`: 38 opponent cells with 38 logo images.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Team Detail Navigation Polish

- Replaced disabled team-detail action buttons with live links to the relevant
  teams and players CRUD pages.
- Updated the missing home-stadium helper text to point users to the stadiums
  page instead of describing stadium CRUD as future work.
- Added an `Open` action to team-detail match rows so related matches can be
  opened directly.
- Dashboard match preview rows now link to match detail pages while preserving
  the logo matchup renderer.
- Browser-verified:
  - `/app`: 8 dashboard matchup rows are wrapped by match detail links.
  - `/app/teams/29`: team action links point to `/app/teams` and `/app/players`,
    disabled placeholder action buttons are gone, and 38 related match links are
    available.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Championship Smoke Polish

- Ran a browser smoke pass on the Docker-served championship workspace.
- Verified the selected demo championship loads standings, a paginated
  380-match schedule, ticket prices, match-detail links, and leaderboard data.
- Fixed player leaderboards so they render real player names from backend
  player data instead of `Player {id}` fallback labels when the player list is
  available.
- Added confirmation before full-season simulation because it generates
  protocols and finishes season matches.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Match Detail Smoke Polish

- Ran a deeper browser smoke pass against the Docker-served frontend on
  `http://127.0.0.1:5173` with the demo account.
- Verified match-detail workflows on a scheduled match:
  - reschedule form submission;
  - referee assignment;
  - ticket price update;
  - generated lineup creation;
  - manual lineup add and lineup deletion;
  - protocol event add and deletion;
  - finish validation for a score that does not match recorded goals;
  - successful match finish.
- Found and fixed a finished-state UI gap: lineup and protocol table `Remove`
  buttons stayed enabled after a match became `finished`. They now follow the
  same finished-match lock as the rest of the normal edit actions.
- Verification:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

## 2026-05-17

### Frontend Smoke Polish

- Ran the full Docker stack with backend and frontend together and verified the
  demo login flow with `demo@example.com` / `DemoPass123`.
- Smoke-checked public preview, protected dashboard, teams, players, matches,
  match detail, championship, and cup pages against real backend data.
- Fixed the championship schedule query so it no longer uses the paged-list
  helper for `/schedule/seasons/{season_id}/matches`. The backend returns that
  endpoint as a full list, so the previous frontend call never resolved and the
  championship page displayed `0 matches` despite generated fixtures.
- Verified the fix in the browser: the demo championship schedule now shows
  `380 matches`.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Frontend Table Usability Slice

- Added shared `DataTable` support for loading rows and lightweight client-side
  pagination.
- Enabled paginated rendering for large workspace tables:
  - players list, 50 rows per page;
  - matches list, 50 rows per page;
  - championship schedule, 50 rows per page;
  - championship leaderboards, 25 rows per page.
- Kept table horizontal scroll inside the table container so page-level width
  stays stable on desktop/mobile layouts.
- Verified on the demo data that players show `Showing 1-50 of 675` and the
  championship schedule shows `Showing 1-50 of 380`.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Frontend Docker And Mobile Controls Slice

- Restored the frontend service to Docker after a transient Docker Hub DNS
  lookup failure. Rebuilt only the frontend image with
  `docker compose build --pull=false frontend`, then restarted it with
  `docker compose up -d --no-build frontend`.
- Removed the temporary local Vite dev servers used for verification; the app
  is again served by `tournament_maker_frontend` on `http://127.0.0.1:5173`.
- Tightened responsive CSS for dense control rows:
  - filters now flex within their containers and cap at `max-width: 100%`;
  - mobile filter controls stack to full width;
  - table pager controls stack cleanly on small screens.
- Verified the Docker-served frontend still shows the championship pager
  (`Showing 1-50 of 380`) and keeps page width stable on the checked desktop
  viewport.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Frontend Loading States Slice

- Connected the shared `DataTable` loading state to the dashboard, team detail,
  and catalog CRUD tables so first-load requests no longer look like real empty
  data.
- Dashboard KPI cards now show a neutral placeholder while seasons, teams, and
  matches are still loading, then resolve to the real counts.
- Team detail roster and team-match tables now show loading rows while related
  players, matches, and stadiums are being fetched.
- Verified in the Docker-served frontend that dashboard counts settle to the
  demo values after loading and page width remains stable.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Frontend Draft Removal And First Rebuild Slice

- Deleted the old `frontend/` draft after explicit user confirmation.
- Created the first small replacement frontend slice instead of rebuilding the
  full app in one pass.
- Added a Vite + React + TypeScript setup with React Router, TanStack Query,
  `lucide-react`, plain CSS, and Docker-ready frontend configuration.
- Added public read-only preview routing for:
  - dashboard;
  - teams;
  - team detail;
  - matches;
  - match detail;
  - championship;
  - cup;
  - login/register visual placeholders.
- Added the first reusable components:
  - app shell;
  - action panel with disabled preview actions;
  - data table;
  - team profile/detail block.
- Added static sample data only. The first slice does not call protected backend
  endpoints and does not perform mutations.
- Verified:
  - `cmd /c npm install`
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Auth And Workspace Slice

- Added a shared frontend API client with:
  - `VITE_API_BASE_URL` support;
  - bearer token injection;
  - request timeout for unavailable backend;
  - backend error normalization;
  - paged list loading helper for backend endpoints capped at `limit=100`.
- Added auth infrastructure:
  - token persistence in `localStorage`;
  - current-user query;
  - logout with TanStack Query cache clearing;
  - global `401` cleanup.
- Replaced login/register placeholders with real forms wired to:
  - `POST /api/v1/auth/login`;
  - `POST /api/v1/auth/register`;
  - `GET /api/v1/auth/me`.
- Added protected `/app/*` workspace routing.
- Added the first authenticated dashboard slice that loads real user-scoped
  seasons, teams, and matches.
- Kept unauthenticated public preview read-only. Domain actions in preview
  remain disabled; login/register are the only path into the real workspace.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Workspace Teams Slice

- Added real authenticated `/app/teams` route backed by the current user's
  backend data.
- Added client-side search by team name, city, and manager.
- Added real authenticated `/app/teams/:teamId` detail route.
- Team detail now reads backend teams, players, stadiums, and matches, then
  renders:
  - team profile and emblem/fallback;
  - city, address, manager, previous season place;
  - home stadium from `Stadium.home_team_id`;
  - roster filtered by `Player.team_id`;
  - team matches filtered by home/away participant ids.
- Mutating team actions remain disabled for this slice and will be implemented
  separately.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Workspace Matches Slice

- Added real authenticated `/app/matches` route backed by user-scoped backend
  data.
- Added client-side filters for season, tournament, team, status, and date
  range.
- Match list now displays date, tournament, teams, status, score, stadium,
  referee, and ticket price.
- Added real authenticated `/app/matches/:matchId` detail route.
- Match detail reads backend match, seasons, tournaments, teams, stadiums, and
  referees, then renders summary, schedule metadata, status, score, ticket
  price, referee, and placeholders for lineups/protocol.
- Mutating match actions remain disabled for this slice. Reschedule, referee
  assignment, ticket price changes, and protocol generation will be implemented
  separately.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Workspace Catalog Tables Slice

- Added real authenticated read-only catalog routes:
  - `/app/seasons`;
  - `/app/stadiums`;
  - `/app/referees`;
  - `/app/tournaments`.
- Expanded workspace sidebar navigation with seasons, stadiums, referees, and
  tournaments.
- Added filters/search for the catalog tables:
  - seasons by name and status;
  - stadiums by name, city, or address;
  - referees by full name;
  - tournaments by name, type, and status.
- Joined related read data where useful:
  - stadium home team names from teams;
  - tournament season names from seasons.
- Mutating create/edit/delete actions remain disabled for this slice and will
  be implemented separately with confirmation/error handling.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Referee CRUD Slice

- Added the first real authenticated CRUD workflow for one simple catalog:
  referees.
- `WorkspaceRefereesPage` now supports:
  - creating a referee through `POST /api/v1/referees/`;
  - editing a referee through `PATCH /api/v1/referees/{referee_id}`;
  - deleting a referee through `DELETE /api/v1/referees/{referee_id}`;
  - delete confirmation before the backend mutation;
  - backend error rendering for form and operation failures;
  - query invalidation after successful mutations.
- Other catalog pages remain read-only until their forms are implemented in
  separate slices.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Season CRUD Slice

- Added authenticated CRUD workflow for seasons.
- `WorkspaceSeasonsPage` now supports:
  - creating a season through `POST /api/v1/seasons/`;
  - editing a season through `PATCH /api/v1/seasons/{season_id}`;
  - deleting a season through `DELETE /api/v1/seasons/{season_id}`;
  - delete confirmation before mutation;
  - backend error rendering for form and operation failures;
  - query invalidation for seasons and related tournament/match reads.
- Season form includes name, start date, end date, and status.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Stadium CRUD Slice

- Added authenticated CRUD workflow for stadiums.
- `WorkspaceStadiumsPage` now supports:
  - creating a stadium through `POST /api/v1/stadiums/`;
  - editing a stadium through `PATCH /api/v1/stadiums/{stadium_id}`;
  - deleting a stadium through `DELETE /api/v1/stadiums/{stadium_id}`;
  - optional home-team assignment through `home_team_id`;
  - delete confirmation before mutation;
  - backend error rendering for form and operation failures;
  - query invalidation for stadiums and match reads.
- Stadium form includes name, city, address, capacity, and optional home team.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Team CRUD Slice

- Added authenticated CRUD workflow for teams.
- `/app/teams` now supports:
  - creating a team through `POST /api/v1/teams/`;
  - editing a team through `PATCH /api/v1/teams/{team_id}`;
  - deleting a team through `DELETE /api/v1/teams/{team_id}`;
  - fields for name, city, address, manager, emblem URL, and previous-season
    place;
  - delete confirmation before mutation;
  - backend error rendering for form and operation failures;
  - query invalidation for teams, team detail, stadiums, and matches.
- The route now uses a dedicated team CRUD page so the current slice stays
  isolated from the existing read/detail workspace code.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Player CRUD Slice

- Added authenticated CRUD workflow for players.
- `/app/players` now supports:
  - creating a player through `POST /api/v1/players/`;
  - editing a player through `PATCH /api/v1/players/{player_id}`;
  - deleting a player through `DELETE /api/v1/players/{player_id}`;
  - fields for full name, age, position, shirt number, and team assignment;
  - filters by player/team text, team, and position;
  - delete confirmation before mutation;
  - backend error rendering for validation and duplicate-number conflicts;
  - query invalidation for players, the affected team detail, and matches.
- Added the protected `/app/players` route and sidebar navigation entry.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Tournament CRUD Slice

- Added authenticated CRUD workflow for tournaments.
- `/app/tournaments` now supports:
  - creating a tournament through `POST /api/v1/tournaments/`;
  - editing a tournament through `PATCH /api/v1/tournaments/{tournament_id}`;
  - deleting a tournament through `DELETE /api/v1/tournaments/{tournament_id}`;
  - fields for season, name, tournament type, and status;
  - filters by tournament/season text, season, type, and status;
  - delete confirmation before mutation;
  - backend error rendering for validation and duplicate-name conflicts;
  - query invalidation for tournaments and matches.
- The route now uses a dedicated tournament CRUD page. Championship schedule
  generation and cup bracket actions remain separate workflows.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Match Create Slice

- Added the first authenticated match mutation workflow on `/app/matches`.
- The matches page now supports creating a scheduled match through
  `POST /api/v1/matches/`.
- The create form includes season, tournament, home team, away team, stadium,
  optional referee, date/time, round number, and optional cup stage.
- The UI blocks obvious incomplete setup before opening the form: a match needs
  a season, tournament, at least two teams, and a stadium.
- Backend validation remains authoritative for cross-resource ownership,
  calendar conflicts, referee conflicts, and ticket-price calculation.
- Successful creation invalidates match list and the created match detail key.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Match Edit Workflows Slice

- Replaced the `/app/matches` route with a dedicated match operations page.
- Kept match creation and added normal edit workflows for non-finished matches:
  - reschedule through `POST /api/v1/matches/{match_id}/reschedule`;
  - assign referee through `POST /api/v1/matches/{match_id}/assign-referee`;
  - update ticket price through `POST /api/v1/matches/{match_id}/ticket-price`;
  - delete through `DELETE /api/v1/matches/{match_id}` with confirmation.
- Finished matches now have normal edit/delete buttons disabled in the table.
- Backend error rendering is shared across schedule, referee, ticket, and delete
  failures, including calendar and referee conflicts.
- Successful actions invalidate match list/detail reads and downstream
  standings/statistics/cup-bracket query families for later screens.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Match Detail Actions Slice

- Replaced the `/app/matches/:matchId` route with a dedicated match detail
  actions page.
- Match detail now supports the same normal non-finished actions as the match
  list:
  - reschedule;
  - assign referee;
  - update ticket price;
  - delete with confirmation.
- Added one-match protocol generation through
  `POST /api/v1/matches/{match_id}/generate-protocol`.
- Successful protocol generation invalidates match list/detail, lineups,
  events, standings, leaderboards, and cup bracket query families.
- Finished matches show a lock message and keep normal edit/delete/generate
  buttons disabled.
- Lineup and protocol sections remain placeholders for the next dedicated
  workflow layers.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Match Lineups Slice

- Added lineup workflows to `/app/matches/:matchId`.
- Match detail now loads real lineup entries from
  `GET /api/v1/matches/{match_id}/lineups`.
- Added manual lineup entry through `POST /api/v1/matches/{match_id}/lineups`,
  limited to the match participant teams and their players in the UI.
- Added lineup deletion through `DELETE /api/v1/lineups/{lineup_id}` with
  confirmation.
- Added generated lineup action through
  `POST /api/v1/matches/{match_id}/lineups/generate`, including lineup size,
  starting size, team selection, and replace-existing flag.
- Backend validation remains authoritative for suspended players, duplicate
  players, duplicate numbers, participant-team checks, and goalkeeper rules.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Match Protocol And Finish Slice

- Added match protocol workflows to `/app/matches/:matchId`.
- Match detail now loads real protocol events from
  `GET /api/v1/matches/{match_id}/events`.
- Added manual protocol event creation through
  `POST /api/v1/matches/{match_id}/events`, including team, player, event type,
  optional assist player, and minute.
- Added event deletion through `DELETE /api/v1/events/{event_id}` with
  confirmation.
- Added finish workflow through `POST /api/v1/matches/{match_id}/finish` with
  home and away score inputs.
- Backend validation remains authoritative for participant-team/player checks,
  assist-player checks, finished-match immutability, and final-score versus goal
  event consistency.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Championship Workspace Slice

- Replaced the `/app/championship` placeholder with a real championship
  workspace page.
- The page now loads seasons, championship tournaments, teams, stadiums,
  standings, season schedule, and player leaderboards from backend endpoints.
- Added championship schedule generation through
  `POST /api/v1/schedule/championships/{tournament_id}/generate`.
- Schedule generation includes start date/time, interval days, selected teams,
  and optional fallback stadium.
- Added standings table with separate played, wins, draws, losses,
  goals-scored, goals-conceded, goal-difference, and points columns.
- Added standings recalculation through
  `POST /api/v1/standings/seasons/{season_id}/recalculate`.
- Added full-season simulation through
  `POST /api/v1/seasons/{season_id}/generate-protocols`.
- Added basic player leaderboards by goals, assists, saves, yellow cards, and
  red cards.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Cup Workspace Slice

- Replaced the `/app/cup` placeholder with a real cup workspace page.
- The page now loads seasons, cup tournaments, teams, stadiums, and cup bracket
  state from backend endpoints.
- Added cup semifinal generation through
  `POST /api/v1/cups/{tournament_id}/semifinals`.
- Semifinal generation supports manual four-team selection or automatic
  previous-season-place selection, two match datetimes, and optional fallback
  stadium.
- Added cup final generation through
  `POST /api/v1/cups/{tournament_id}/final`, with final datetime and stadium.
- Added bracket view for semifinals, final, winners, champion, and links to
  match detail pages.
- Backend validation remains authoritative for duplicate brackets, unfinished
  semifinals, drawn semifinals, calendar conflicts, stadium resolution, and
  owner-scoped linked resources.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`

### Rebuild Decision

- Agreed that the existing `frontend/` app is a draft and should not be
  polished further.
- The draft frontend remains in the repository for now and must be deleted only
  after explicit user confirmation.
- The replacement frontend will be built from scratch as a dark organizer
  workspace, not as a Tournify-inspired public tournament page.
- The expected stack remains:
  - Vite
  - React
  - TypeScript
  - React Router
  - TanStack Query
  - `lucide-react`
  - plain CSS
  - dark-only UI
- Docker Compose must keep a frontend service.

### New UX Decisions

- Unauthenticated users may view only a read-only public preview of the app
  layout and tabs.
- Public preview must not load protected backend data and must not allow any
  create/update/delete/generate/simulate/finish action.
- Preview actions are disabled or route the user to login/register.
- Authenticated workspace routes remain JWT-protected.
- A dedicated team detail page is required.
- Team detail must show team profile data, emblem, home stadium relation,
  roster, recent/upcoming matches, and related standings/stat snippets where
  available.

### Documentation Updated

- Replaced `docs/FRONTEND_CONTEXT.md` with the new frontend product direction.
- Replaced `docs/FRONTEND_ARCHITECTURE.md` with the planned replacement
  architecture.
- Replaced `docs/FRONTEND_BUGS.md` to preserve previous draft issues as
  historical context and define risks for the rebuild.
- Replaced `docs/FRONTEND_REFERENCE_TOURNIFY.md` to explicitly retire Tournify
  as a design source.
- Replaced `docs/NEXT_CHAT_PROMPT.md` with a clean continuation prompt.

### Next Step

Wait for explicit user confirmation before deleting `frontend/` and creating
the new frontend.

## Historical Note

The previous frontend pass included auth, dashboard, CRUD pages, matches,
championship, cup, and Docker Compose integration. It also had fixes for
paginated list loading and mobile matches overflow. These findings should
inform the rebuild, but the old UI code should not be treated as the base for
the new implementation.

### Season Rollover UI

- Added a `Следующий сезон` action to the seasons catalog.
- The rollover form pre-fills a next season name/date range from the source
  season, resets status to `planned`, and enables tournament copying by
  default.
- Successful rollover shows a short success notice with the created season name
  and copied tournament count.
- Frontend API types/endpoints now include the season rollover response and
  payload.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build backend frontend`
  - backend live smoke confirmed rollover behavior; in-app browser login smoke
    was blocked by the browser environment clipboard bridge, not by app code.

### Error Message Polish

- Ran a live API smoke for remaining workflow conflicts against a temporary
  smoke organizer.
- Confirmed backend detail strings for duplicate season/stadium/referee/
  tournament names, same-team match creation, team calendar conflicts, referee
  parallel conflicts, championship generation conflicts, and duplicate cup
  semifinals.
- Expanded frontend API error translation for exact backend strings that were
  previously not matched:
  - referee duplicate `full_name`;
  - tournament duplicate in a season;
  - same home/away team match;
  - parallel referee conflict;
  - common championship schedule and cup generation failures.
- Verified:
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`
