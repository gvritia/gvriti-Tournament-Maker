from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tournament import Tournament
from app.repositories.base import BaseRepository


class TournamentRepository(BaseRepository[Tournament]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(Tournament, db, owner_id)

    def get_by_season_and_name(self, *, season_id: int, name: str) -> Tournament | None:
        statement = select(Tournament).where(
            Tournament.season_id == season_id,
            Tournament.name == name,
        )
        statement = self._filter_owner(statement)
        return self.db.scalar(statement)

    def list_by_season(self, season_id: int) -> list[Tournament]:
        statement = select(Tournament).where(Tournament.season_id == season_id)
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())
