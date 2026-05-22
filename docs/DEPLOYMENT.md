# Ввод в эксплуатацию

Документ описывает демонстрационный ввод Tournament Maker в эксплуатацию в локальной среде.

## Подготовка

Перед запуском необходимо:

- установить зависимости backend;
- создать файл `backend/.env`;
- запустить PostgreSQL;
- применить миграции Alembic.

Минимальная последовательность:

```powershell
docker compose up -d db
cd backend
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Проверка запуска

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok","service":"Tournament Maker Backend"}
```

## Demo-наполнение

```powershell
python -m app.scripts.seed_demo_data `
  --clubs-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_clubs.csv" `
  --squads-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_squads.csv"
```

Для генерации полного расписания чемпионата можно добавить параметр:

```powershell
--generate-championship-schedule
```

## Основной эксплуатационный сценарий

1. Пользователь регистрируется или входит в систему.
2. Backend выдает JWT-токен.
3. Пользователь создает или выбирает сезон.
4. Добавляются команды, игроки, стадионы и судьи.
5. Создается чемпионат или кубковый турнир.
6. Формируется расписание матчей.
7. Заполняются составы и протоколы матчей.
8. Матч завершается вручную или через генерацию результата.
9. Система пересчитывает турнирную таблицу и статистику игроков.

## Контейнерный запуск

```powershell
docker compose up --build
```

Этот способ удобен для демонстрации, так как поднимает PostgreSQL, backend и frontend одной командой.
