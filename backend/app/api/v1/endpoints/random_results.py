from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.errors import app_error_to_http_exception
from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.player import PlayerRepository
from app.schemas.random_result import RandomResultGenerate, RandomResultRead
from app.services.random_result_service import RandomResultService

router = APIRouter()


def get_random_result_service(db: DbSession) -> RandomResultService:
    return RandomResultService(
        matches=MatchRepository(db),
        events=MatchEventRepository(db),
        players=PlayerRepository(db),
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
    _current_user: CurrentUser,
) -> RandomResultRead:
    try:
        return get_random_result_service(db).generate_for_match(match_id, payload)
    except (BusinessRuleError, ConflictError, NotFoundError) as exc:
        raise app_error_to_http_exception(exc) from exc
