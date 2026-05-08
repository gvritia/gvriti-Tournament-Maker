from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.player import PlayerRepository
from app.repositories.team import TeamRepository
from app.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
from app.services.player_service import PlayerService

router = APIRouter()


def get_player_service(db: DbSession) -> PlayerService:
    return PlayerService(PlayerRepository(db), TeamRepository(db))


@router.get(
    "/",
    response_model=list[PlayerRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_players(
    db: DbSession,
    _current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[PlayerRead]:
    return get_player_service(db).list_players(offset=offset, limit=limit)


@router.post(
    "/",
    response_model=PlayerRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def create_player(
    payload: PlayerCreate,
    db: DbSession,
    _current_user: CurrentUser,
) -> PlayerRead:
    try:
        return get_player_service(db).create_player(payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{player_id}",
    response_model=PlayerRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_player(
    player_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> PlayerRead:
    try:
        return get_player_service(db).get_player(player_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/{player_id}",
    response_model=PlayerRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_player(
    player_id: int,
    payload: PlayerUpdate,
    db: DbSession,
    _current_user: CurrentUser,
) -> PlayerRead:
    try:
        return get_player_service(db).update_player(player_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/{player_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_player(
    player_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> None:
    try:
        get_player_service(db).delete_player(player_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
