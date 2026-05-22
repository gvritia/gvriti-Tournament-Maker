# Глава 3. Этапы создания программного продукта Tournament Maker

## Назначение документа

Этот файл является развернутой заготовкой для написания раздела курсовой работы
по приложению **Tournament Maker**. Текст можно использовать как основу для
дальнейшего анализа, переработки и адаптации под требования методических
указаний. В документе описаны этапы создания программного продукта:
разработка составных элементов, установка и настройка, тестирование, ввод в
эксплуатацию и разработка сопроводительной документации.

Tournament Maker представляет собой backend-систему для организации футбольного
чемпионата и кубкового турнира. Приложение позволяет регистрировать
организаторов, управлять сезонами, командами, игроками, стадионами, судьями,
турнирами, матчами, составами, протоколами матчей, турнирной таблицей,
стоимостью билетов, расписанием и статистикой игроков. Основной стек проекта:
Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, Pydantic v2, JWT,
pytest, ruff, black и Docker Compose.

Все упоминания функций, модулей и подсистем сопровождаются указанием файла, в
котором они реализованы или на который опирается соответствующая часть
приложения.

## 3.1 Разработка составных элементов

### Общая архитектура приложения

При разработке Tournament Maker была выбрана многослойная архитектура backend
приложения. Такой подход разделяет ответственность между слоями и упрощает
поддержку проекта. В приложении выделены следующие основные слои:

- слой запуска и конфигурации FastAPI-приложения (`backend/app/main.py`);
- слой маршрутизации API версии v1 (`backend/app/api/v1/router.py`);
- слой HTTP-эндпоинтов для отдельных предметных областей
  (`backend/app/api/v1/endpoints/*.py`);
- слой Pydantic-схем для валидации входных данных и формирования ответов
  (`backend/app/schemas/*.py`);
- слой бизнес-логики сервисов (`backend/app/services/*.py`);
- слой репозиториев для доступа к базе данных
  (`backend/app/repositories/*.py`);
- слой SQLAlchemy ORM-моделей (`backend/app/models/*.py`);
- слой подключения к базе данных (`backend/app/db/session.py`);
- слой общих настроек, безопасности и доменных исключений
  (`backend/app/core/*.py`);
- слой миграций базы данных (`backend/alembic/versions/*.py`);
- слой автоматических тестов (`backend/tests/*.py`).

Точка входа приложения создается функцией `create_app`, которая настраивает
экземпляр FastAPI, описание OpenAPI, CORS, healthcheck и подключение основного
API-роутера (`backend/app/main.py`). Основной роутер `api_router` подключает
предметные маршруты: авторизацию, пользователей, сезоны, команды, игроков,
стадионы, судей, турниры, матчи, составы, протоколы, случайные результаты,
кубок, расписание, турнирную таблицу и статистику
(`backend/app/api/v1/router.py`).

Ключевой архитектурный принцип проекта заключается в том, что HTTP-эндпоинты
остаются тонкими: они принимают запрос, валидируют входные данные через схемы,
получают текущего пользователя, вызывают сервис и возвращают ответ. Бизнес-логика
находится в сервисах, а работа с SQL-запросами вынесена в репозитории. Например,
создание матча вызывается через endpoint `create_match`
(`backend/app/api/v1/endpoints/matches.py`), а основная логика создания,
проверки команд, турнира, стадиона, календарных ограничений и цены билета
выполняется в методе `create_match` класса `MatchService`
(`backend/app/services/match_service.py`).

### Подсистема конфигурации и запуска

Конфигурация приложения реализована через Pydantic Settings. Класс `Settings`
считывает переменные окружения: название приложения, режим работы, префикс API,
разрешенные CORS-источники, настройки JWT и строку подключения к PostgreSQL
(`backend/app/core/config.py`). Это позволяет запускать один и тот же код в
локальной среде, тестовой среде, Docker-контейнере и CI.

Для подключения к базе данных используется SQLAlchemy engine и sessionmaker.
Функция `get_db` создает сессию, передает ее в зависимости FastAPI, выполняет
rollback при ошибке и закрывает соединение после обработки запроса
(`backend/app/db/session.py`). Такой подход обеспечивает контролируемую работу
с транзакциями и предотвращает утечки соединений.

Основной healthcheck `/health` возвращает статус сервиса и используется для
быстрой проверки работоспособности API (`backend/app/main.py`). Префикс
основной версии API задан как `/api/v1` (`backend/app/core/config.py`).

### Подсистема авторизации и пользователей

Авторизация построена на JWT-токенах. Регистрация пользователя выполняется через
endpoint `register` (`backend/app/api/v1/endpoints/auth.py`). В сервисном слое
метод `AuthService.register` проверяет уникальность email и nickname, хеширует
пароль с помощью bcrypt, создает пользователя и запускает наполнение стартовыми
данными для нового организатора (`backend/app/services/auth_service.py`).

Проверка и хеширование пароля реализованы функциями `validate_bcrypt_password`,
`verify_password` и `get_password_hash` (`backend/app/core/security.py`). При
успешном входе метод `AuthService.create_token_for_user` формирует JWT-токен
через функцию `create_access_token` (`backend/app/services/auth_service.py`,
`backend/app/core/security.py`).

Получение текущего пользователя осуществляется через зависимость
`get_current_user`. Она извлекает bearer-token, декодирует его, получает `sub`,
загружает пользователя из базы и возвращает ошибку `401 Unauthorized`, если
токен отсутствует, поврежден или указывает на удаленного пользователя
(`backend/app/api/deps.py`).

Для новых пользователей предусмотрено автоматическое создание стартового набора
данных: команд, игроков, домашних стадионов и судей. Эта логика реализована в
`StarterDataService.seed_for_new_owner`
(`backend/app/services/starter_data_service.py`). Благодаря этому после
регистрации пользователь сразу получает рабочее пространство, пригодное для
демонстрации расписания, составов, протоколов и статистики.

### Подсистема доменных моделей

Структура базы данных описана через SQLAlchemy ORM-модели. Модель пользователя
хранит nickname, email, хеш пароля, роль и дату создания (`backend/app/models/user.py`).
Сезон содержит название, даты начала и окончания, статус и связь с владельцем
через `owner_id` (`backend/app/models/season.py`). Команда содержит название,
город, адрес, тренера, эмблему, место в прошлом сезоне и связь с игроками,
домашними матчами, гостевыми матчами и статистикой
(`backend/app/models/team.py`).

Игрок хранится как отдельная сущность, связанная с командой через `team_id`
(`backend/app/models/player.py`). Такой подход выбран вместо хранения массива
игроков внутри команды, потому что он лучше соответствует реляционной модели,
позволяет строить запросы по игрокам и упрощает статистику. Стадион содержит
название, город, адрес, вместимость и необязательную домашнюю команду
(`backend/app/models/stadium.py`). Судья хранится как отдельная сущность,
которая может быть назначена на матчи (`backend/app/models/referee.py`).

Турнир относится к сезону и имеет тип: чемпионат или кубок
(`backend/app/models/tournament.py`). Матч хранит турнир, сезон, домашнюю и
гостевую команды, стадион, судью, дату, статус, раунд, стадию кубка, счет,
цену билета, число проданных билетов и доход (`backend/app/models/match.py`).
Состав матча вынесен в отдельную таблицу `MatchLineup`, где фиксируются игрок,
команда, номер, позиция и признак стартового состава
(`backend/app/models/match_lineup.py`). Протокол матча хранится в таблице
`MatchEvent`, где фиксируются голы, ассисты, сейвы, желтые и красные карточки
(`backend/app/models/match_event.py`).

