from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.season import Season
from app.repositories.base import BaseRepository


class SeasonRepository(BaseRepository[Season]):
    def __init__(self, db: Session) -> None:
        super().__init__(Season, db)

    def get_by_name(self, name: str) -> Season | None:
        return self.db.scalar(select(Season).where(Season.name == name))
