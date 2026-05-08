from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CupStage, MatchStatus
from app.db.base import Base, enum_column


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="ck_match_distinct_teams"),
        CheckConstraint("ticket_sold >= 0", name="ck_match_ticket_sold"),
        CheckConstraint("home_score IS NULL OR home_score >= 0", name="ck_home_score"),
        CheckConstraint("away_score IS NULL OR away_score >= 0", name="ck_away_score"),
        Index("ix_matches_datetime", "match_datetime"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
    )
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"))
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    stadium_id: Mapped[int] = mapped_column(ForeignKey("stadiums.id"))
    referee_id: Mapped[int | None] = mapped_column(
        ForeignKey("referees.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[MatchStatus] = mapped_column(
        enum_column(MatchStatus),
        default=MatchStatus.SCHEDULED,
    )
    round_number: Mapped[int] = mapped_column(Integer)
    stage: Mapped[CupStage | None] = mapped_column(enum_column(CupStage), nullable=True)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ticket_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    ticket_sold: Mapped[int] = mapped_column(Integer, default=0)
    income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    tournament: Mapped["Tournament"] = relationship(back_populates="matches")
    season: Mapped["Season"] = relationship(back_populates="matches")
    home_team: Mapped["Team"] = relationship(
        back_populates="home_matches",
        foreign_keys=[home_team_id],
    )
    away_team: Mapped["Team"] = relationship(
        back_populates="away_matches",
        foreign_keys=[away_team_id],
    )
    stadium: Mapped["Stadium"] = relationship(back_populates="matches")
    referee: Mapped["Referee | None"] = relationship(back_populates="matches")
    lineups: Mapped[list["MatchLineup"]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["MatchEvent"]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
    )
