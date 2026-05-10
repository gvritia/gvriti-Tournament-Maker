from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.season import SeasonRepository
from app.schemas.season import SeasonCreate, SeasonRead, SeasonUpdate
from app.services.season_service import SeasonService

router = APIRouter()


@router.get(
    "/",
    response_model=list[SeasonRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_seasons(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[SeasonRead]:
    return SeasonService(SeasonRepository(db, current_user.id)).list_seasons(
        offset=offset,
        limit=limit,
    )


@router.post(
    "/",
    response_model=SeasonRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def create_season(
    payload: SeasonCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> SeasonRead:
    try:
        return SeasonService(SeasonRepository(db, current_user.id)).create_season(
            payload
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{season_id}",
    response_model=SeasonRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_season(
    season_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> SeasonRead:
    try:
        return SeasonService(SeasonRepository(db, current_user.id)).get_season(
            season_id
        )
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/{season_id}",
    response_model=SeasonRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_season(
    season_id: int,
    payload: SeasonUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> SeasonRead:
    try:
        return SeasonService(SeasonRepository(db, current_user.id)).update_season(
            season_id,
            payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/{season_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_season(
    season_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    try:
        SeasonService(SeasonRepository(db, current_user.id)).delete_season(season_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
