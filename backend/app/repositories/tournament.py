from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tournament import Tournament
from app.repositories.base import BaseRepository


class TournamentRepository(BaseRepository[Tournament]):
    def __init__(self, db: Session) -> None:
        super().__init__(Tournament, db)

    def get_by_season_and_name(self, *, season_id: int, name: str) -> Tournament | None:
        return self.db.scalar(
            select(Tournament).where(
                Tournament.season_id == season_id,
                Tournament.name == name,
            )
        )
