from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.stats import PlayerSeasonStats, TeamSeasonStats
from app.repositories.base import BaseRepository


class TeamSeasonStatsRepository(BaseRepository[TeamSeasonStats]):
    def __init__(self, db: Session) -> None:
        super().__init__(TeamSeasonStats, db)

    def list_by_season(self, season_id: int) -> list[TeamSeasonStats]:
        statement = (
            select(TeamSeasonStats)
            .where(TeamSeasonStats.season_id == season_id)
            .order_by(TeamSeasonStats.place, TeamSeasonStats.team_id)
        )
        return list(self.db.scalars(statement).all())

    def delete_by_season(self, season_id: int) -> None:
        self.db.execute(
            delete(TeamSeasonStats).where(TeamSeasonStats.season_id == season_id)
        )
        self.db.flush()


class PlayerSeasonStatsRepository(BaseRepository[PlayerSeasonStats]):
    def __init__(self, db: Session) -> None:
        super().__init__(PlayerSeasonStats, db)

    def list_by_season(self, season_id: int) -> list[PlayerSeasonStats]:
        statement = (
            select(PlayerSeasonStats)
            .where(PlayerSeasonStats.season_id == season_id)
            .order_by(PlayerSeasonStats.player_id)
        )
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
        return list(self.db.scalars(statement).all())

    def delete_by_season(self, season_id: int) -> None:
        self.db.execute(
            delete(PlayerSeasonStats).where(PlayerSeasonStats.season_id == season_id)
        )
        self.db.flush()
