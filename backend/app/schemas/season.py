from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.constants import SeasonStatus


class SeasonBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    start_date: date
    end_date: date
    status: SeasonStatus = SeasonStatus.PLANNED

    @model_validator(mode="after")
    def validate_dates(self) -> "SeasonBase":
        if self.end_date < self.start_date:
            raise ValueError(
                "Season end_date must be greater than or equal to start_date."
            )
        return self


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    status: SeasonStatus | None = None


class SeasonRead(SeasonBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
