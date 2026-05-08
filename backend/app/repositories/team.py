from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    def __init__(self, db: Session) -> None:
        super().__init__(Team, db)

    def get_by_name(self, name: str) -> Team | None:
        return self.db.scalar(select(Team).where(Team.name == name))
