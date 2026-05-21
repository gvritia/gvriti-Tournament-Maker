from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import MatchEventType


class MatchEventBase(BaseModel):
    team_id: int = Field(gt=0)
    player_id: int = Field(gt=0)
    assist_player_id: int | None = Field(default=None, gt=0)
    event_type: MatchEventType
    minute: int = Field(ge=0, le=130)


class MatchEventCreate(MatchEventBase):
    pass


class MatchEventUpdate(BaseModel):
    team_id: int | None = Field(default=None, gt=0)
    player_id: int | None = Field(default=None, gt=0)
    assist_player_id: int | None = Field(default=None, gt=0)
    event_type: MatchEventType | None = None
    minute: int | None = Field(default=None, ge=0, le=130)


class MatchFinish(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)


class MatchEventRead(MatchEventBase):
    id: int
    match_id: int

    model_config = ConfigDict(from_attributes=True)