Производные данные вынесены в отдельные таблицы статистики:
`TeamSeasonStats` хранит турнирную таблицу команд за сезон, а
`PlayerSeasonStats` хранит суммарную статистику игроков за сезон
(`backend/app/models/stats.py`). Такой подход позволяет не перегружать модель
команды и игрока полями, которые должны пересчитываться по завершенным матчам.

Перечисления доменных статусов и типов вынесены в `UserRole`, `SeasonStatus`,
`TournamentType`, `TournamentStatus`, `MatchStatus`, `CupStage`,
`MatchEventType` и `PlayerPosition` (`backend/app/core/constants.py`).

### Подсистема схем API

Для описания контрактов API используются Pydantic-схемы. Например, данные
регистрации и входа описаны схемами `RegisterRequest`, `LoginRequest` и `Token`
(`backend/app/schemas/auth.py`). Схемы матчей `MatchCreate`, `MatchUpdate`,
`MatchRead`, `MatchRefereeAssign`, `MatchReschedule` и
`MatchTicketPriceUpdate` описывают создание, редактирование, назначение судьи,
перенос и изменение цены билета (`backend/app/schemas/match.py`).

Схемы составов `MatchLineupCreate`, `MatchLineupUpdate` и
`MatchLineupGenerate` используются для ручного и автоматического формирования
заявки команды на матч (`backend/app/schemas/match_lineup.py`). Схемы протокола
`MatchEventCreate`, `MatchEventUpdate` и `MatchFinish` описывают события матча
и завершение матча с итоговым счетом (`backend/app/schemas/match_event.py`).
Генерация расписания чемпионата описывается схемой
`ChampionshipScheduleGenerate` (`backend/app/schemas/schedule.py`). Генерация
кубковых полуфиналов и финала описывается схемами `CupSemifinalsGenerate` и
`CupFinalGenerate` (`backend/app/schemas/cup.py`).

Отдельные схемы существуют для сезонов, команд, игроков, стадионов, судей,
турниров, статистики и случайных результатов (`backend/app/schemas/season.py`,
`backend/app/schemas/team.py`, `backend/app/schemas/player.py`,
`backend/app/schemas/stadium.py`, `backend/app/schemas/referee.py`,
`backend/app/schemas/tournament.py`, `backend/app/schemas/stats.py`,
`backend/app/schemas/random_result.py`).

### Подсистема доступа к данным

Для работы с базой данных используется слой репозиториев. Базовый класс
`BaseRepository` реализует типовые операции `get`, `list`, `add`, `delete` и
owner-фильтрацию (`backend/app/repositories/base.py`). Owner-фильтрация важна,
потому что все предметные данные должны принадлежать конкретному пользователю
и не должны быть доступны другим организаторам.

Для каждой предметной области реализован отдельный репозиторий: сезоны
(`backend/app/repositories/season.py`), команды
(`backend/app/repositories/team.py`), игроки
(`backend/app/repositories/player.py`), стадионы
(`backend/app/repositories/stadium.py`), судьи
(`backend/app/repositories/referee.py`), турниры
(`backend/app/repositories/tournament.py`), матчи
(`backend/app/repositories/match.py`), составы
(`backend/app/repositories/match_lineup.py`), события протокола
(`backend/app/repositories/match_event.py`) и статистика
(`backend/app/repositories/stats.py`).

Например, репозиторий матчей содержит методы для поиска матчей команды в
интервале дат, поиска параллельного матча судьи, получения матчей сезона,
стадиона, турнира и стадии кубка (`backend/app/repositories/match.py`). Эти
методы используются сервисами расписания, матчей, судейства, кубка,
статистики и генерации результатов.

### Подсистема CRUD для справочников

Базовые CRUD-операции реализованы для сезонов, команд, игроков, стадионов,
судей и турниров. Для сезонов методы `list_seasons`, `get_season`,
`create_season`, `update_season` и `delete_season` инкапсулированы в
`SeasonService` (`backend/app/services/season_service.py`) и вызываются из
эндпоинтов сезонов (`backend/app/api/v1/endpoints/seasons.py`).

Для команд аналогичная логика находится в `TeamService`
(`backend/app/services/team_service.py`) и маршрутах команд
(`backend/app/api/v1/endpoints/teams.py`). При создании команды проверяется
уникальность названия внутри пользователя, а не глобально. Для игроков логика
находится в `PlayerService`, где проверяется существование команды и
уникальность номера игрока внутри команды (`backend/app/services/player_service.py`).

Стадионы обслуживаются через `StadiumService`, который проверяет домашнюю
команду и уникальность названия стадиона в пределах владельца
(`backend/app/services/stadium_service.py`). Судьи обслуживаются через
`RefereeService`, где проверяется уникальность полного имени судьи в пределах
пользователя (`backend/app/services/referee_service.py`). Турниры обслуживаются
через `TournamentService`, где проверяется существование сезона и уникальность
названия турнира внутри сезона пользователя
(`backend/app/services/tournament_service.py`).

### Подсистема матчей

Работа с матчами является одной из центральных частей приложения. Endpoint
`create_match` принимает данные о турнире, сезоне, командах, стадионе, судье,
дате, раунде и статусе (`backend/app/api/v1/endpoints/matches.py`). Метод
`MatchService.create_match` проверяет существование турнира, сезона, команд,
стадиона и судьи в пределах текущего пользователя, запрещает матч команды с
самой собой, проверяет соответствие турнира сезону, проверяет календарные
ограничения и рассчитывает цену билета (`backend/app/services/match_service.py`).

Редактирование матча выполняется методом `MatchService.update_match`
(`backend/app/services/match_service.py`). Перенос матча на другую дату
выделен в отдельный метод `reschedule_match`, чтобы повторно применить
календарные ограничения (`backend/app/services/match_service.py`). Назначение
судьи выполняется методом `assign_referee`, который дополнительно проверяет,
что судья не назначен на другой матч в то же время
(`backend/app/services/match_service.py`,
`backend/app/services/validation_service.py`). Изменение цены билета вручную
выполняется методом `set_manual_ticket_price`
(`backend/app/services/match_service.py`).

Для завершенных матчей запрещены обычное редактирование, перенос, назначение
судьи, изменение цены билета и удаление. Это реализовано через проверку
`_ensure_match_can_be_changed` (`backend/app/services/match_service.py`).
Завершение матча происходит только через протокол или генератор результата,
что защищает целостность статистики (`backend/app/services/match_protocol_service.py`,
`backend/app/services/random_result_service.py`).

### Подсистема расписания чемпионата

Генерация расписания чемпионата реализована в endpoint
`generate_championship_schedule`
(`backend/app/api/v1/endpoints/schedule.py`). Основная логика находится в
`ScheduleService.generate_championship_schedule`
(`backend/app/services/schedule_service.py`). Сервис создает двойной круговой
турнир: каждая команда играет с каждой другой командой дважды, один раз дома и
один раз на выезде. Формирование пар и раундов выполняется методом
`_build_double_round_robin_rounds` (`backend/app/services/schedule_service.py`).

При генерации учитываются доменные ограничения календаря. Метод
`validate_team_can_play_at` проверяет, что команда не играет больше одного
матча в день и больше двух матчей за неделю
(`backend/app/services/schedule_service.py`). Метод `validate_teams_can_play_at`
применяет эту проверку к обеим командам матча
(`backend/app/services/schedule_service.py`). При выборе стадионов сервис
сначала использует домашний стадион команды, затем явную карту стадионов,
затем fallback-стадион, если он передан (`backend/app/services/schedule_service.py`).

Сервис также предоставляет чтение расписания сезона и стадиона. Endpoint
`list_season_matches` возвращает матчи сезона с фильтрами по команде, турниру
и диапазону дат (`backend/app/api/v1/endpoints/schedule.py`,
`backend/app/services/schedule_service.py`). Endpoint `list_stadium_matches`
возвращает расписание конкретного стадиона
(`backend/app/api/v1/endpoints/schedule.py`,
`backend/app/services/schedule_service.py`).

