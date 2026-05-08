from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.match_lineup import MatchLineupRepository
from app.repositories.player import PlayerRepository
from app.repositories.team import TeamRepository
from app.schemas.match_lineup import (
    MatchLineupCreate,
    MatchLineupRead,
    MatchLineupUpdate,
)
from app.services.lineup_service import LineupService

router = APIRouter()


def get_lineup_service(db: DbSession) -> LineupService:
    return LineupService(
        lineups=MatchLineupRepository(db),
        matches=MatchRepository(db),
        players=PlayerRepository(db),
        teams=TeamRepository(db),
        events=MatchEventRepository(db),
    )


@router.get(
    "/matches/{match_id}/lineups",
    response_model=list[MatchLineupRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_match_lineups(
    match_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> list[MatchLineupRead]:
    try:
        return get_lineup_service(db).list_match_lineups(match_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/matches/{match_id}/lineups",
    response_model=MatchLineupRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def add_player_to_lineup(
    match_id: int,
    payload: MatchLineupCreate,
    db: DbSession,
    _current_user: CurrentUser,
) -> MatchLineupRead:
    try:
        return get_lineup_service(db).add_player_to_lineup(match_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/lineups/{lineup_id}",
    response_model=MatchLineupRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_lineup(
    lineup_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> MatchLineupRead:
    try:
        return get_lineup_service(db).get_lineup(lineup_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/lineups/{lineup_id}",
    response_model=MatchLineupRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_lineup(
    lineup_id: int,
    payload: MatchLineupUpdate,
    db: DbSession,
    _current_user: CurrentUser,
) -> MatchLineupRead:
    try:
        return get_lineup_service(db).update_lineup(lineup_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/lineups/{lineup_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_lineup(
    lineup_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> None:
    try:
        get_lineup_service(db).delete_lineup(lineup_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
