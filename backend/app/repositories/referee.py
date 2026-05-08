from sqlalchemy.orm import Session

from app.models.referee import Referee
from app.repositories.base import BaseRepository


class RefereeRepository(BaseRepository[Referee]):
    def __init__(self, db: Session) -> None:
        super().__init__(Referee, db)
