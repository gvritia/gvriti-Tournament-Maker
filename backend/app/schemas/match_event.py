from pydantic import BaseModel, ConfigDict

from app.core.constants import MatchEventType


class MatchEventBase(BaseModel):
    match_id: int
    team_id: int
    player_id: int
    assist_player_id: int | None = None
    event_type: MatchEventType
    minute: int


class MatchEventCreate(MatchEventBase):
    pass


class MatchEventUpdate(BaseModel):
    assist_player_id: int | None = None
    event_type: MatchEventType | None = None
    minute: int | None = None


class MatchEventRead(MatchEventBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
