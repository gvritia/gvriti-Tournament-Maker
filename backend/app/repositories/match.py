from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.constants import TournamentType
from app.models.match import Match
from app.models.tournament import Tournament
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
        exclude_match_id: int | None = None,
    ) -> list[Match]:
        statement = select(Match).where(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.match_datetime >= starts_at,
            Match.match_datetime < ends_at,
        )
        if exclude_match_id is not None:
            statement = statement.where(Match.id != exclude_match_id)
        return list(self.db.scalars(statement).all())

    def get_referee_match_at(
        self,
        *,
        referee_id: int,
        match_datetime: datetime,
        exclude_match_id: int | None = None,
    ) -> Match | None:
        statement = select(Match).where(
            Match.referee_id == referee_id,
            Match.match_datetime == match_datetime,
        )
        if exclude_match_id is not None:
            statement = statement.where(Match.id != exclude_match_id)
        return self.db.scalar(statement)

    def get_next_team_match_after(
        self,
        *,
        team_id: int,
        season_id: int,
        after_match_datetime: datetime,
    ) -> Match | None:
        statement = (
            select(Match)
            .where(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.season_id == season_id,
                Match.match_datetime > after_match_datetime,
            )
            .order_by(Match.match_datetime, Match.id)
            .limit(1)
        )
        return self.db.scalar(statement)

    def list_by_season(self, season_id: int) -> list[Match]:
        statement = (
            select(Match)
            .where(Match.season_id == season_id)
            .order_by(Match.match_datetime, Match.id)
        )
        return list(self.db.scalars(statement).all())

    def list_by_stadium(self, stadium_id: int) -> list[Match]:
        statement = (
            select(Match)
            .where(Match.stadium_id == stadium_id)
            .order_by(Match.match_datetime, Match.id)
        )
        return list(self.db.scalars(statement).all())

    def list_championship_matches_by_season(self, season_id: int) -> list[Match]:
        statement = (
            select(Match)
            .join(Tournament, Tournament.id == Match.tournament_id)
            .where(
                Match.season_id == season_id,
                Tournament.type == TournamentType.CHAMPIONSHIP,
            )
            .order_by(Match.match_datetime, Match.id)
        )
        return list(self.db.scalars(statement).all())
