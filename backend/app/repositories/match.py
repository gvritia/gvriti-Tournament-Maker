from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    def __init__(self, db: Session) -> None:
        super().__init__(Match, db)

    def list_team_matches_between(
        self,
        *,
        team_id: int,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[Match]:
        statement = select(Match).where(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.match_datetime >= starts_at,
            Match.match_datetime < ends_at,
        )
        return list(self.db.scalars(statement).all())
