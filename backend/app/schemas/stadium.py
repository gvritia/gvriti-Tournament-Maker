from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StadiumBase(BaseModel):
    name: str
    city: str
    address: str
    capacity: int
    home_team_id: int | None = None


class StadiumCreate(StadiumBase):
    pass


class StadiumUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    capacity: int | None = None
    home_team_id: int | None = None


class StadiumRead(StadiumBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
