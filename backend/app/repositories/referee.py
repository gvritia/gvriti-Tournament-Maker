from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.referee import Referee
from app.repositories.base import BaseRepository


class RefereeRepository(BaseRepository[Referee]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(Referee, db, owner_id)

    def get_by_full_name(self, full_name: str) -> Referee | None:
        statement = select(Referee).where(Referee.full_name == full_name)
        statement = self._filter_owner(statement)
        return self.db.scalar(statement)
