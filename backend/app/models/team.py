from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    city: Mapped[str] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    previous_season_place: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    players: Mapped[list["Player"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
    )
    home_stadiums: Mapped[list["Stadium"]] = relationship(back_populates="home_team")
    home_matches: Mapped[list["Match"]] = relationship(
        back_populates="home_team",
        foreign_keys="Match.home_team_id",
    )
    away_matches: Mapped[list["Match"]] = relationship(
        back_populates="away_team",
        foreign_keys="Match.away_team_id",
    )
    lineups: Mapped[list["MatchLineup"]] = relationship(back_populates="team")
    events: Mapped[list["MatchEvent"]] = relationship(back_populates="team")
    season_stats: Mapped[list["TeamSeasonStats"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
    )
