# Tournament Maker

Tournament Maker - учебная система для организации футбольного чемпионата и кубкового турнира. Проект включает backend на FastAPI, базу данных PostgreSQL, миграции Alembic, JWT-авторизацию, автоматические тесты и клиентскую часть на React.

## Возможности

- регистрация и вход организатора соревнований;
- изоляция данных разных пользователей через `owner_id`;
- управление сезонами, командами, игроками, стадионами, судьями и турнирами;
- создание матчей чемпионата и кубка;
- генерация расписания чемпионата;
- генерация полуфиналов и финала кубкового турнира;
- работа с составами команд и протоколами матчей;
- расчет цены билета;
- генерация случайных результатов матчей;
- пересчет турнирной таблицы и статистики игроков;
- демонстрационное наполнение данными;
- frontend-интерфейс для основных пользовательских сценариев.

## Технологии

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT, passlib/bcrypt, python-jose
- pytest, ruff, black
- React, TypeScript, Vite
- Docker Compose

## Структура проекта

```text
backend/      серверная часть FastAPI
frontend/     клиентская часть React/Vite
docs/         проектная и эксплуатационная документация
.github/      конфигурация GitHub Actions
docker-compose.yml
```

## Быстрый запуск через Docker Compose

```powershell
docker compose up --build
```

После запуска:

- backend: `http://127.0.0.1:8000`;
- Swagger UI: `http://127.0.0.1:8000/docs`;
- frontend: `http://127.0.0.1:5173`.

## Локальный запуск backend

```powershell
docker compose up -d db
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Проверка backend:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Локальный запуск frontend

```powershell
cd frontend
npm install
npm run dev
```

## Demo-данные

Для заполнения проекта demo-данными используется скрипт:

```powershell
cd backend
python -m app.scripts.seed_demo_data `
  --clubs-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_clubs.csv" `
  --squads-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_squads.csv"
```

Demo-пользователь по умолчанию:

```text
email: demo@example.com
password: DemoPass123
```

## Проверка проекта

```powershell
cd backend
pytest
ruff check .
black --check .
alembic check
```

## Документация

Основная документация находится в папке `docs/`.

- `docs/README.md` - навигация по документации;
- `backend/README.md` - инструкция по backend;
- `frontend/README.md` - инструкция по frontend;
- `docs/PROJECT_CONTEXT.md` - предметная область и бизнес-правила;
- `docs/ARCHITECTURE.md` - архитектура проекта;
- `docs/ACCEPTANCE_CASES.md` - приемочные сценарии.
