from datetime import datetime, time

from pydantic import BaseModel, Field


class ChampionshipScheduleGenerate(BaseModel):
    start_datetime: datetime
    match_time: time | None = None
    interval_days: int = Field(default=4, ge=1)
    team_ids: list[int] = Field(min_length=2)
    fallback_stadium_id: int | None = Field(default=None, gt=0)
    stadium_ids_by_team: dict[int, int] = Field(default_factory=dict)
