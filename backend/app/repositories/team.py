from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.team import Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(Team, db, owner_id)

    def get_by_name(self, name: str) -> Team | None:
        statement = select(Team).where(Team.name == name)
        statement = self._filter_owner(statement)
        return self.db.scalar(statement)

    def get_previous_season_table_size(self) -> int | None:
        statement = select(func.max(Team.previous_season_place))
        if self.owner_id is not None:
            statement = statement.where(Team.owner_id == self.owner_id)
        return self.db.scalar(statement)

    def list_top_by_previous_season_place(self, *, limit: int) -> list[Team]:
        statement = (
            select(Team)
            .where(Team.previous_season_place.is_not(None))
            .order_by(Team.previous_season_place, Team.id)
            .limit(limit)
        )
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())
