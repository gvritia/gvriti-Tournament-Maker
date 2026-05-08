from sqlalchemy.orm import Session

from app.models.player import Player
from app.repositories.base import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    def __init__(self, db: Session) -> None:
        super().__init__(Player, db)
