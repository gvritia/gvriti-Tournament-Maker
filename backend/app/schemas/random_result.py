from pydantic import BaseModel

from app.schemas.match import MatchRead
from app.schemas.match_event import MatchEventRead


class RandomResultGenerate(BaseModel):
    seed: int | None = None


class RandomResultRead(BaseModel):
    match: MatchRead
    events: list[MatchEventRead]
