# Next Chat Prompt

Use this prompt in a fresh Codex chat when continuing the project.

```text
Ты работаешь над учебным проектом Tournament Maker.

Репозиторий:
C:\Users\user\PycharmProjects\gvriti - Tournament Maker

Сначала обязательно прочитай:
- AGENTS.md
- docs/PROJECT_CONTEXT.md
- docs/ARCHITECTURE.md
- docs/DEVELOPMENT_LOG.md
- docs/ACCEPTANCE_CASES.md
- docs/BACKEND_REVIEW_LOG.md
- docs/FRONTEND_CONTEXT.md
- docs/FRONTEND_ARCHITECTURE.md
- docs/FRONTEND_DEVELOPMENT_LOG.md
- docs/FRONTEND_BUGS.md
- docs/FRONTEND_REFERENCE_TOURNIFY.md
- docs/NEXT_CHAT_PROMPT.md

Перед изменениями:
- Проверь `git status`.
- Не трогай `.idea/*`.
- Не откатывай чужие изменения.
- Продолжай frontend маленькими проверяемыми слоями.
- После каждого frontend-слоя запускай:
  `cd frontend`
  `cmd /c npm run build`
  `cmd /c npm audit`
- Если нужно проверить Docker frontend после правки, используй:
  `docker compose build --pull=false frontend`
  `docker compose up -d --no-build frontend`

Текущее состояние backend:
- JWT auth: register/login/current user.
- User-scoped данные через `owner_id`.
- CRUD: seasons, teams, players, stadiums, referees, tournaments, matches.
- Teams имеют optional `emblem_url`.
- Новые пользователи получают 20 стартовых команд, 360 стартовых игроков,
  20 домашних стадионов, starter pool судей и logo URL.
- Match actions: reschedule, assign referee, ticket price, delete.
- Finished matches нельзя редактировать обычными действиями.
- Championship schedule generation:
  `POST /api/v1/schedule/championships/{tournament_id}/generate`.
- One-match protocol generation:
  `POST /api/v1/matches/{match_id}/generate-protocol`.
- Full-season simulation:
  `POST /api/v1/seasons/{season_id}/generate-protocols`.
- Lineups: manual/generate, exactly one starting goalkeeper.
- Protocol events, finish match, standings/statistics refresh.
- Cup: semifinals, final, bracket.
- Season rollover:
  `POST /api/v1/seasons/{season_id}/rollover`.
- Rollover creates a new season, can copy tournaments as planned, and reuses
  user-scoped teams/players/stadiums/referees instead of cloning them.
- Demo login: `demo@example.com` / `DemoPass123`.

Текущее состояние frontend:
- Vite + React + TypeScript.
- React Router.
- TanStack Query.
- lucide-react.
- plain CSS.
- dark-only organizer workspace.
- Docker frontend service работает на `http://127.0.0.1:5173`.
- Backend работает на `http://127.0.0.1:8000`.
- Public preview доступен без входа и не читает protected backend data.
- Preview actions disabled или ведут на login/register.
- Auth подключен:
  - `/login`;
  - `/register`;
  - JWT token в localStorage;
  - `/auth/me`;
  - logout очищает token и TanStack Query cache.
- Protected workspace под `/app/*`.
- Dashboard грузит реальные user-scoped seasons, teams, matches.
- Header имеет переключатель RU/EN; выбранный язык хранится в localStorage.
- Shell и championship workspace подключены к language provider.
- Championship full-season simulation показывает in-page progress panel после
  подтверждения и до ответа backend.
- Fresh user onboarding smoke пройден:
  - регистрация нового пользователя работает;
  - новый пользователь сразу получает 20 команд, 360 игроков, 20 домашних
    стадионов и 20 logo URL;
  - seasons/tournaments/matches у нового пользователя пустые до ручной настройки;
  - dashboard показывает notice, что стартовые команды уже созданы и их можно редактировать.
- Mobile smoke после логотипов/onboarding notice пройден на 390px:
  - dashboard, teams, players, stadiums, matches, championship, cup;
  - page-level horizontal overflow не найден;
  - кнопки, mode chips и notices не обрезают текст на проверенном viewport.
- Human-friendly error smoke частично пройден и исправлен:
  - duplicate team name показывает русское сообщение;
  - invalid team emblem URL показывает русскую field error;
  - duplicate player shirt number показывает русское сообщение;
  - временный smoke player удален после проверки.
- Human-friendly error smoke продолжен:
  - duplicate season/stadium/referee/tournament names проверены;
  - same-team match create проверен;
  - team calendar conflict проверен;
  - referee parallel conflict проверен;
  - championship generation conflict проверен;
  - duplicate cup semifinals проверен;
  - frontend API translation map расширен под фактические backend detail strings.
- Human-friendly error smoke для match-detail workflow продолжен:
  - duplicate lineup player/number проверены live API smoke;
  - suspended player проверен live API smoke;
  - finish score mismatch проверен live API smoke;
  - generate protocol без доступного referee проверен live API smoke;
  - frontend API translation map расширен под lineups/protocol/random-result
    backend detail strings;
  - временный smoke organizer удалён из PostgreSQL после проверки.
- Исправлен источник проблемы, где test/starter пользователи видели команды,
  но не видели игроков:
  - `StarterDataService` теперь создаёт 11 игроков на каждую стартовую команду;
  - существующие Docker test/starter аккаунты с 20 командами и 0 игроков
    backfill-нуты до 360 игроков;
  - dashboard onboarding notice теперь упоминает стартовых игроков;
  - demo user с импортированными 675 игроками не изменялся.
- Исправлена генерация полуфиналов кубка:
  - даты из формы теперь считаются предпочтительными слотами;
  - если команда занята в этот день или достигла недельного лимита, backend
    ищет ближайшую свободную дату вперёд в то же время;
  - добавлены backend tests для same-day и weekly-limit conflicts.
- Исправлена симуляция сезона:
  - если часть матчей уже завершена, backend теперь пропускает finished,
    cancelled и already-protocolled matches;
  - генерируются только оставшиеся чистые матчи;
  - one-match generation остаётся строгой и не перезаписывает готовый протокол.
- CRUD реализован для:
  - referees;
  - seasons;
  - stadiums;
  - teams;
  - players;
  - tournaments.
- Seasons catalog имеет action `Следующий сезон`:
  - prefill следующего имени/дат;
  - checkbox копирования турниров;
  - success notice с количеством скопированных турниров.
- Matches list реализует:
  - create;
  - reschedule;
  - assign referee;
  - ticket price update;
  - delete;
  - filters;
  - disabled normal actions for finished matches.
- Match detail реализует:
  - summary;
  - reschedule;
  - assign referee;
  - ticket price update;
  - delete;
  - generate protocol;
  - lineups list/add/delete/generate;
  - protocol events list/add/delete;
  - finish match.
- Championship реализует:
  - generate schedule;
  - standings;
  - season simulation;
  - schedule table;
  - leaderboards.
- Cup реализует:
  - generate semifinals;
  - generate final;
  - bracket view.
- Large tables теперь используют shared `DataTable` pagination/loading:
  - players: 50 rows/page;
  - matches: 50 rows/page;
  - championship schedule: 50 rows/page;
  - leaderboards: 25 rows/page.
- Dashboard/catalog/team-detail таблицы имеют loading states.
- Mobile/control CSS слегка усилен: filters and table pager не должны расширять page-level width.

Последние проверенные команды:
- `.venv\Scripts\python.exe -m pytest backend/tests/test_crud.py backend/tests/test_owner_scope.py -q`
- `cmd /c npm run build`
- `cmd /c npm audit`
- `docker compose build --pull=false backend`
- `docker compose build --pull=false frontend`
- `docker compose up -d --no-build backend frontend`
- live Docker API smoke: season rollover on demo user with temporary seasons/tournaments, then cleanup verified.
- live Docker API smoke: conflict/error details for duplicate catalog rows,
  match conflicts, championship generation, and cup duplicate semifinals.
- live Docker API smoke: lineup/protocol/random-result error details on a
  temporary organizer, then cleanup verified.
- live Docker API smoke: newly registered user receives 20 teams and 360
  players, then cleanup verified.
- live Docker API smoke: newly registered user receives 360 players; a
  follow-up match protocol generated after a red-card suspension and skipped
  the suspended player; temporary user cleanup verified.
- `.venv\Scripts\python.exe -m pytest backend/tests/test_cups.py -q`
- `.venv\Scripts\python.exe -m ruff check backend/app/services/cup_service.py backend/tests/test_cups.py`
- `.venv\Scripts\python.exe -m pytest backend/tests/test_random_results.py -q`
- `.venv\Scripts\python.exe -m ruff check backend/app/services/random_result_service.py backend/tests/test_random_results.py`
- `.venv\Scripts\python.exe -m black --check backend/app/services/random_result_service.py backend/tests/test_random_results.py`
- live Docker API smoke: season simulation skipped one already-finished match,
  generated one remaining match, then cleanup verified.
- `docker compose build --pull=false backend`
- `docker compose up -d --no-build backend`
- `docker compose build --pull=false frontend`
- `docker compose up -d --no-build frontend`
- 2026-05-21 latest slice:
  - frontend API client now supports per-action timeouts;
  - full-season generation uses a 120s timeout, so it should not show a false
    connection error while the backend continues generating;
  - one-match protocol generation uses 30s, championship schedule and cup
    generation use longer timeouts;
  - dashboard/internal copy no longer shows `backend scope`;
  - match detail no longer shows the missing-referee notice while the referees
    query is still loading;
  - live API smoke confirmed demo user has 8 referees;
  - browser smoke confirmed `/app/referees` displays demo referees and mobile
    `/app` has no page-level horizontal overflow at `390x844`;
  - added backend regression tests in `backend/tests/test_random_results.py`
    for cancelled-match skipping, red-card substitute selection, invalid
    existing lineups, missing goalkeeper, and missing-referee full-season
    rollback/no partial events.
- 2026-05-21 latest follow-up:
  - starter/test users now receive starter referees automatically at
    registration;
  - negative missing-referee tests explicitly delete the starter referee pool;
  - header RU/EN toggle added;
  - championship page has a progress panel for "generate season remainder";
  - `backend/tests/test_crud.py` was formatted, so full black check now passes.
- Latest verification:
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py backend/tests/test_random_results.py -q`
  - `.venv\Scripts\python.exe -m pytest backend/tests/test_lineups.py backend/tests/test_cups.py -q`
  - `.venv\Scripts\python.exe -m ruff check backend/app backend/tests`
  - `.venv\Scripts\python.exe -m black --check backend/app backend/tests`
  - `cmd /c npm run build`
  - `cmd /c npm audit`
  - `docker compose build --pull=false backend`
  - `docker compose up -d --no-build backend`
  - `docker compose build --pull=false frontend`
  - `docker compose up -d --no-build frontend`
  - live Docker API smoke: new temporary starter user received
    `20,360,20,8` teams/players/stadiums/referees; temp user cleanup verified.
  - browser smoke: public shell RU/EN toggle worked and checked viewport had
    no page-level horizontal overflow; authenticated browser login smoke was
    blocked by the in-app browser clipboard bridge.

Свежий слой 2026-05-21 (SCSS + visual polish + GitHub Pages):
- `frontend/src/styles` переведена с одного `global.css` на модульный
  SCSS (`_tokens`, `_mixins`, `_reset`, `_layout`, `_panels`, `_buttons`,
  `_forms`, `_tables`, `_notices`, `_components`), entry — `global.scss`.
- В `frontend/package.json` добавлена `sass ^1.83`; перед билдом нужно
  один раз запустить `cmd /c npm install`.
- React-структура не менялась, только класс-стили; функционал тот же.
- Vite получил конфигурируемый `base` и режим `pages`
  (`npm run build:pages`); `.env.pages` задаёт hash routing,
  `VITE_BASE_PATH=/gvriti-Tournament-Maker/` и placeholder API URL.
- `App.tsx` → `createHashRouter` в режиме pages.
- `AuthProvider` игнорирует `localStorage` токен в режиме pages.
- `AuthPage` показывает понятный notice в режиме pages.
- `public/404.html` — SPA fallback, переписывает unknown path на корень.
- `.github/workflows/frontend-pages.yml` собирает и деплоит SPA на GH
  Pages. Один раз в репозитории: Settings → Pages → Source = "GitHub
  Actions".
- Локальные команды: `cmd /c npm install && cmd /c npm run build` для
  Docker-сборки и `cmd /c npm run build:pages` для проверки pages-режима
  до пуша.

Рекомендуемый следующий маленький шаг:
0. Локально на Windows:
   - `cd frontend && cmd /c npm install` (поставит `sass`);
   - `cmd /c npm run build` — обычная Docker-сборка должна пройти;
   - `cmd /c npm run build:pages` — проверка GH Pages сборки.
   - Если frontend перебирается под Docker:
     `docker compose build --pull=false frontend &&
      docker compose up -d --no-build frontend`.
0a. В репозитории GitHub: Settings → Pages → Source = "GitHub Actions",
    затем push в `master`. Через 1–2 минуты сайт будет доступен по
    `https://gvritia.github.io/gvriti-Tournament-Maker/`.
1. Прогнать live browser smoke на временном starter user'е для реальных
   UI-level ошибок генерации:
   - existing protocol events;
   - invalid existing lineups;
   - missing players / goalkeeper / field players;
   - season simulation conflicts;
   - missing referees.
   Временного пользователя удалить после проверки.
2. Проверить match create/edit/detail формы с demo user'ом:
   - `/app/referees` показывает demo referees;
   - assign referee dropdown содержит demo referees;
   - match create optional referee select содержит demo referees;
   - one-match generate protocol работает для championship и cup матчей.
3. Продолжить вынос видимых строк в language provider маленькими слоями:
   CRUD pages, match detail, cup, dashboard.
4. После frontend-слоя запустить `cmd /c npm run build`, `cmd /c npm audit`;
   если менялся Docker-served frontend, выполнить
   `docker compose build --pull=false frontend` и
   `docker compose up -d --no-build frontend`.

Важно:
- Не реализуй всё приложение разом.
- Backend validation остается source of truth.
- Не показывай normal users raw API URLs или stack traces.
- Dangerous actions должны иметь confirmation.
- Mobile не должен иметь page-level horizontal overflow.
- Не трогай `.idea/*`.
```
