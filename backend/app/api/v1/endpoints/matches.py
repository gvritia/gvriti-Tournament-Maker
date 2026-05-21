from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.referee import RefereeRepository
from app.repositories.season import SeasonRepository
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.match import (
    MatchCreate,
    MatchRead,
    MatchRefereeAssign,
    MatchReschedule,
    MatchTicketPriceUpdate,
    MatchUpdate,
)
from app.services.match_service import MatchService
from app.services.schedule_service import ScheduleService
from app.services.ticket_price_service import TicketPriceService
from app.services.validation_service import ValidationService

router = APIRouter()


def get_match_service(db: DbSession, owner_id: int) -> MatchService:
    matches = MatchRepository(db, owner_id)
    return MatchService(
        matches=matches,
        tournaments=TournamentRepository(db, owner_id),
        seasons=SeasonRepository(db, owner_id),
        teams=TeamRepository(db, owner_id),
        stadiums=StadiumRepository(db, owner_id),
        referees=RefereeRepository(db, owner_id),
        schedule=ScheduleService(matches),
        ticket_prices=TicketPriceService(),
        validation=ValidationService(matches),
    )


@router.get(
    "/",
    response_model=list[MatchRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_matches(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[MatchRead]:
    return get_match_service(db, current_user.id).list_matches(
        offset=offset,
        limit=limit,
    )


@router.post(
    "/",
    response_model=MatchRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def create_match(
    payload: MatchCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_service(db, current_user.id).create_match(payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{match_id}",
    response_model=MatchRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_match(
    match_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_service(db, current_user.id).get_match(match_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.patch(
    "/{match_id}",
    response_model=MatchRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def update_match(
    match_id: int,
    payload: MatchUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_service(db, current_user.id).update_match(match_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.delete(
    "/{match_id}",
    status_code=status_codes.HTTP_NO_CONTENT,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def delete_match(
    match_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    try:
        get_match_service(db, current_user.id).delete_match(match_id)
    except (BusinessRuleError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/{match_id}/assign-referee",
    response_model=MatchRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def assign_referee(
    match_id: int,
    payload: MatchRefereeAssign,
    db: DbSession,
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_service(db, current_user.id).assign_referee(
            match_id,
            payload.referee_id,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/{match_id}/reschedule",
    response_model=MatchRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def reschedule_match(
    match_id: int,
    payload: MatchReschedule,
    db: DbSession,
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_service(db, current_user.id).reschedule_match(
            match_id,
            payload.match_datetime,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/{match_id}/ticket-price",
    response_model=MatchRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def set_manual_ticket_price(
    match_id: int,
    payload: MatchTicketPriceUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_match_service(db, current_user.id).set_manual_ticket_price(
            match_id,
            payload.ticket_price,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
