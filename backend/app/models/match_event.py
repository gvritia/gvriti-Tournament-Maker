from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MatchEventType
from app.db.base import Base, enum_column

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.player import Player
    from app.models.team import Team


class MatchEvent(Base):
    __tablename__ = "match_events"
    __table_args__ = (CheckConstraint("minute >= 0", name="ck_match_event_minute"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    assist_player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[MatchEventType] = mapped_column(enum_column(MatchEventType))
    minute: Mapped[int] = mapped_column(Integer)

    match: Mapped[Match] = relationship(back_populates="events")
    team: Mapped[Team] = relationship(back_populates="events")
    player: Mapped[Player] = relationship(
        back_populates="events",
        foreign_keys=[player_id],
    )
    assist_player: Mapped[Player | None] = relationship(
        back_populates="assist_events",
        foreign_keys=[assist_player_id],
    )
