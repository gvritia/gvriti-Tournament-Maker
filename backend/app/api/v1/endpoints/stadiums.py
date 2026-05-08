from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.schemas.stadium import StadiumCreate, StadiumRead, StadiumUpdate
from app.services.stadium_service import StadiumService

router = APIRouter()


def get_stadium_service(db: DbSession) -> StadiumService:
    return StadiumService(StadiumRepository(db), TeamRepository(db))


@router.get(
    "/",
    response_model=list[StadiumRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_stadiums(
    db: DbSession,
    _current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[StadiumRead]:
    return get_stadium_service(db).list_stadiums(offset=offset, limit=limit)


@router.post(
    "/",
    response_model=StadiumRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def create_stadium(
    payload: StadiumCreate,
    db: DbSession,
    _current_user: CurrentUser,
) -> StadiumRead:
    try:
        return get_stadium_service(db).create_stadium(payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{stadium_id}",
    response_model=StadiumRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_stadium(
    stadium_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> StadiumRead:
    try:
        return get_stadium_service(db).get_stadium(stadium_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/{stadium_id}",
    response_model=StadiumRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_stadium(
    stadium_id: int,
    payload: StadiumUpdate,
    db: DbSession,
    _current_user: CurrentUser,
) -> StadiumRead:
    try:
        return get_stadium_service(db).update_stadium(stadium_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/{stadium_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_stadium(
    stadium_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> None:
    try:
        get_stadium_service(db).delete_stadium(stadium_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
