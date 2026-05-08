from pydantic import BaseModel, ConfigDict, Field


class MatchLineupBase(BaseModel):
    team_id: int = Field(gt=0)
    player_id: int = Field(gt=0)
    is_starting: bool = False
    position: str = Field(min_length=1, max_length=80)
    number: int = Field(ge=1, le=99)


class MatchLineupCreate(MatchLineupBase):
    pass


class MatchLineupUpdate(BaseModel):
    is_starting: bool | None = None
    position: str | None = Field(default=None, min_length=1, max_length=80)
    number: int | None = Field(default=None, ge=1, le=99)


class MatchLineupRead(MatchLineupBase):
    id: int
    match_id: int

    model_config = ConfigDict(from_attributes=True)
