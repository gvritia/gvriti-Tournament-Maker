from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.match import MatchRead


class CupSemifinalsGenerate(BaseModel):
    team_ids: list[int] | None = Field(default=None, min_length=4, max_length=4)
    use_previous_season_places: bool = False
    match_datetimes: list[datetime] = Field(min_length=2, max_length=2)
    fallback_stadium_id: int | None = Field(default=None, gt=0)
    stadium_ids_by_team: dict[int, int] = Field(default_factory=dict)


class CupFinalGenerate(BaseModel):
    match_datetime: datetime
    stadium_id: int = Field(gt=0)


class CupMatchNode(BaseModel):
    match: MatchRead
    winner_team_id: int | None = None


class CupBracketRead(BaseModel):
    tournament_id: int
    season_id: int
    semifinals: list[CupMatchNode]
    final: CupMatchNode | None = None
    champion_team_id: int | None = None
