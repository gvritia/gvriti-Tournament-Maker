from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.team import TeamRepository
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate
from app.services.team_service import TeamService

router = APIRouter()


@router.get(
    "/",
    response_model=list[TeamRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_teams(
    db: DbSession,
    _current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[TeamRead]:
    return TeamService(TeamRepository(db)).list_teams(offset=offset, limit=limit)


@router.post(
    "/",
    response_model=TeamRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def create_team(
    payload: TeamCreate,
    db: DbSession,
    _current_user: CurrentUser,
) -> TeamRead:
    try:
        return TeamService(TeamRepository(db)).create_team(payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_team(
    team_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> TeamRead:
    try:
        return TeamService(TeamRepository(db)).get_team(team_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/{team_id}",
    response_model=TeamRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: DbSession,
    _current_user: CurrentUser,
) -> TeamRead:
    try:
        return TeamService(TeamRepository(db)).update_team(team_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/{team_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_team(
    team_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> None:
    try:
        TeamService(TeamRepository(db)).delete_team(team_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
