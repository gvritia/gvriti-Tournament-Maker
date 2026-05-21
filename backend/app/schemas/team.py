from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TeamBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    city: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=160)
    emblem_url: str | None = Field(default=None, max_length=2048)
    previous_season_place: int | None = Field(default=None, ge=1)

    @field_validator("emblem_url")
    @classmethod
    def validate_emblem_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith(("http://", "https://")):
            raise ValueError("emblem_url must be an HTTP or HTTPS URL.")
        return value


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=160)
    emblem_url: str | None = Field(default=None, max_length=2048)
    previous_season_place: int | None = Field(default=None, ge=1)

    @field_validator("emblem_url")
    @classmethod
    def validate_emblem_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith(("http://", "https://")):
            raise ValueError("emblem_url must be an HTTP or HTTPS URL.")
        return value


class TeamRead(TeamBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
