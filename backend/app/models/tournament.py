from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import TournamentStatus, TournamentType
from app.db.base import Base, enum_column

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.season import Season


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160), index=True)
    type: Mapped[TournamentType] = mapped_column(enum_column(TournamentType))
    status: Mapped[TournamentStatus] = mapped_column(
        enum_column(TournamentStatus),
        default=TournamentStatus.PLANNED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    season: Mapped[Season] = relationship(back_populates="tournaments")
    matches: Mapped[list[Match]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
