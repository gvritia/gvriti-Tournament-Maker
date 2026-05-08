from datetime import datetime

from app.core.exceptions import ConflictError
from app.repositories.match import MatchRepository


class ValidationService:
    def __init__(self, matches: MatchRepository) -> None:
        self.matches = matches

    def ensure_referee_is_available(
        self,
        *,
        referee_id: int,
        match_datetime: datetime,
        exclude_match_id: int | None = None,
    ) -> None:
        existing_match = self.matches.get_referee_match_at(
            referee_id=referee_id,
            match_datetime=match_datetime,
            exclude_match_id=exclude_match_id,
        )
        if existing_match is not None:
            raise ConflictError("Referee is already assigned to a parallel match.")
