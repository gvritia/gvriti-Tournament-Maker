# Tournament Maker Backend

Backend - серверная часть учебной системы Tournament Maker. Приложение управляет футбольными сезонами, чемпионатом, кубком, командами, игроками, стадионами, судьями, матчами, составами, протоколами, турнирной таблицей и статистикой игроков.

## Возможности backend

- JWT-регистрация и вход пользователя;
- хранение паролей в виде bcrypt-хеша;
- изоляция данных организаторов через `owner_id`;
- CRUD для сезонов, команд, игроков, стадионов, судей и турниров;
- создание и редактирование матчей;
- назначение судей с проверкой занятости;
- расчет и ручное изменение цены билета;
- генерация расписания чемпионата;
- генерация полуфиналов и финала кубка;
- ручное и автоматическое формирование составов;
- ведение протокола матча;
- генерация случайного результата;
- пересчет турнирной таблицы;
- пересчет статистики игроков;
- demo-наполнение из CSV-файлов.

## Технологии

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- pydantic-settings
- python-jose
- passlib/bcrypt
- pytest
- ruff
- black

## Структура backend

```text
app/core          настройки, безопасность, константы, исключения
app/db            база SQLAlchemy и создание сессий
app/models        ORM-модели SQLAlchemy
app/schemas       Pydantic-схемы запросов и ответов
app/api           FastAPI-маршруты и зависимости
app/repositories  слой доступа к данным
app/services      бизнес-логика приложения
app/scripts       служебные скрипты, включая demo-seed
alembic           миграции базы данных
tests             автоматические тесты pytest
```

## Первый запуск

Из корня проекта запустить PostgreSQL:

```powershell
docker compose up -d db
```

Подготовить backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Проверить запуск:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok","service":"Tournament Maker Backend"}
```

## Документация API

После запуска backend доступны:

- Swagger UI: `http://127.0.0.1:8000/docs`;
- ReDoc: `http://127.0.0.1:8000/redoc`;
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`.

## Demo-данные

```powershell
cd backend
python -m app.scripts.seed_demo_data `
  --clubs-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_clubs.csv" `
  --squads-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_squads.csv"
```

Для генерации полного расписания чемпионата:

```powershell
python -m app.scripts.seed_demo_data `
  --clubs-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_clubs.csv" `
  --squads-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_squads.csv" `
  --generate-championship-schedule
```

Demo-пользователь:

```text
email: demo@example.com
password: DemoPass123
```

## Пример входа через API

```powershell
$token = (Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"demo@example.com","password":"DemoPass123"}').access_token

$headers = @{ Authorization = "Bearer $token" }
```

Проверка защищенных маршрутов:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/v1/seasons/ -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/v1/teams/ -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/v1/matches/ -Headers $headers
```

## Тесты и проверки

```powershell
cd backend
pytest
ruff check .
black --check .
alembic check
```

## Основные HTTP-статусы

- `200 OK` - успешное чтение, изменение или действие;
- `201 Created` - создание ресурса;
- `204 No Content` - удаление;
- `400 Bad Request` - некорректный бизнес-запрос;
- `401 Unauthorized` - отсутствует или неверен JWT;
- `403 Forbidden` - нет доступа;
- `404 Not Found` - ресурс не найден;
- `409 Conflict` - конфликт уникальности или расписания;
- `422 Unprocessable Entity` - ошибка валидации входных данных.
