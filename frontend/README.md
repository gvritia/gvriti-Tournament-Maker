# Tournament Maker Frontend

Frontend - клиентская часть Tournament Maker, реализованная на React, TypeScript и Vite. Интерфейс используется для работы организатора с backend API: авторизации, просмотра и управления сезонами, командами, игроками, стадионами, судьями, турнирами, матчами, расписанием, кубком, турнирной таблицей и статистикой.

## Технологии

- React;
- TypeScript;
- Vite;
- React Router;
- TanStack Query;
- SCSS;
- lucide-react.

## Запуск

```powershell
npm install
npm run dev
```

По умолчанию frontend доступен по адресу:

```text
http://127.0.0.1:5173
```

## Переменные окружения

Основной адрес backend API:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

При запуске через Docker Compose переменная задается в `docker-compose.yml`.

## Сборка

```powershell
npm run build
```

## Основные разделы интерфейса

- вход и регистрация;
- dashboard организатора;
- сезоны;
- команды;
- игроки;
- стадионы;
- судьи;
- турниры;
- матчи;
- детальная страница матча;
- чемпионат;
- кубок.
