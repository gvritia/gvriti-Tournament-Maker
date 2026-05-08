from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.constants import CupStage, MatchStatus


class MatchBase(BaseModel):
    tournament_id: int
    season_id: int
    home_team_id: int
    away_team_id: int
    stadium_id: int
    referee_id: int | None = None
    match_datetime: datetime
    status: MatchStatus = MatchStatus.SCHEDULED
    round_number: int
    stage: CupStage | None = None
    ticket_price: Decimal | None = None


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    stadium_id: int | None = None
    referee_id: int | None = None
    match_datetime: datetime | None = None
    status: MatchStatus | None = None
    round_number: int | None = None
    stage: CupStage | None = None
    home_score: int | None = None
    away_score: int | None = None
    ticket_price: Decimal | None = None
    ticket_sold: int | None = None


class MatchRead(MatchBase):
    id: int
    home_score: int | None = None
    away_score: int | None = None
    ticket_sold: int
    income: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)
