from sqlalchemy.orm import Session

from app.models.stadium import Stadium
from app.repositories.base import BaseRepository


class StadiumRepository(BaseRepository[Stadium]):
    def __init__(self, db: Session) -> None:
        super().__init__(Stadium, db)
