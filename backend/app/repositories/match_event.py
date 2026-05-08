from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import MatchEventType
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.repositories.base import BaseRepository


class MatchEventRepository(BaseRepository[MatchEvent]):
    def __init__(self, db: Session) -> None:
        super().__init__(MatchEvent, db)

    def list_by_match(self, match_id: int) -> list[MatchEvent]:
        statement = (
            select(MatchEvent)
            .where(MatchEvent.match_id == match_id)
            .order_by(MatchEvent.minute, MatchEvent.id)
        )
        return list(self.db.scalars(statement).all())

    def list_player_events_before_match(
        self,
        *,
        player_id: int,
        season_id: int,
        match_datetime: datetime,
        event_type: MatchEventType,
    ) -> list[MatchEvent]:
        statement = (
            select(MatchEvent)
            .join(Match, Match.id == MatchEvent.match_id)
            .where(
                MatchEvent.player_id == player_id,
                MatchEvent.event_type == event_type,
                Match.season_id == season_id,
                Match.match_datetime < match_datetime,
            )
            .order_by(Match.match_datetime, MatchEvent.id)
        )
        return list(self.db.scalars(statement).all())

    def count_match_goals_for_team(self, *, match_id: int, team_id: int) -> int:
        statement = select(MatchEvent).where(
            MatchEvent.match_id == match_id,
            MatchEvent.team_id == team_id,
            MatchEvent.event_type == MatchEventType.GOAL,
        )
        return len(self.db.scalars(statement).all())
