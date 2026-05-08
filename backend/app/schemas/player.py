from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import PlayerPosition


class PlayerBase(BaseModel):
    full_name: str
    age: int | None = None
    position: PlayerPosition
    number: int
    team_id: int


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    full_name: str | None = None
    age: int | None = None
    position: PlayerPosition | None = None
    number: int | None = None
    team_id: int | None = None


class PlayerRead(PlayerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
