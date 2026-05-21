from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.match_lineup import MatchLineupRepository
from app.repositories.player import PlayerRepository
from app.repositories.referee import RefereeRepository
from app.repositories.season import SeasonRepository
from app.repositories.stats import (
    PlayerSeasonStatsRepository,
    TeamSeasonStatsRepository,
)
from app.schemas.random_result import (
    RandomResultGenerate,
    RandomResultRead,
    RandomSeasonResultRead,
)
from app.services.random_result_service import RandomResultService
from app.services.standings_service import StandingsService
from app.services.statistics_service import StatisticsService

router = APIRouter()


def get_random_result_service(db: DbSession, owner_id: int) -> RandomResultService:
    matches = MatchRepository(db, owner_id)
    events = MatchEventRepository(db, owner_id)
    return RandomResultService(
        matches=matches,
        events=events,
        players=PlayerRepository(db, owner_id),
        lineups=MatchLineupRepository(db, owner_id),
        referees=RefereeRepository(db, owner_id),
        seasons=SeasonRepository(db, owner_id),
        standings=StandingsService(
            seasons=SeasonRepository(db, owner_id),
            matches=matches,
            team_stats=TeamSeasonStatsRepository(db, owner_id),
        ),
        statistics=StatisticsService(
            seasons=SeasonRepository(db, owner_id),
            events=events,
            player_stats=PlayerSeasonStatsRepository(db, owner_id),
        ),
    )


@router.post(
    "/matches/{match_id}/generate-random-result",
    response_model=RandomResultRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def generate_random_match_result(
    match_id: int,
    payload: RandomResultGenerate,
    db: DbSession,
    current_user: CurrentUser,
) -> RandomResultRead:
    try:
        return get_random_result_service(db, current_user.id).generate_for_match(
            match_id,
            payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/matches/{match_id}/generate-protocol",
    response_model=RandomResultRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def generate_match_protocol(
    match_id: int,
    payload: RandomResultGenerate,
    db: DbSession,
    current_user: CurrentUser,
) -> RandomResultRead:
    try:
        return get_random_result_service(db, current_user.id).generate_for_match(
            match_id,
            payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/seasons/{season_id}/generate-protocols",
    response_model=RandomSeasonResultRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def generate_season_protocols(
    season_id: int,
    payload: RandomResultGenerate,
    db: DbSession,
    current_user: CurrentUser,
) -> RandomSeasonResultRead:
    try:
        return get_random_result_service(db, current_user.id).generate_for_season(
            season_id,
            payload,
        )
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
