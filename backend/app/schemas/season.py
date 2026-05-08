from datetime import date

from pydantic import BaseModel, ConfigDict

from app.core.constants import SeasonStatus


class SeasonBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    status: SeasonStatus = SeasonStatus.PLANNED


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: SeasonStatus | None = None


class SeasonRead(SeasonBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