### Подсистема кубкового турнира

Кубковый турнир строится из полуфиналов и финала. Генерация полуфиналов
выполняется endpoint `generate_cup_semifinals`
(`backend/app/api/v1/endpoints/cups.py`), а основная логика находится в методе
`CupService.generate_semifinals` (`backend/app/services/cup_service.py`).
Сервис принимает четыре уникальные команды вручную либо выбирает топ-4 по
полю `previous_season_place` (`backend/app/services/cup_service.py`,
`backend/app/repositories/team.py`). Полуфинальные пары формируются по схеме
`1 против 4` и `2 против 3` (`backend/app/services/cup_service.py`).

Если выбранная дата полуфинала нарушает календарные ограничения команды,
сервис ищет ближайшую доступную дату в будущем в то же время. Эта логика
выполнена методом `_find_available_match_datetime`
(`backend/app/services/cup_service.py`). Создание матчей полуфинала опирается
на метод `_build_match`, который формирует объект `Match` со стадией кубка
`semifinal` (`backend/app/services/cup_service.py`).

Финал кубка создается endpoint `generate_cup_final`
(`backend/app/api/v1/endpoints/cups.py`). Метод `CupService.generate_final`
проверяет, что полуфиналы завершены и имеют явных победителей, после чего
создает финальный матч (`backend/app/services/cup_service.py`). Просмотр сетки
кубка выполняется через endpoint `get_cup_bracket` и метод
`CupService.get_bracket`, который возвращает полуфиналы, финал, победителей и
чемпиона после завершения финала (`backend/app/api/v1/endpoints/cups.py`,
`backend/app/services/cup_service.py`).

### Подсистема составов команд

Составы на матч реализованы как отдельная сущность `MatchLineup`
(`backend/app/models/match_lineup.py`). Ручное добавление игрока в состав
выполняется endpoint `add_player_to_lineup`
(`backend/app/api/v1/endpoints/lineups.py`) и методом
`LineupService.add_player_to_lineup`
(`backend/app/services/lineup_service.py`). При добавлении проверяется, что
команда участвует в матче, игрок принадлежит этой команде, игрок не добавлен
повторно и номер не повторяется внутри состава команды
(`backend/app/services/lineup_service.py`).

Автоматическая генерация состава выполняется endpoint `generate_lineup`
(`backend/app/api/v1/endpoints/lineups.py`) и методом
`LineupService.generate_lineup` (`backend/app/services/lineup_service.py`).
Сервис может учитывать предпочитаемых игроков, пропускать дисквалифицированных,
заполнять свободные места доступными игроками и обеспечивать наличие ровно
одного стартового вратаря. Проверка доступности игрока после красной карточки
или пяти желтых карточек реализована через методы `_ensure_player_is_available`
и `_is_player_available` (`backend/app/services/lineup_service.py`).

### Подсистема протокола матча

Протокол матча хранит игровые события: голы, ассисты, сейвы, желтые карточки и
красные карточки (`backend/app/models/match_event.py`). Добавление события
выполняется endpoint `add_match_event`
(`backend/app/api/v1/endpoints/protocol.py`) и методом
`MatchProtocolService.add_event`
(`backend/app/services/match_protocol_service.py`). При добавлении события
проверяется, что матч существует, еще не завершен, команда участвует в матче,
игрок принадлежит этой команде, а ассистент при голе также относится к
команде-участнику (`backend/app/services/match_protocol_service.py`).

Завершение матча выполняется endpoint `finish_match`
(`backend/app/api/v1/endpoints/protocol.py`) и методом
`MatchProtocolService.finish_match`
(`backend/app/services/match_protocol_service.py`). Сервис сверяет итоговый
счет с количеством записанных голевых событий, меняет статус матча на
`finished`, сохраняет счет и пересчитывает связанные производные данные
(`backend/app/services/match_protocol_service.py`). Если завершен матч
чемпионата, пересчитывается турнирная таблица
(`backend/app/services/standings_service.py`). Если завершен любой матч,
пересчитывается статистика игроков за сезон
(`backend/app/services/statistics_service.py`).

### Подсистема случайной генерации результатов

Для демонстрации и ускоренного наполнения сезона реализована генерация
реалистичного результата матча. Endpoint `generate_random_match_result`
вызывает метод `RandomResultService.generate_for_match`
(`backend/app/api/v1/endpoints/random_results.py`,
`backend/app/services/random_result_service.py`). Сервис проверяет, что матч
не завершен, не отменен, не имеет уже записанных событий и что у обеих команд
есть игроки (`backend/app/services/random_result_service.py`).

Случайный счет формируется методом `_generate_score`, а количество голов
ограничивается реалистичными пределами (`backend/app/services/random_result_service.py`).
Голевые события создаются методом `_generate_goal_events`, события сейвов -
методом `_generate_save_events`, карточки - методом `_generate_card_events`
(`backend/app/services/random_result_service.py`). Для кубковых стадий
дополнительно используется `_break_cup_draw`, чтобы полуфинал или финал не
заканчивался ничьей (`backend/app/services/random_result_service.py`).

Сервис также поддерживает генерацию протокола одного матча через endpoint
`generate_match_protocol` и массовую симуляцию сезона через endpoint
`generate_season_protocols` (`backend/app/api/v1/endpoints/random_results.py`).
Массовая симуляция реализована в методе `RandomResultService.generate_for_season`
(`backend/app/services/random_result_service.py`). Она пропускает завершенные,
отмененные и уже имеющие протокол матчи, автоматически назначает доступного
судью при необходимости, генерирует стартовые составы и пересчитывает
статистику с турнирной таблицей после завершения набора матчей
(`backend/app/services/random_result_service.py`).

### Подсистема турнирной таблицы

Турнирная таблица чемпионата рассчитывается только по завершенным матчам
чемпионата. Endpoint `get_season_standings` возвращает текущую таблицу сезона,
а endpoint `recalculate_season_standings` запускает пересчет вручную
(`backend/app/api/v1/endpoints/standings.py`). Основная логика находится в
`StandingsService` (`backend/app/services/standings_service.py`).

Метод `StandingsService.recalculate_for_season` пересчитывает таблицу сезона,
а метод `rebuild_for_season` используется другими сервисами при завершении
матчей (`backend/app/services/standings_service.py`). Внутри расчета
`TeamStandingAccumulator.record_match` обновляет количество игр, побед, ничьих,
поражений, голов и очков (`backend/app/services/standings_service.py`).
Сортировка таблицы выполняется по очкам, разнице голов, забитым голам и
`team_id` как стабильному последнему критерию
(`backend/app/services/standings_service.py`).

### Подсистема статистики игроков

Статистика игроков рассчитывается на основе событий завершенных матчей.
Endpoint `get_player_stats` возвращает статистику игроков за сезон, endpoint
`recalculate_player_stats` запускает пересчет, а endpoint `get_player_leaders`
возвращает лидеров по выбранному показателю: голам, ассистам, сейвам, желтым
или красным карточкам (`backend/app/api/v1/endpoints/statistics.py`).

Основная логика находится в `StatisticsService`
(`backend/app/services/statistics_service.py`). Метод
`recalculate_player_stats_for_season` удаляет старые производные записи и
создает актуальные значения на основе протоколов (`backend/app/services/statistics_service.py`).
Метод `_build_accumulators` суммирует события игроков, включая явные ассисты и
`assist_player_id` у голевых событий (`backend/app/services/statistics_service.py`).
Метод `get_leaders` проверяет допустимость метрики и возвращает отсортированный
список лидеров (`backend/app/services/statistics_service.py`,
`backend/app/repositories/stats.py`).

### Подсистема расчета цены билетов

