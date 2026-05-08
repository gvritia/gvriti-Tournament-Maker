from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    city: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=160)
    previous_season_place: int | None = Field(default=None, ge=1)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=160)
    previous_season_place: int | None = Field(default=None, ge=1)


class TeamRead(TeamBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
