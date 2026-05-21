from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match_lineup import MatchLineup
from app.repositories.base import BaseRepository


class MatchLineupRepository(BaseRepository[MatchLineup]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(MatchLineup, db, owner_id)

    def list_by_match(self, match_id: int) -> list[MatchLineup]:
        statement = select(MatchLineup).where(MatchLineup.match_id == match_id)
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())

    def list_by_match_and_team(
        self,
        *,
        match_id: int,
        team_id: int,
    ) -> list[MatchLineup]:
        statement = select(MatchLineup).where(
            MatchLineup.match_id == match_id,
            MatchLineup.team_id == team_id,
        )
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())

    def get_by_match_and_player(
        self,
        *,
        match_id: int,
        player_id: int,
    ) -> MatchLineup | None:
        statement = select(MatchLineup).where(
            MatchLineup.match_id == match_id,
            MatchLineup.player_id == player_id,
        )
        statement = self._filter_owner(statement)
        return self.db.scalar(statement)

    def get_by_match_team_and_number(
        self,
        *,
        match_id: int,
        team_id: int,
        number: int,
        exclude_lineup_id: int | None = None,
    ) -> MatchLineup | None:
        statement = select(MatchLineup).where(
            MatchLineup.match_id == match_id,
            MatchLineup.team_id == team_id,
            MatchLineup.number == number,
        )
        if exclude_lineup_id is not None:
            statement = statement.where(MatchLineup.id != exclude_lineup_id)
        statement = self._filter_owner(statement)
        return self.db.scalar(statement)
