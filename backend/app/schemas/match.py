from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import CupStage, MatchStatus


class MatchBase(BaseModel):
    tournament_id: int = Field(gt=0)
    season_id: int = Field(gt=0)
    home_team_id: int = Field(gt=0)
    away_team_id: int = Field(gt=0)
    stadium_id: int = Field(gt=0)
    referee_id: int | None = Field(default=None, gt=0)
    match_datetime: datetime
    status: MatchStatus = MatchStatus.SCHEDULED
    round_number: int = Field(ge=1)
    stage: CupStage | None = None


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    stadium_id: int | None = Field(default=None, gt=0)
    referee_id: int | None = Field(default=None, gt=0)
    match_datetime: datetime | None = None
    status: MatchStatus | None = None
    round_number: int | None = Field(default=None, ge=1)
    stage: CupStage | None = None
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    ticket_price: Decimal | None = Field(default=None, gt=0)
    ticket_sold: int | None = Field(default=None, ge=0)


class MatchRefereeAssign(BaseModel):
    referee_id: int = Field(gt=0)


class MatchReschedule(BaseModel):
    match_datetime: datetime


class MatchTicketPriceUpdate(BaseModel):
    ticket_price: Decimal = Field(gt=0)


class MatchRead(MatchBase):
    id: int
    ticket_price: Decimal | None = None
    home_score: int | None = None
    away_score: int | None = None
    ticket_sold: int
    income: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)