Цена билета рассчитывается при создании матча. Формула использует базовую цену,
коэффициент вместимости стадиона и коэффициент уровня клубов
(`backend/app/services/ticket_price_service.py`). Метод
`TicketPriceService.calculate_default_price` рассчитывает значение по формуле:
`(base_price + capacity_factor) * club_coefficient`
(`backend/app/services/ticket_price_service.py`).

Коэффициент вместимости определяется методом `get_capacity_factor`: стадионы
меньше 10 000 мест не получают надбавку, от 10 000 мест получают один уровень,
от 30 000 - следующий, от 60 000 - максимальный
(`backend/app/services/ticket_price_service.py`). Коэффициент клуба определяется
методом `get_club_coefficient` на основе места команды в прошлом сезоне
(`backend/app/services/ticket_price_service.py`). Для матча берется наибольший
коэффициент между домашней и гостевой командой
(`backend/app/services/ticket_price_service.py`).

Ручное изменение цены билета выполняется методом
`MatchService.set_manual_ticket_price` (`backend/app/services/match_service.py`).
После изменения цены или количества проданных билетов метод `_sync_income`
пересчитывает доход матча (`backend/app/services/match_service.py`).

### Подсистема перехода к новому сезону

Для начала нового сезона без повторного ввода всех справочников реализован
`SeasonRolloverService` (`backend/app/services/season_rollover_service.py`).
Endpoint `rollover_season` создает следующий сезон на основе существующего
(`backend/app/api/v1/endpoints/seasons.py`). Метод
`create_next_season` создает новый сезон и при необходимости копирует турниры
исходного сезона со статусом `planned`
(`backend/app/services/season_rollover_service.py`). Команды, игроки, стадионы
и судьи не копируются, потому что они уже являются пользовательскими
справочниками и могут использоваться в нескольких сезонах.

### Подсистема демо-данных

Для наполнения проекта демонстрационными данными используется скрипт
`seed_demo_data` (`backend/app/scripts/seed_demo_data.py`). Он импортирует CSV
с клубами и составами, создает или переиспользует demo-пользователя, сезон,
чемпионат, кубок, команды, стадионы, игроков, судей и кубковые полуфиналы
(`backend/app/scripts/seed_demo_data.py`). При необходимости скрипт может
сгенерировать полное расписание чемпионата через параметр
`--generate-championship-schedule` (`backend/app/scripts/seed_demo_data.py`,
`backend/app/services/schedule_service.py`).

Скрипт поддерживает CSV-файлы с разделителем `;` или табуляцией, несколько
кодировок и импорт эмблем клубов в поле `Team.emblem_url`
(`backend/app/scripts/seed_demo_data.py`). Идемпотентность импорта проверяется
автоматическими тестами (`backend/tests/test_seed_demo_data.py`).

### Подсистема миграций базы данных

Изменения схемы базы данных управляются через Alembic. Конфигурация Alembic
подключает metadata SQLAlchemy и строку подключения из настроек приложения
(`backend/alembic/env.py`). Первая миграция создает базовую схему проекта
(`backend/alembic/versions/b9508a0cd80d_initial_schema.py`). Отдельные миграции
добавляют owner-scope, эмблемы команд и уникальные ограничения внутри владельца
(`backend/alembic/versions/9d3f4e1a6b2c_add_owner_scope.py`,
`backend/alembic/versions/7a1c2e9d4b6f_add_team_emblem_url.py`,
`backend/alembic/versions/4f2a7b91c8e3_add_owner_unique_constraints.py`).

Такой подход позволяет воспроизводимо разворачивать базу данных, применять
изменения в разработке, CI и контейнерной среде, а также контролировать
соответствие моделей фактической структуре БД.

### Подсистема обработки ошибок и HTTP-статусов

В приложении используются собственные доменные исключения `NotFoundError`,
`ConflictError` и `BusinessRuleError` (`backend/app/core/exceptions.py`).
Функция `app_error_to_http_exception` преобразует их в HTTP-ответы: `404 Not
Found`, `409 Conflict` и `400 Bad Request`
(`backend/app/api/errors.py`). Общие константы HTTP-статусов и стандартные
наборы ответов для OpenAPI вынесены в `backend/app/core/status_codes.py`.

Такой подход делает поведение API предсказуемым. Например, отсутствие сущности
или попытка обратиться к чужим данным возвращает `404`, конфликт уникальности
или расписания возвращает `409`, а нарушение бизнес-правил без конфликта
ресурсов возвращает `400`.

### Подсистема изоляции пользовательских данных

Все предметные данные, кроме самой учетной записи пользователя, имеют поле
`owner_id`. Это поле присутствует в моделях сезонов, команд, игроков,
стадионов, судей, турниров, матчей, составов, событий, турнирной таблицы и
статистики (`backend/app/models/*.py`). Репозитории принимают `owner_id` и
автоматически применяют фильтрацию к операциям чтения и списков
(`backend/app/repositories/base.py`).

Эндпоинты получают текущего пользователя через зависимость `CurrentUser`
(`backend/app/api/deps.py`) и передают `current_user.id` в сервисы и
репозитории (`backend/app/api/v1/endpoints/*.py`). Благодаря этому один
организатор не может увидеть, изменить или использовать данные другого
организатора. Проверки изоляции покрыты отдельным набором тестов
(`backend/tests/test_owner_scope.py`).

## 3.2 Установка и настройка

### Требования к окружению

Для локального запуска backend-части приложения требуется:

- Python 3.11 или новее (`backend/pyproject.toml`);
- PostgreSQL, рекомендуемый запуск через Docker Compose (`docker-compose.yml`);
- Docker и Docker Compose для контейнерного запуска (`docker-compose.yml`);
- зависимости Python: FastAPI, SQLAlchemy, Alembic, psycopg, Pydantic,
  pydantic-settings, python-jose, passlib/bcrypt и Uvicorn
  (`backend/pyproject.toml`, `backend/requirements.txt`);
- инструменты разработки и тестирования: pytest, httpx, ruff, black
  (`backend/pyproject.toml`, `backend/requirements-dev.txt`).

### Подготовка базы данных

PostgreSQL поднимается из корня репозитория командой:

```powershell
docker compose up -d db
```

В Docker Compose описан сервис `db`, который использует образ
`postgres:16-alpine`, создает базу `tournament_maker`, пользователя `postgres`
и публикует порт контейнера `5432` на локальный порт `55432`
(`docker-compose.yml`). Использование порта `55432` позволяет избежать
конфликта с локально установленным PostgreSQL.

Сервис базы данных имеет healthcheck через `pg_isready`, поэтому backend в
контейнерном режиме может дождаться готовности PostgreSQL перед запуском
(`docker-compose.yml`).

### Установка зависимостей backend

