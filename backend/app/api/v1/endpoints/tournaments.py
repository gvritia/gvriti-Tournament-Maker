from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.season import SeasonRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.tournament import TournamentCreate, TournamentRead, TournamentUpdate
from app.services.tournament_service import TournamentService

router = APIRouter()


def get_tournament_service(db: DbSession, owner_id: int) -> TournamentService:
    return TournamentService(
        TournamentRepository(db, owner_id),
        SeasonRepository(db, owner_id),
    )


@router.get(
    "/",
    response_model=list[TournamentRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_tournaments(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[TournamentRead]:
    return get_tournament_service(db, current_user.id).list_tournaments(
        offset=offset,
        limit=limit,
    )


@router.post(
    "/",
    response_model=TournamentRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def create_tournament(
    payload: TournamentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> TournamentRead:
    try:
        return get_tournament_service(db, current_user.id).create_tournament(payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{tournament_id}",
    response_model=TournamentRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_tournament(
    tournament_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> TournamentRead:
    try:
        return get_tournament_service(db, current_user.id).get_tournament(tournament_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/{tournament_id}",
    response_model=TournamentRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_tournament(
    tournament_id: int,
    payload: TournamentUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> TournamentRead:
    try:
        return get_tournament_service(db, current_user.id).update_tournament(
            tournament_id,
            payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/{tournament_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_tournament(
    tournament_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    try:
        get_tournament_service(db, current_user.id).delete_tournament(tournament_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
