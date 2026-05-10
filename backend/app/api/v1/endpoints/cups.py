from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.cup import CupBracketRead, CupFinalGenerate, CupSemifinalsGenerate
from app.schemas.match import MatchRead
from app.services.cup_service import CupService
from app.services.schedule_service import ScheduleService
from app.services.ticket_price_service import TicketPriceService

router = APIRouter()


def get_cup_service(db: DbSession, owner_id: int) -> CupService:
    matches = MatchRepository(db, owner_id)
    return CupService(
        matches=matches,
        tournaments=TournamentRepository(db, owner_id),
        teams=TeamRepository(db, owner_id),
        stadiums=StadiumRepository(db, owner_id),
        schedule=ScheduleService(matches),
        ticket_prices=TicketPriceService(),
    )


@router.post(
    "/{tournament_id}/semifinals",
    response_model=list[MatchRead],
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def generate_cup_semifinals(
    tournament_id: int,
    payload: CupSemifinalsGenerate,
    db: DbSession,
    current_user: CurrentUser,
) -> list[MatchRead]:
    try:
        return get_cup_service(db, current_user.id).generate_semifinals(
            tournament_id=tournament_id,
            payload=payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/{tournament_id}/final",
    response_model=MatchRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def generate_cup_final(
    tournament_id: int,
    payload: CupFinalGenerate,
    db: DbSession,
    current_user: CurrentUser,
) -> MatchRead:
    try:
        return get_cup_service(db, current_user.id).generate_final(
            tournament_id=tournament_id,
            payload=payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/{tournament_id}/bracket",
    response_model=CupBracketRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_cup_bracket(
    tournament_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> CupBracketRead:
    try:
        return get_cup_service(db, current_user.id).get_bracket(tournament_id)
    except (BusinessRuleError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
