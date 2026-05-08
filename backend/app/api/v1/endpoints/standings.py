from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.season import SeasonRepository
from app.repositories.stats import TeamSeasonStatsRepository
from app.schemas.stats import TeamSeasonStatsRead
from app.services.standings_service import StandingsService

router = APIRouter()


def get_standings_service(db: DbSession) -> StandingsService:
    return StandingsService(
        seasons=SeasonRepository(db),
        matches=MatchRepository(db),
        team_stats=TeamSeasonStatsRepository(db),
    )


@router.get(
    "/seasons/{season_id}",
    response_model=list[TeamSeasonStatsRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def get_season_standings(
    season_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> list[TeamSeasonStatsRead]:
    try:
        return get_standings_service(db).get_season_standings(season_id)
    except NotFoundError as exc:
        raise app_error_to_http_exception(exc) from exc


@router.post(
    "/seasons/{season_id}/recalculate",
    response_model=list[TeamSeasonStatsRead],
    status_code=status_codes.HTTP_OK,
    responses=status_codes.CRUD_ERROR_RESPONSES,
)
def recalculate_season_standings(
    season_id: int,
    db: DbSession,
    _current_user: CurrentUser,
) -> list[TeamSeasonStatsRead]:
    try:
        return get_standings_service(db).recalculate_for_season(season_id)
    except (ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
