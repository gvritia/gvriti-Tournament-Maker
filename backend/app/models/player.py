from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import PlayerPosition
from app.db.base import Base, enum_column


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("team_id", "number", name="uq_player_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[PlayerPosition] = mapped_column(enum_column(PlayerPosition))
    number: Mapped[int] = mapped_column(Integer)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    team: Mapped["Team"] = relationship(back_populates="players")
    lineups: Mapped[list["MatchLineup"]] = relationship(back_populates="player")
    events: Mapped[list["MatchEvent"]] = relationship(
        back_populates="player",
        foreign_keys="MatchEvent.player_id",
    )
    assist_events: Mapped[list["MatchEvent"]] = relationship(
        back_populates="assist_player",
        foreign_keys="MatchEvent.assist_player_id",
    )
    season_stats: Mapped[list["PlayerSeasonStats"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )
