from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.player import PlayerRepository
from app.repositories.season import SeasonRepository
from app.repositories.stats import (
    PlayerSeasonStatsRepository,
    TeamSeasonStatsRepository,
)
from app.repositories.team import TeamRepository
from app.schemas.match import MatchRead
from app.schemas.match_event import (
    MatchEventCreate,
    MatchEventRead,
    MatchEventUpdate,
    MatchFinish,
)
from app.services.match_protocol_service import MatchProtocolService
from app.services.standings_service import StandingsService
from app.services.statistics_service import StatisticsService

router = APIRouter()


def get_match_protocol_service(db: DbSession) -> MatchProtocolService:
    matches = MatchRepository(db)
    events = MatchEventRepository(db)
    return MatchProtocolService(
        matches=matches,
        events=events,
        players=PlayerRepository(db),
        teams=TeamRepository(db),
        standings=StandingsService(
            seasons=SeasonRepository(db),
            matches=matches,
            team_stats=TeamSeasonStatsRepository(db),
        ),
        statistics=StatisticsService(
            seasons=SeasonRepository(db),
            events=events,
            player_stats=PlayerSeasonStatsRepository(db),
        ),
    )


@router.get(
    "/matches/{match_id}/events",
    response_model=list[MatchEventRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_match_events(
    match_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> list[MatchEventRead]:
    try:
        return get_match_protocol_service(db).list_match_events(match_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/matches/{match_id}/events",
    response_model=MatchEventRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def add_match_event(
    match_id: int,
    payload: MatchEventCreate,
    db: DbSession,
    _current_user: CurrentUser,
) -> MatchEventRead:
    try:
        return get_match_protocol_service(db).add_event(match_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/events/{event_id}",
    response_model=MatchEventRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_match_event(
    event_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> MatchEventRead:
    try:
        return get_match_protocol_service(db).get_event(event_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/events/{event_id}",
    response_model=MatchEventRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_match_event(
    event_id: int,
    payload: MatchEventUpdate,
    db: DbSession,
    _current_user: CurrentUser,
) -> MatchEventRead:
    try:
        return get_match_protocol_service(db).update_event(event_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/events/{event_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_match_event(
    event_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> None:
    try:
        get_match_protocol_service(db).delete_event(event_id)
    except (BusinessRuleError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/matches/{match_id}/finish",
    response_model=MatchRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def finish_match(
    match_id: int,
    payload: MatchFinish,
    db: DbSession,
    _current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_protocol_service(db).finish_match(match_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
