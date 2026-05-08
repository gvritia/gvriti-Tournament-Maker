from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.referee import Referee
from app.repositories.base import BaseRepository


class RefereeRepository(BaseRepository[Referee]):
    def __init__(self, db: Session) -> None:
        super().__init__(Referee, db)

    def get_by_full_name(self, full_name: str) -> Referee | None:
        return self.db.scalar(select(Referee).where(Referee.full_name == full_name))