Локальная установка выполняется из каталога backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Команда `pip install -e ".[dev]"` устанавливает приложение в editable-режиме
и добавляет dev-зависимости для тестирования, форматирования и статического
анализа (`backend/pyproject.toml`). Альтернативно можно установить зависимости
из файла:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
```

Такой вариант удобен, если виртуальное окружение уже создано заранее
(`backend/requirements-dev.txt`).

### Настройка переменных окружения

Перед запуском необходимо создать файл `.env` на основе примера:

```powershell
cd backend
Copy-Item .env.example .env
```

В файле `.env.example` заданы основные параметры: имя приложения, окружение,
debug-режим, API-префикс, CORS-источники, секрет JWT, алгоритм подписи, время
жизни токена и строка подключения к PostgreSQL (`backend/.env.example`).
Приложение считывает эти параметры через класс `Settings`
(`backend/app/core/config.py`).

Для локальной разработки используется строка подключения:

```text
postgresql+psycopg://postgres:postgres@localhost:55432/tournament_maker
```

В production-среде секретный ключ `SECRET_KEY` должен быть изменен. Проверка
секретного ключа реализована в валидаторе `validate_secret_key`
(`backend/app/core/config.py`).

### Применение миграций

После запуска PostgreSQL необходимо применить миграции:

```powershell
cd backend
alembic upgrade head
```

Alembic использует строку подключения из настроек приложения
(`backend/alembic/env.py`). Миграции создают таблицы пользователей, сезонов,
команд, игроков, стадионов, судей, турниров, матчей, составов, событий,
турнирной таблицы и статистики (`backend/alembic/versions/*.py`).

Для проверки, что модели и миграции синхронизированы, используется команда:

```powershell
cd backend
alembic check
```

Эта проверка также выполняется в CI (`.github/workflows/backend-ci.yml`).

### Запуск backend локально

После установки зависимостей и применения миграций backend запускается командой:

```powershell
cd backend
uvicorn app.main:app --reload
```

Uvicorn импортирует объект `app`, который создается в `backend/app/main.py`.
Параметр `--reload` используется в разработке и автоматически перезапускает
сервер при изменении файлов.

Работоспособность проверяется запросом:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok","service":"Tournament Maker Backend"}
```

Healthcheck реализован непосредственно в `create_app`
(`backend/app/main.py`).

### Контейнерный запуск backend

Для запуска PostgreSQL и backend вместе используется команда из корня
репозитория:

```powershell
docker compose up --build backend
```

Сервис `backend` собирается из `backend/Dockerfile`, получает переменные
окружения из `docker-compose.yml`, зависит от готовности сервиса `db` и
публикует порт `8000` (`docker-compose.yml`). В Dockerfile перед запуском
приложения выполняется `alembic upgrade head`, после чего стартует Uvicorn
(`backend/Dockerfile`).

Контейнерный запуск полезен для демонстрации, потому что он снижает зависимость
от локальной конфигурации Python и PostgreSQL.

### Наполнение демо-данными

Для демонстрации проекта можно импортировать подготовленные CSV-файлы с клубами
и составами:

```powershell
cd backend
python -m app.scripts.seed_demo_data `
  --clubs-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_clubs.csv" `
  --squads-csv "C:\Users\user\PycharmProjects\parsing_footbal_clubs\laliga_squads.csv"
```

Скрипт создает demo-пользователя `demo@example.com`, сезон, чемпионат, кубок,
команды, стадионы, игроков, судей и полуфиналы кубка
(`backend/app/scripts/seed_demo_data.py`). При добавлении параметра
`--generate-championship-schedule` скрипт также создает полное расписание
чемпионата (`backend/app/scripts/seed_demo_data.py`,
`backend/app/services/schedule_service.py`).

### Базовая проверка после установки

После запуска можно выполнить базовый сценарий:

1. Проверить `/health` (`backend/app/main.py`).
2. Зарегистрировать пользователя через `/api/v1/auth/register`
   (`backend/app/api/v1/endpoints/auth.py`).
3. Выполнить вход через `/api/v1/auth/login`
   (`backend/app/api/v1/endpoints/auth.py`).
4. Получить текущего пользователя через `/api/v1/auth/me`
   (`backend/app/api/v1/endpoints/auth.py`).
5. Получить список сезонов, команд, игроков и матчей
   (`backend/app/api/v1/endpoints/seasons.py`,
   `backend/app/api/v1/endpoints/teams.py`,
   `backend/app/api/v1/endpoints/players.py`,
   `backend/app/api/v1/endpoints/matches.py`).
6. Сгенерировать результат матча через `/api/v1/matches/{match_id}/generate-random-result`
   (`backend/app/api/v1/endpoints/random_results.py`,
   `backend/app/services/random_result_service.py`).
7. Проверить турнирную таблицу и статистику игроков
   (`backend/app/api/v1/endpoints/standings.py`,
   `backend/app/api/v1/endpoints/statistics.py`).

## 3.3 Тестирование

### Подход к тестированию

В проекте используется автоматическое тестирование с помощью pytest и
FastAPI TestClient (`backend/tests/conftest.py`). Тесты проверяют как
техническое поведение API, так и доменные правила футбольного турнира.

В тестовой конфигурации создается in-memory SQLite-база данных через SQLAlchemy
StaticPool, а зависимость `get_db` подменяется на тестовую сессию
(`backend/tests/conftest.py`). Это позволяет запускать тесты быстро и
изолированно, без необходимости поднимать PostgreSQL для каждого теста.

### Проверка работоспособности API

Базовая доступность сервиса проверяется тестом healthcheck
(`backend/tests/test_health.py`). Он обращается к `/health` и ожидает успешный
ответ со статусом сервиса. В этом же файле проверяется CORS для локальных
frontend-origin, разрешенных настройками приложения
(`backend/tests/test_health.py`, `backend/app/main.py`,
`backend/app/core/config.py`).

### Тестирование авторизации

Авторизация покрыта тестами регистрации, входа и получения текущего
пользователя (`backend/tests/test_auth.py`). Проверяется создание пользователя
с хешированным паролем, конфликт при повторном email, ограничение bcrypt на
длину пароля, выдача bearer-token при корректном входе, отказ при неправильном
пароле и ошибка `401` при отсутствии токена
(`backend/tests/test_auth.py`, `backend/app/services/auth_service.py`,
`backend/app/core/security.py`, `backend/app/api/deps.py`).

Также проверяется ситуация, когда токен указывает на удаленного пользователя.
В этом случае зависимость текущего пользователя должна вернуть
`401 Unauthorized` (`backend/tests/test_auth.py`,
`backend/app/api/deps.py`).

### Тестирование CRUD-операций

CRUD-тесты проверяют справочные сущности: сезоны, команды, игроков, стадионы,
судей и турниры (`backend/tests/test_crud.py`). Для сезонов проверяется
создание, чтение, обновление, удаление и конфликт уникального имени в пределах
пользователя (`backend/tests/test_crud.py`,
`backend/app/services/season_service.py`). Для команд проверяется создание и
редактирование, включая дополнительные поля клуба
(`backend/tests/test_crud.py`, `backend/app/services/team_service.py`).

Для игроков проверяется, что игрок может быть создан только в существующей
команде пользователя, а номер игрока уникален в пределах команды
(`backend/tests/test_crud.py`, `backend/app/services/player_service.py`).
Для стадионов проверяется корректность домашней команды
(`backend/tests/test_crud.py`, `backend/app/services/stadium_service.py`).
Для турниров проверяется существование сезона и уникальность названия турнира
внутри сезона (`backend/tests/test_crud.py`,
`backend/app/services/tournament_service.py`).

Отдельно проверяется переход к новому сезону: создание нового сезона с
копированием турниров или без копирования турниров
(`backend/tests/test_crud.py`,
`backend/app/services/season_rollover_service.py`).

### Тестирование матчей и календарных ограничений

Тесты матчей проверяют успешное создание матча, запрет матча команды с самой
собой, запрет создания матча сразу в статусе `finished`, проверку связи
турнира и сезона, проверку связанных сущностей, перенос матча и назначение
судьи (`backend/tests/test_matches.py`,
`backend/app/services/match_service.py`).

Доменные календарные ограничения проверяются отдельными тестами: команда не
может играть второй матч в тот же день и не может играть третий матч в пределах
одной недели (`backend/tests/test_matches.py`,
`backend/app/services/schedule_service.py`). Назначение судьи проверяется на
конфликт параллельных матчей через `ValidationService.ensure_referee_is_available`
(`backend/tests/test_matches.py`,
`backend/app/services/validation_service.py`).

Также проверяется, что ручная цена билета сохраняется после переноса матча, и
что завершенный матч нельзя редактировать обычными endpoint-ами
(`backend/tests/test_matches.py`, `backend/app/services/match_service.py`).

### Тестирование расписания

Расписание чемпионата проверяется в `test_schedule.py`
(`backend/tests/test_schedule.py`). Тест
`test_generate_championship_schedule_creates_double_round_robin_for_four_teams`
проверяет создание двойного кругового расписания для четырех команд
(`backend/tests/test_schedule.py`,
`backend/app/services/schedule_service.py`). Это важно, потому что каждый клуб
должен сыграть с каждым соперником дома и на выезде.

Также проверяются представления расписания сезона и стадиона, фильтрация по
команде, турниру и диапазону дат, ошибки при неверных фильтрах, отсутствие
ресурсов, запрет генерации расписания для кубкового турнира и конфликт
существующего календаря (`backend/tests/test_schedule.py`,
`backend/app/api/v1/endpoints/schedule.py`,
`backend/app/services/schedule_service.py`).

### Тестирование кубкового турнира

Кубковый сценарий покрыт тестами в `test_cups.py`
(`backend/tests/test_cups.py`). Основной тест проверяет полный поток:
создание полуфиналов, завершение полуфиналов, создание финала и получение
сетки кубка (`backend/tests/test_cups.py`,
`backend/app/services/cup_service.py`).

Дополнительно проверяется запрет генерации полуфиналов для некубкового турнира,
автовыбор топ-команд по месту прошлого сезона, отсутствие обязательного
стадиона у гостевых команд, необходимость ручного выбора без мест прошлого
сезона, ошибки отсутствующего турнира, команды или стадиона, запрет дублей
команд, перенос полуфиналов из-за календарных конфликтов, недельный лимит,
запрет повторной сетки, запрет финала без завершенных полуфиналов и запрет
финала после ничейного полуфинала (`backend/tests/test_cups.py`,
`backend/app/services/cup_service.py`).

### Тестирование составов

Составы матчей проверяются в `test_lineups.py`
(`backend/tests/test_lineups.py`). Тесты покрывают добавление, список,
обновление и удаление игроков из состава
(`backend/tests/test_lineups.py`,
`backend/app/services/lineup_service.py`). Проверяются ошибки, когда команда
не участвует в матче, игрок принадлежит другой команде, игрок добавляется
повторно или номер в составе команды повторяется
(`backend/tests/test_lineups.py`,
`backend/app/services/lineup_service.py`).

Автоматическая генерация состава проверяется отдельными сценариями:
выбор доступных игроков, ровно один стартовый вратарь, продвижение вратаря в
стартовый состав, замена дисквалифицированного предпочитаемого игрока, запрет
перезаписи существующего состава без явного флага, разрешенная перезапись,
ошибка для предпочитаемого игрока из другой команды и ошибка при недостатке
доступных игроков (`backend/tests/test_lineups.py`,
`backend/app/services/lineup_service.py`).

### Тестирование протокола матча

Протоколы матчей проверяются в `test_match_protocol.py`
(`backend/tests/test_match_protocol.py`). Тесты покрывают добавление, список,
обновление и удаление событий протокола
(`backend/tests/test_match_protocol.py`,
`backend/app/services/match_protocol_service.py`). Проверяется, что событие
нельзя добавить за команду, которая не участвует в матче, нельзя указать
игрока другой команды и нельзя указать ассистента другой команды
(`backend/tests/test_match_protocol.py`,
`backend/app/services/match_protocol_service.py`).

Завершение матча проверяется на соответствие итогового счета записанным голам.
Если счет не совпадает с голевыми событиями, сервис возвращает ошибку
(`backend/tests/test_match_protocol.py`,
`backend/app/services/match_protocol_service.py`). Также проверяется, что
завершение матча чемпионата пересчитывает турнирную таблицу и статистику
игроков, а завершение кубкового матча обновляет статистику игроков без влияния
на таблицу чемпионата (`backend/tests/test_match_protocol.py`,
`backend/app/services/standings_service.py`,
`backend/app/services/statistics_service.py`).

### Тестирование случайной генерации результатов

Случайная генерация результатов покрыта тестами в `test_random_results.py`
(`backend/tests/test_random_results.py`). Проверяется, что генерация завершает
матч, создает ограниченный по реалистичным пределам протокол, выставляет
итоговый счет и обновляет производные данные
(`backend/tests/test_random_results.py`,
`backend/app/services/random_result_service.py`).

Также проверяются alias генерации протокола одного матча, генерация протоколов
для всего сезона, пропуск матчей с уже существующим протоколом, пропуск
завершенных и отмененных матчей, учет дисквалификаций после красной карточки,
ошибка при невалидном существующем составе, ошибка при отсутствии вратаря,
откат транзакции при отсутствии доступного судьи, запрет генерации без игроков,
запрет генерации при пустом пуле судей, запрет генерации поверх существующих
событий, запрет генерации для завершенного матча и обязательный победитель в
кубковой стадии (`backend/tests/test_random_results.py`,
`backend/app/services/random_result_service.py`).

### Тестирование турнирной таблицы и статистики

Турнирная таблица проверяется в `test_standings.py`
(`backend/tests/test_standings.py`). Тесты подтверждают, что таблица
пересчитывается по завершенным матчам чемпионата, учитывает очки, победы,
ничьи, поражения, голы, разницу мячей и места
(`backend/tests/test_standings.py`,
`backend/app/services/standings_service.py`). Также проверяется идемпотентность
пересчета, ошибка для отсутствующего сезона и обязательность JWT
(`backend/tests/test_standings.py`).

Статистика игроков проверяется в `test_statistics.py`
(`backend/tests/test_statistics.py`). Тесты подтверждают пересчет голов,
ассистов, сейвов, желтых и красных карточек, работу таблиц лидеров,
идемпотентность пересчета, ошибку для неподдерживаемой метрики, ошибку для
отсутствующего сезона и обязательность JWT
(`backend/tests/test_statistics.py`,
`backend/app/services/statistics_service.py`).

### Тестирование изоляции данных пользователей

Изоляция пользовательских данных проверяется в `test_owner_scope.py`
(`backend/tests/test_owner_scope.py`). Тесты создают несколько пользователей и
подтверждают, что справочники, расписание, турнирная таблица, статистика,
кубковая сетка и автоматический выбор команд работают только в пределах
текущего владельца (`backend/tests/test_owner_scope.py`,
`backend/app/repositories/base.py`, `backend/app/api/deps.py`).

Также проверяется, что нельзя создать связанную сущность с foreign ID,
принадлежащим другому пользователю. Например, пользователь не может создать
матч с чужой командой, чужим сезоном или чужим стадионом
(`backend/tests/test_owner_scope.py`,
`backend/app/services/match_service.py`,
`backend/app/services/schedule_service.py`).

### Статический анализ, форматирование и CI

Для контроля качества кода используются ruff и black. Ruff проверяет ошибки
стиля, импорты, современные конструкции Python и потенциальные баги
(`backend/pyproject.toml`). Black обеспечивает единый формат кода
(`backend/pyproject.toml`).

Локальный запуск проверок:

```powershell
cd backend
pytest
ruff check .
black .
```

В CI выполняются тесты, ruff, проверка форматирования `black --check .`,
применение миграций и `alembic check`
(`.github/workflows/backend-ci.yml`). Это обеспечивает автоматический контроль
регрессий при изменении кода.

## 3.4 Ввод в эксплуатацию

### Подготовка к эксплуатации

Ввод приложения в эксплуатацию начинается с подготовки окружения. Необходимо
развернуть PostgreSQL, настроить переменные окружения, применить миграции,
запустить backend и проверить healthcheck. При локальной эксплуатации или
демонстрации предпочтителен Docker Compose, потому что он одновременно
описывает базу данных, backend и их параметры (`docker-compose.yml`).

Минимальная последовательность запуска:

```powershell
docker compose up -d db
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

Контейнерная последовательность:

```powershell
docker compose up --build backend
```

В контейнерном сценарии миграции выполняются автоматически перед запуском
Uvicorn (`backend/Dockerfile`).

### Настройка эксплуатационных параметров

Для эксплуатации необходимо настроить переменные:

- `SECRET_KEY` - секрет подписи JWT (`backend/app/core/config.py`);
- `DATABASE_URL` - строка подключения к PostgreSQL (`backend/app/core/config.py`);
- `ENVIRONMENT` - режим окружения (`backend/app/core/config.py`);
- `DEBUG` - включение или отключение debug-режима (`backend/app/core/config.py`);
- `CORS_ORIGINS` - разрешенные источники клиентского приложения
  (`backend/app/core/config.py`, `backend/app/main.py`);
- `ACCESS_TOKEN_EXPIRE_MINUTES` - время жизни JWT-токена
  (`backend/app/core/config.py`, `backend/app/core/security.py`).

Особенно важно заменить `SECRET_KEY` вне локальной среды. Валидация настроек
запрещает использовать стандартный секрет в нелокальной среде
(`backend/app/core/config.py`).

### Проверка после развертывания

После запуска сервиса выполняется smoke-тест:

1. Запросить `/health` и убедиться в ответе `{"status":"ok","service":"Tournament Maker Backend"}`
   (`backend/app/main.py`).
2. Зарегистрировать тестового организатора (`backend/app/api/v1/endpoints/auth.py`).
3. Выполнить login и получить JWT (`backend/app/api/v1/endpoints/auth.py`,
   `backend/app/core/security.py`).
4. Проверить `/api/v1/auth/me` с bearer-token (`backend/app/api/deps.py`).
5. Получить списки стартовых команд, игроков, стадионов и судей, которые
   создаются для нового пользователя (`backend/app/services/starter_data_service.py`).
6. Создать сезон и турнир (`backend/app/api/v1/endpoints/seasons.py`,
   `backend/app/api/v1/endpoints/tournaments.py`).
7. Создать или сгенерировать матч (`backend/app/services/match_service.py`,
   `backend/app/services/schedule_service.py`).
8. Завершить матч через протокол или генератор результата
   (`backend/app/services/match_protocol_service.py`,
   `backend/app/services/random_result_service.py`).
9. Проверить турнирную таблицу и статистику
   (`backend/app/services/standings_service.py`,
   `backend/app/services/statistics_service.py`).

### Начальное наполнение данных

Для демонстрационной эксплуатации можно использовать два механизма наполнения.
Первый механизм - автоматические starter-данные при регистрации нового
организатора (`backend/app/services/starter_data_service.py`). Второй механизм
- CSV-импорт через `seed_demo_data` (`backend/app/scripts/seed_demo_data.py`).

Starter-данные подходят для быстрого старта нового пользователя. CSV-импорт
подходит для защиты проекта и демонстрации более реалистичного набора данных:
сезона, чемпионата, кубка, команд, стадионов, игроков, судей и расписания
(`backend/app/scripts/seed_demo_data.py`).

### Эксплуатационный сценарий работы пользователя

Типовой пользовательский сценарий backend выглядит следующим образом:

1. Организатор регистрируется и получает стартовые команды, игроков, стадионы
   и судей (`backend/app/api/v1/endpoints/auth.py`,
   `backend/app/services/starter_data_service.py`).
2. Организатор создает сезон (`backend/app/api/v1/endpoints/seasons.py`,
   `backend/app/services/season_service.py`).
3. Организатор создает турнир чемпионата и/или кубка
   (`backend/app/api/v1/endpoints/tournaments.py`,
   `backend/app/services/tournament_service.py`).
4. Для чемпионата генерируется расписание двойного кругового турнира
   (`backend/app/api/v1/endpoints/schedule.py`,
   `backend/app/services/schedule_service.py`).
5. Для кубка генерируются полуфиналы и затем финал
   (`backend/app/api/v1/endpoints/cups.py`,
   `backend/app/services/cup_service.py`).
6. Организатор назначает судей, переносит матчи при необходимости и
   контролирует цену билетов (`backend/app/services/match_service.py`,
   `backend/app/services/validation_service.py`,
   `backend/app/services/ticket_price_service.py`).
7. На матч формируется состав вручную или автоматически
   (`backend/app/api/v1/endpoints/lineups.py`,
   `backend/app/services/lineup_service.py`).
8. После матча заполняется протокол и матч завершается
   (`backend/app/api/v1/endpoints/protocol.py`,
   `backend/app/services/match_protocol_service.py`).
9. Система пересчитывает турнирную таблицу и статистику игроков
   (`backend/app/services/standings_service.py`,
   `backend/app/services/statistics_service.py`).
10. При необходимости организатор запускает генерацию случайных результатов
    для одного матча или всего сезона
    (`backend/app/api/v1/endpoints/random_results.py`,
    `backend/app/services/random_result_service.py`).
11. После окончания сезона организатор создает следующий сезон через rollover
    (`backend/app/api/v1/endpoints/seasons.py`,
    `backend/app/services/season_rollover_service.py`).

### Обеспечение целостности при эксплуатации

Целостность данных обеспечивается несколькими механизмами. На уровне базы
данных используются внешние ключи, уникальные ограничения и check-constraint:
например, матч не может иметь одинаковую домашнюю и гостевую команду, количество
проданных билетов не может быть отрицательным, а вместимость стадиона должна
быть положительной (`backend/app/models/match.py`,
`backend/app/models/stadium.py`).

На уровне сервисов проверяются бизнес-правила: лимиты матчей команды в день и
неделю (`backend/app/services/schedule_service.py`), доступность судьи
(`backend/app/services/validation_service.py`), принадлежность игроков и
команд текущему пользователю (`backend/app/services/*.py`), корректность
итогового счета относительно событий протокола
(`backend/app/services/match_protocol_service.py`) и невозможность обычного
редактирования завершенного матча (`backend/app/services/match_service.py`).

На уровне авторизации все предметные данные фильтруются по `owner_id`
(`backend/app/repositories/base.py`, `backend/app/api/deps.py`). Это означает,
что данные одного организатора изолированы от данных другого.

### Мониторинг и диагностика

Минимальная диагностика включает healthcheck `/health` (`backend/app/main.py`),
журналы Uvicorn при локальном запуске и логи Docker-контейнеров при
контейнерном запуске (`backend/Dockerfile`, `docker-compose.yml`). Для проверки
базы данных можно использовать состояние контейнера PostgreSQL и healthcheck
`pg_isready` (`docker-compose.yml`).

Для диагностики ошибок API используется единая схема HTTP-статусов:
`401` для отсутствующих или неверных JWT, `404` для отсутствующих ресурсов,
`409` для конфликтов уникальности и расписания, `400` для нарушений бизнес-
правил и `422` для ошибок валидации входного payload
(`backend/app/core/status_codes.py`, `backend/app/api/errors.py`).

### Обновление версии приложения

При изменении моделей базы данных создается новая миграция Alembic:

```powershell
cd backend
alembic revision --autogenerate -m "описание изменения"
alembic upgrade head
```

Перед вводом новой версии необходимо выполнить тесты и проверки качества:

```powershell
cd backend
pytest
ruff check .
black --check .
alembic check
```

Эта же последовательность частично автоматизирована в GitHub Actions
(`.github/workflows/backend-ci.yml`). Такой процесс снижает риск регрессий при
обновлении приложения.

## 3.5 Разработка сопроводительной документации

### Назначение сопроводительной документации

Сопроводительная документация нужна для того, чтобы разработчик, пользователь,
преподаватель или проверяющий могли понять назначение системы, ее архитектуру,
порядок установки, правила эксплуатации, API-сценарии и ограничения предметной
области. Для учебного проекта документация также фиксирует принятые
архитектурные решения и показывает, что разработка велась системно.

В проекте уже присутствует набор документов, каждый из которых выполняет
свою роль.

### Документация по контексту проекта

Файл `docs/PROJECT_CONTEXT.md` описывает цель проекта, предметную область,
основные сущности, бизнес-ограничения, MVP, текущее состояние реализации и
API-конвенции (`docs/PROJECT_CONTEXT.md`). Этот документ является главным
источником предметного контекста: в нем зафиксировано, что система управляет
сезонами, чемпионатом, кубком, матчами, составами, протоколами, расписанием,
турнирной таблицей и статистикой.

При изменении архитектурных решений этот файл должен обновляться. Например,
если меняется правило расчета цены билета, логика кубка, ограничения
расписания или структура статистики, такие изменения должны быть отражены в
`docs/PROJECT_CONTEXT.md`.

### Архитектурная документация

Файл `docs/ARCHITECTURE.md` описывает слои backend, текущие архитектурные
решения, реализованные доменные сервисы и бизнес-правила
(`docs/ARCHITECTURE.md`). В нем зафиксировано, что бизнес-логика находится в
сервисах, доступ к данным вынесен в репозитории, модели находятся в
`backend/app/models`, схемы - в `backend/app/schemas`, а endpoint-ы остаются
тонкими.

Этот документ полезен для раздела курсовой, посвященного проектированию
структуры приложения. В нем можно взять формулировки про owner-scope, сервисный
слой, миграции, расписание, кубок, составы, протоколы, статистику и CI
(`docs/ARCHITECTURE.md`).

### README backend

Файл `backend/README.md` содержит практические инструкции по первому запуску,
установке зависимостей, запуску PostgreSQL, запуску backend, импорту демо-данных,
проверке API, работе с Alembic, запуску тестов и структуре проекта
(`backend/README.md`). Это основной пользовательско-разработческий документ
для запуска backend-части приложения.

В курсовой этот файл можно использовать как основу для подраздела "Установка и
настройка", потому что он содержит команды, ожидаемые ответы и демонстрационный
API-flow (`backend/README.md`).

### Журналы разработки и проверки

Файл `docs/DEVELOPMENT_LOG.md` используется для фиксации хода разработки
(`docs/DEVELOPMENT_LOG.md`). Файл `docs/BACKEND_REVIEW_LOG.md` может
использоваться для записей по ревью backend-части (`docs/BACKEND_REVIEW_LOG.md`).
Файл `docs/ACCEPTANCE_CASES.md` может использоваться как список приемочных
сценариев и требований к демонстрации (`docs/ACCEPTANCE_CASES.md`).

Наличие таких файлов помогает показать, что разработка велась итерационно:
сначала была сформулирована предметная область, затем реализованы модели,
сервисы, endpoint-ы, тесты, документация и проверочные сценарии.

### Документация API через OpenAPI

FastAPI автоматически формирует OpenAPI-спецификацию на основе маршрутов,
схем и metadata приложения (`backend/app/main.py`,
`backend/app/api/v1/router.py`, `backend/app/schemas/*.py`). Описание тегов
API задано в списке `OPENAPI_TAGS` (`backend/app/main.py`). Благодаря этому
после запуска backend доступны интерактивные страницы документации:

- Swagger UI: `http://127.0.0.1:8000/docs`;
- ReDoc: `http://127.0.0.1:8000/redoc`;
- JSON-спецификация OpenAPI: `http://127.0.0.1:8000/openapi.json`.

Эта документация является машинно-генерируемой и всегда отражает актуальные
Pydantic-схемы и endpoint-ы проекта (`backend/app/schemas/*.py`,
`backend/app/api/v1/endpoints/*.py`).

### Документация установки

Документация установки включает:

- команды запуска PostgreSQL (`docker-compose.yml`, `backend/README.md`);
- создание виртуального окружения и установку зависимостей
  (`backend/pyproject.toml`, `backend/requirements-dev.txt`,
  `backend/README.md`);
- создание `.env` из `.env.example` (`backend/.env.example`,
  `backend/README.md`);
- применение миграций (`backend/alembic/env.py`, `backend/README.md`);
- запуск backend через Uvicorn (`backend/app/main.py`, `backend/README.md`);
- контейнерный запуск через Docker Compose (`docker-compose.yml`,
  `backend/Dockerfile`).

Эти сведения позволяют повторить установку приложения на новой машине и
проверить его работоспособность.

### Документация тестирования

Документация тестирования описывает запуск:

```powershell
cd backend
pytest
ruff check .
black --check .
alembic check
```

Команды тестирования и форматирования указаны в `backend/README.md`, а сами
инструменты настроены в `backend/pyproject.toml`. Набор тестов находится в
`backend/tests/*.py`. В курсовой можно указать, что тестирование включает
модульно-интеграционные проверки API, проверку бизнес-правил, проверку
безопасности owner-scope, проверку статистики и проверку генерации расписаний
и результатов.

### Документация эксплуатационных сценариев

Для эксплуатации и защиты проекта полезен сценарий, в котором демонстрируется
полный жизненный цикл: регистрация, login, получение JWT, просмотр стартовых
данных, создание сезона, создание турнира, генерация расписания, создание
составов, заполнение протокола, завершение матча, пересчет турнирной таблицы
и статистики (`backend/README.md`, `backend/app/api/v1/endpoints/*.py`).

Такой сценарий показывает не только отдельные endpoint-ы, но и связность всей
системы: действия пользователя приводят к изменению доменных сущностей, а
производные данные обновляются автоматически через сервисы
(`backend/app/services/match_protocol_service.py`,
`backend/app/services/random_result_service.py`,
`backend/app/services/standings_service.py`,
`backend/app/services/statistics_service.py`).

### Рекомендации по дальнейшему расширению документации

Для улучшения сопроводительной документации можно дополнительно подготовить:

- руководство администратора с настройками окружения, миграциями, резервным
  копированием PostgreSQL и обновлениями;
- руководство пользователя с типовыми сценариями организатора турнира;
- ER-диаграмму базы данных на основе моделей SQLAlchemy
  (`backend/app/models/*.py`);
- таблицу endpoint-ов с методами, URL, назначением, статус-кодами и схемами
  (`backend/app/api/v1/endpoints/*.py`, `backend/app/schemas/*.py`);
- описание бизнес-правил календаря, кубка, составов, протоколов и статистики
  (`backend/app/services/*.py`);
- матрицу тестового покрытия по подсистемам (`backend/tests/*.py`);
- инструкцию по демонстрационному запуску с CSV-импортом
  (`backend/app/scripts/seed_demo_data.py`).

## Итог по главе

В ходе разработки Tournament Maker были созданы основные составные элементы
backend-приложения: конфигурация, авторизация, доменные модели, API-схемы,
репозитории, сервисы бизнес-логики, миграции, тесты, Docker-конфигурация и
документация. Архитектура приложения построена вокруг разделения
ответственности: endpoint-ы отвечают за HTTP-уровень, сервисы - за бизнес-
правила, репозитории - за доступ к данным, модели - за структуру базы данных,
а схемы - за контракты API.

Установка и настройка выполняются через Python-окружение, PostgreSQL,
переменные окружения, Alembic-миграции и запуск Uvicorn либо Docker Compose.
Тестирование организовано через pytest, FastAPI TestClient, ruff, black,
Alembic check и CI. Ввод в эксплуатацию включает подготовку окружения,
настройку секретов, миграции, запуск сервиса, smoke-тесты и начальное
наполнение данных. Сопроводительная документация представлена контекстом
проекта, архитектурным описанием, README, журналами разработки, OpenAPI-
документацией и данным файлом как основой для курсовой работы.
