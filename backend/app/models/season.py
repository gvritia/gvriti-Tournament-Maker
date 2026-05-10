from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SeasonStatus
from app.db.base import Base, enum_column

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.stats import PlayerSeasonStats, TeamSeasonStats
    from app.models.tournament import Tournament


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_season_owner_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[SeasonStatus] = mapped_column(
        enum_column(SeasonStatus),
        default=SeasonStatus.PLANNED,
    )

    tournaments: Mapped[list[Tournament]] = relationship(back_populates="season")
    matches: Mapped[list[Match]] = relationship(back_populates="season")
    team_stats: Mapped[list[TeamSeasonStats]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
    )
    player_stats: Mapped[list[PlayerSeasonStats]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
    )
