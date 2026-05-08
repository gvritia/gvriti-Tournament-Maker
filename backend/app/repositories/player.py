from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.player import Player
from app.repositories.base import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    def __init__(self, db: Session) -> None:
        super().__init__(Player, db)

    def get_by_team_and_number(self, *, team_id: int, number: int) -> Player | None:
        return self.db.scalar(
            select(Player).where(Player.team_id == team_id, Player.number == number)
        )
