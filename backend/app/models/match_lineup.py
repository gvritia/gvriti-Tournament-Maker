from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MatchLineup(Base):
    __tablename__ = "match_lineups"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_match_lineup_player"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    is_starting: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[str] = mapped_column(String(80))
    number: Mapped[int] = mapped_column(Integer)

    match: Mapped["Match"] = relationship(back_populates="lineups")
    team: Mapped["Team"] = relationship(back_populates="lineups")
    player: Mapped["Player"] = relationship(back_populates="lineups")
