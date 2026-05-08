from pydantic import BaseModel, ConfigDict


class MatchLineupBase(BaseModel):
    match_id: int
    team_id: int
    player_id: int
    is_starting: bool = False
    position: str
    number: int


class MatchLineupCreate(MatchLineupBase):
    pass


class MatchLineupUpdate(BaseModel):
    is_starting: bool | None = None
    position: str | None = None
    number: int | None = None


class MatchLineupRead(MatchLineupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
