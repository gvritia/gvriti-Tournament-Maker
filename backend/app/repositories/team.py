from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.team import Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    def __init__(self, db: Session) -> None:
        super().__init__(Team, db)

    def get_by_name(self, name: str) -> Team | None:
        return self.db.scalar(select(Team).where(Team.name == name))

    def get_previous_season_table_size(self) -> int | None:
        return self.db.scalar(select(func.max(Team.previous_season_place)))
