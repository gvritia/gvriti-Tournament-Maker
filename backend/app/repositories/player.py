from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.player import Player
from app.repositories.base import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(Player, db, owner_id)

    def get_by_team_and_number(self, *, team_id: int, number: int) -> Player | None:
        statement = select(Player).where(
            Player.team_id == team_id,
            Player.number == number,
        )
        statement = self._filter_owner(statement)
        return self.db.scalar(statement)

    def list_by_team(self, team_id: int) -> list[Player]:
        statement = select(Player).where(Player.team_id == team_id).order_by(Player.id)
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())
