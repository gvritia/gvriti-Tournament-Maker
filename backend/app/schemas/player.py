from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import PlayerPosition


class PlayerBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    age: int | None = Field(default=None, ge=14, le=60)
    position: PlayerPosition
    number: int = Field(ge=1, le=99)
    team_id: int


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    age: int | None = Field(default=None, ge=14, le=60)
    position: PlayerPosition | None = None
    number: int | None = Field(default=None, ge=1, le=99)
    team_id: int | None = None


class PlayerRead(PlayerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
