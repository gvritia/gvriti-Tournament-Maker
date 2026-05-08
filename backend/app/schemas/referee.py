from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RefereeBase(BaseModel):
    full_name: str


class RefereeCreate(RefereeBase):
    pass


class RefereeUpdate(BaseModel):
    full_name: str | None = None


class RefereeRead(RefereeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
