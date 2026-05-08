from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match_event import MatchEventRepository
from app.repositories.season import SeasonRepository
from app.repositories.stats import PlayerSeasonStatsRepository
from app.schemas.stats import PlayerSeasonStatsRead
from app.services.statistics_service import StatisticsService

router = APIRouter()


def get_statistics_service(db: DbSession) -> StatisticsService:
    return StatisticsService(
        seasons=SeasonRepository(db),
        events=MatchEventRepository(db),
        player_stats=PlayerSeasonStatsRepository(db),
    )


@router.get(
    "/seasons/{season_id}/players",
    response_model=list[PlayerSeasonStatsRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_player_stats(
    season_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> list[PlayerSeasonStatsRead]:
    try:
        return get_statistics_service(db).get_player_stats_for_season(season_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/seasons/{season_id}/players/recalculate",
    response_model=list[PlayerSeasonStatsRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def recalculate_player_stats(
    season_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> list[PlayerSeasonStatsRead]:
    try:
        return get_statistics_service(db).recalculate_player_stats_for_season(season_id)
    except (ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc


@router.get(
    "/seasons/{season_id}/leaders/{metric}",
    response_model=list[PlayerSeasonStatsRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_player_leaders(
    season_id: int,
    metric: str,
    db: DbSession,
    _current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=100),
) -> list[PlayerSeasonStatsRead]:
    try:
        return get_statistics_service(db).get_leaders(
            season_id=season_id,
            metric=metric,
            limit=limit,
        )
    except (BusinessRuleError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
