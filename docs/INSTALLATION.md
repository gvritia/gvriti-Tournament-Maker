# Установка и настройка

Документ описывает базовый порядок установки и настройки Tournament Maker для локального запуска.

## Требования

- Git;
- Python 3.11 или выше;
- Docker и Docker Compose;
- Node.js и npm для запуска frontend;
- доступ к CSV-файлам demo-данных при необходимости наполнения базы.

## Получение проекта

```powershell
git clone https://github.com/gvritia/gvriti-Tournament-Maker.git
cd gvriti-Tournament-Maker
```

## Подготовка backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Файл `.env` содержит настройки подключения к базе данных, JWT-секрет, префикс API и CORS-адреса.

## Запуск базы данных

```powershell
cd ..
docker compose up -d db
```

PostgreSQL запускается на локальном порту `55432`.

## Применение миграций

```powershell
cd backend
alembic upgrade head
```

## Запуск backend

```powershell
uvicorn app.main:app --reload
```

Проверка:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Запуск frontend

```powershell
cd ..\frontend
npm install
npm run dev
```

Frontend доступен по адресу `http://127.0.0.1:5173`.

## Запуск всего проекта

```powershell
docker compose up --build
```

Эта команда запускает PostgreSQL, backend и frontend.
