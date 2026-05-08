from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    city: str
    address: str | None = None
    manager_name: str | None = None
    previous_season_place: int | None = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    manager_name: str | None = None
    previous_season_place: int | None = None


class TeamRead(TeamBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
