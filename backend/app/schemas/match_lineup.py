from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class MatchLineupGenerate(BaseModel):
    team_id: int = Field(gt=0)
    lineup_size: int = Field(default=11, ge=1, le=25)
    starting_size: int | None = Field(default=None, ge=0, le=11)
    preferred_player_ids: list[int] = Field(default_factory=list)
    replace_existing: bool = False

    @model_validator(mode="after")
    def validate_sizes(self) -> "MatchLineupGenerate":
        if self.starting_size is not None and self.starting_size > self.lineup_size:
            raise ValueError("starting_size cannot be greater than lineup_size.")
        return self


class MatchLineupRead(MatchLineupBase):
    id: int
    match_id: int

    model_config = ConfigDict(from_attributes=True)
