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


def get_statistics_service(db: DbSession, owner_id: int) -> StatisticsService:
    return StatisticsService(
        seasons=SeasonRepository(db, owner_id),
        events=MatchEventRepository(db, owner_id),
        player_stats=PlayerSeasonStatsRepository(db, owner_id),
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
    current_user: CurrentUser,
) -> list[PlayerSeasonStatsRead]:
    try:
        return get_statistics_service(db, current_user.id).get_player_stats_for_season(
            season_id
        )
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
    current_user: CurrentUser,
) -> list[PlayerSeasonStatsRead]:
    try:
        return get_statistics_service(
            db,
            current_user.id,
        ).recalculate_player_stats_for_season(season_id)
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
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=100),
) -> list[PlayerSeasonStatsRead]:
    try:
        return get_statistics_service(db, current_user.id).get_leaders(
            season_id=season_id,
            metric=metric,
            limit=limit,
        )
    except (BusinessRuleError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
