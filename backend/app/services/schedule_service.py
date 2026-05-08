from datetime import datetime

from app.core.exceptions import BusinessRuleError
from app.repositories.match import MatchRepository


class ScheduleService:
    def __init__(self, matches: MatchRepository) -> None:
        self.matches = matches

    def validate_team_can_play_at(self, *, team_id: int, match_datetime: datetime) -> None:
        """Validate calendar limits before scheduling or moving a match."""
        raise BusinessRuleError(
            "Calendar validation is reserved for the next implementation iteration."
        )
