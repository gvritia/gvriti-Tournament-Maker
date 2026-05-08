from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.referee import RefereeRepository
from app.schemas.referee import RefereeCreate, RefereeRead, RefereeUpdate
from app.services.referee_service import RefereeService

router = APIRouter()


@router.get(
    "/",
    response_model=list[RefereeRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_referees(
    db: DbSession,
    _current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[RefereeRead]:
    return RefereeService(RefereeRepository(db)).list_referees(
        offset=offset,
        limit=limit,
    )


@router.post(
    "/",
    response_model=RefereeRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def create_referee(
    payload: RefereeCreate,
    db: DbSession,
    _current_user: CurrentUser,
) -> RefereeRead:
    try:
        return RefereeService(RefereeRepository(db)).create_referee(payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{referee_id}",
    response_model=RefereeRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_referee(
    referee_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> RefereeRead:
    try:
        return RefereeService(RefereeRepository(db)).get_referee(referee_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/{referee_id}",
    response_model=RefereeRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_referee(
    referee_id: int,
    payload: RefereeUpdate,
    db: DbSession,
    _current_user: CurrentUser,
) -> RefereeRead:
    try:
        return RefereeService(RefereeRepository(db)).update_referee(
            referee_id,
            payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/{referee_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_referee(
    referee_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> None:
    try:
        RefereeService(RefereeRepository(db)).delete_referee(referee_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
