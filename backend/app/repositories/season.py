from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.season import Season
from app.repositories.base import BaseRepository


class SeasonRepository(BaseRepository[Season]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(Season, db, owner_id)

    def get_by_name(self, name: str) -> Season | None:
        statement = select(Season).where(Season.name == name)
        statement = self._filter_owner(statement)
        return self.db.scalar(statement)
