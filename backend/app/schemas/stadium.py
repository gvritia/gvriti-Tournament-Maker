from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StadiumBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    city: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=255)
    capacity: int = Field(gt=0)
    home_team_id: int | None = None


class StadiumCreate(StadiumBase):
    pass


class StadiumUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    capacity: int | None = Field(default=None, gt=0)
    home_team_id: int | None = None


class StadiumRead(StadiumBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
