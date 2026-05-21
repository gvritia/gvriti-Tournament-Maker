from pydantic import BaseModel, ConfigDict


class TeamSeasonStatsBase(BaseModel):
    team_id: int
    season_id: int
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    goal_difference: int = 0
    points: int = 0
    place: int | None = None
    cup_place: int | None = None


class TeamSeasonStatsRead(TeamSeasonStatsBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PlayerSeasonStatsBase(BaseModel):
    player_id: int
    season_id: int
    goals: int = 0
    assists: int = 0
    saves: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


class PlayerSeasonStatsRead(PlayerSeasonStatsBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
