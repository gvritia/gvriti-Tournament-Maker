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

    def list_top_by_previous_season_place(self, *, limit: int) -> list[Team]:
        statement = (
            select(Team)
            .where(Team.previous_season_place.is_not(None))
            .order_by(Team.previous_season_place, Team.id)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
