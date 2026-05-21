from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.stats import PlayerSeasonStats, TeamSeasonStats
from app.repositories.base import BaseRepository


class TeamSeasonStatsRepository(BaseRepository[TeamSeasonStats]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(TeamSeasonStats, db, owner_id)

    def list_by_season(self, season_id: int) -> list[TeamSeasonStats]:
        statement = (
            select(TeamSeasonStats)
            .where(TeamSeasonStats.season_id == season_id)
            .order_by(TeamSeasonStats.place, TeamSeasonStats.team_id)
        )
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())

    def delete_by_season(self, season_id: int) -> None:
        statement = delete(TeamSeasonStats).where(
            TeamSeasonStats.season_id == season_id
        )
        if self.owner_id is not None:
            statement = statement.where(TeamSeasonStats.owner_id == self.owner_id)
        self.db.execute(statement)
        self.db.flush()


class PlayerSeasonStatsRepository(BaseRepository[PlayerSeasonStats]):
    def __init__(self, db: Session, owner_id: int | None = None) -> None:
        super().__init__(PlayerSeasonStats, db, owner_id)

    def list_by_season(self, season_id: int) -> list[PlayerSeasonStats]:
        statement = (
            select(PlayerSeasonStats)
            .where(PlayerSeasonStats.season_id == season_id)
            .order_by(PlayerSeasonStats.player_id)
        )
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())

    def list_leaders(
        self,
        *,
        season_id: int,
        metric: str,
        limit: int,
    ) -> list[PlayerSeasonStats]:
        metric_column = getattr(PlayerSeasonStats, metric)
        statement = (
            select(PlayerSeasonStats)
            .where(PlayerSeasonStats.season_id == season_id)
            .order_by(metric_column.desc(), PlayerSeasonStats.player_id)
            .limit(limit)
        )
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())

    def delete_by_season(self, season_id: int) -> None:
        statement = delete(PlayerSeasonStats).where(
            PlayerSeasonStats.season_id == season_id
        )
        if self.owner_id is not None:
            statement = statement.where(PlayerSeasonStats.owner_id == self.owner_id)
        self.db.execute(statement)
        self.db.flush()
