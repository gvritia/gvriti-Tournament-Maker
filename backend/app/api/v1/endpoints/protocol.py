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


def get_match_protocol_service(db: DbSession, owner_id: int) -> MatchProtocolService:
    matches = MatchRepository(db, owner_id)
    events = MatchEventRepository(db, owner_id)
    return MatchProtocolService(
        matches=matches,
        events=events,
        players=PlayerRepository(db, owner_id),
        teams=TeamRepository(db, owner_id),
        standings=StandingsService(
            seasons=SeasonRepository(db, owner_id),
            matches=matches,
            team_stats=TeamSeasonStatsRepository(db, owner_id),
        ),
        statistics=StatisticsService(
            seasons=SeasonRepository(db, owner_id),
            events=events,
            player_stats=PlayerSeasonStatsRepository(db, owner_id),
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
    current_user: CurrentUser,
) -> list[MatchEventRead]:
    try:
        return get_match_protocol_service(db, current_user.id).list_match_events(
            match_id
        )
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
    current_user: CurrentUser,
) -> MatchEventRead:
    try:
        return get_match_protocol_service(db, current_user.id).add_event(
            match_id,
            payload,
        )
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
    current_user: CurrentUser,
) -> MatchEventRead:
    try:
        return get_match_protocol_service(db, current_user.id).get_event(event_id)
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
    current_user: CurrentUser,
) -> MatchEventRead:
    try:
        return get_match_protocol_service(db, current_user.id).update_event(
            event_id,
            payload,
        )
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
    current_user: CurrentUser,
) -> None:
    try:
        get_match_protocol_service(db, current_user.id).delete_event(event_id)
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
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_protocol_service(db, current_user.id).finish_match(
            match_id,
            payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
