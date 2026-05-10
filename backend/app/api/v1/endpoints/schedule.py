from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.season import SeasonRepository
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.match import MatchRead
from app.schemas.schedule import ChampionshipScheduleGenerate
from app.services.schedule_service import ScheduleService
from app.services.ticket_price_service import TicketPriceService

router = APIRouter()


def get_schedule_service(db: DbSession, owner_id: int) -> ScheduleService:
    return ScheduleService(
        matches=MatchRepository(db, owner_id),
        tournaments=TournamentRepository(db, owner_id),
        seasons=SeasonRepository(db, owner_id),
        teams=TeamRepository(db, owner_id),
        stadiums=StadiumRepository(db, owner_id),
        ticket_prices=TicketPriceService(),
    )


@router.post(
    "/championships/{tournament_id}/generate",
    response_model=list[MatchRead],
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def generate_championship_schedule(
    tournament_id: int,
    payload: ChampionshipScheduleGenerate,
    db: DbSession,
    current_user: CurrentUser,
) -> list[MatchRead]:
    try:
        return get_schedule_service(db, current_user.id).generate_championship_schedule(
            tournament_id=tournament_id,
            payload=payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/seasons/{season_id}/matches",
    response_model=list[MatchRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_season_matches(
    season_id: int,
    db: DbSession,
    current_user: CurrentUser,
    team_id: int | None = Query(default=None, gt=0),
    tournament_id: int | None = Query(default=None, gt=0),
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[MatchRead]:
    try:
        return get_schedule_service(db, current_user.id).list_season_matches(
            season_id,
            team_id=team_id,
            tournament_id=tournament_id,
            date_from=date_from,
            date_to=date_to,
        )
    except (BusinessRuleError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/stadiums/{stadium_id}/matches",
    response_model=list[MatchRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def list_stadium_matches(
    stadium_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[MatchRead]:
    try:
        return get_schedule_service(db, current_user.id).list_stadium_matches(
            stadium_id
        )
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc
