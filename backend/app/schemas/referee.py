from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RefereeBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)


class RefereeCreate(RefereeBase):
    pass


class RefereeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=160)


class RefereeRead(RefereeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
