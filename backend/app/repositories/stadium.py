from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stadium import Stadium
from app.repositories.base import BaseRepository


class StadiumRepository(BaseRepository[Stadium]):
    def __init__(self, db: Session) -> None:
        super().__init__(Stadium, db)

    def get_by_name(self, name: str) -> Stadium | None:
        return self.db.scalar(select(Stadium).where(Stadium.name == name))

    def get_home_stadium_for_team(self, team_id: int) -> Stadium | None:
        statement = (
            select(Stadium)
            .where(Stadium.home_team_id == team_id)
            .order_by(Stadium.id)
            .limit(1)
        )
        return self.db.scalar(statement)
