from datetime import datetime, timedelta

from app.core.exceptions import ConflictError
from app.repositories.match import MatchRepository
from app.utils.datetime_utils import start_of_day, start_of_week


class ScheduleService:
    def __init__(self, matches: MatchRepository) -> None:
        self.matches = matches

    def validate_team_can_play_at(
        self,
        *,
        team_id: int,
        match_datetime: datetime,
        exclude_match_id: int | None = None,
    ) -> None:
        """Validate calendar limits before scheduling or moving a match."""
        day_start = start_of_day(match_datetime)
        day_matches = self.matches.list_team_matches_between(
            team_id=team_id,
            starts_at=day_start,
            ends_at=day_start + timedelta(days=1),
            exclude_match_id=exclude_match_id,
        )
        if day_matches:
            raise ConflictError("A team cannot play more than one match per day.")

        week_start = start_of_week(match_datetime)
        week_matches = self.matches.list_team_matches_between(
            team_id=team_id,
            starts_at=week_start,
            ends_at=week_start + timedelta(days=7),
            exclude_match_id=exclude_match_id,
        )
        if len(week_matches) >= 2:
            raise ConflictError("A team cannot play more than two matches per week.")

    def validate_teams_can_play_at(
        self,
        *,
        home_team_id: int,
        away_team_id: int,
        match_datetime: datetime,
        exclude_match_id: int | None = None,
    ) -> None:
        self.validate_team_can_play_at(
            team_id=home_team_id,
            match_datetime=match_datetime,
            exclude_match_id=exclude_match_id,
        )
        self.validate_team_can_play_at(
            team_id=away_team_id,
            match_datetime=match_datetime,
            exclude_match_id=exclude_match_id,
        )
