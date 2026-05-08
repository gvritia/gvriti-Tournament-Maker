from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SeasonStatus
from app.db.base import Base, enum_column


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[SeasonStatus] = mapped_column(
        enum_column(SeasonStatus),
        default=SeasonStatus.PLANNED,
    )

    tournaments: Mapped[list["Tournament"]] = relationship(back_populates="season")
    matches: Mapped[list["Match"]] = relationship(back_populates="season")
    team_stats: Mapped[list["TeamSeasonStats"]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
    )
    player_stats: Mapped[list["PlayerSeasonStats"]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
    )
