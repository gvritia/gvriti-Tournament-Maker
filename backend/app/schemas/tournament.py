from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import TournamentStatus, TournamentType


class TournamentBase(BaseModel):
    season_id: int
    name: str = Field(min_length=1, max_length=160)
    type: TournamentType
    status: TournamentStatus = TournamentStatus.PLANNED


class TournamentCreate(TournamentBase):
    pass


class TournamentUpdate(BaseModel):
    season_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    type: TournamentType | None = None
    status: TournamentStatus | None = None


class TournamentRead(TournamentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
