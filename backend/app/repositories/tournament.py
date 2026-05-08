from sqlalchemy.orm import Session

from app.models.tournament import Tournament
from app.repositories.base import BaseRepository


class TournamentRepository(BaseRepository[Tournament]):
    def __init__(self, db: Session) -> None:
        super().__init__(Tournament, db)
