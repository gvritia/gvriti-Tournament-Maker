from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.core.constants import MatchStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.match import Match
from app.models.stats import TeamSeasonStats
from app.repositories.match import MatchRepository
from app.repositories.season import SeasonRepository
from app.repositories.stats import TeamSeasonStatsRepository


@dataclass
class TeamStandingAccumulator:
    team_id: int
    season_id: int
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_scored - self.goals_conceded

    def record_match(self, *, goals_for: int, goals_against: int) -> None:
        self.played += 1
        self.goals_scored += goals_for
        self.goals_conceded += goals_against
        if goals_for > goals_against:
            self.wins += 1
            self.points += 3
        elif goals_for == goals_against:
            self.draws += 1
            self.points += 1
        else:
            self.losses += 1


class StandingsService:
    def __init__(
        self,
        seasons: SeasonRepository,
        matches: MatchRepository,
        team_stats: TeamSeasonStatsRepository,
    ) -> None:
        self.seasons = seasons
        self.matches = matches
        self.team_stats = team_stats

    def get_season_standings(self, season_id: int) -> list[TeamSeasonStats]:
        self._ensure_season_exists(season_id)
        return self.team_stats.list_by_season(season_id)

    def recalculate_for_season(self, season_id: int) -> list[TeamSeasonStats]:
        self._ensure_season_exists(season_id)
        try:
            self.rebuild_for_season(season_id)
            self.team_stats.db.commit()
        except IntegrityError as exc:
            self.team_stats.db.rollback()
            raise ConflictError(
                "Could not recalculate standings because of a conflict."
            ) from exc
        return self.team_stats.list_by_season(season_id)

    def rebuild_for_season(self, season_id: int) -> None:
        matches = self.matches.list_championship_matches_by_season(season_id)
        accumulators = self._build_accumulators(
            season_id=season_id,
            matches=matches,
        )
        ordered_accumulators = self._sort_accumulators(accumulators.values())

        self.team_stats.delete_by_season(season_id)
        for place, accumulator in enumerate(ordered_accumulators, start=1):
            self.team_stats.add(
                TeamSeasonStats(
                    team_id=accumulator.team_id,
                    season_id=accumulator.season_id,
                    played=accumulator.played,
                    wins=accumulator.wins,
                    draws=accumulator.draws,
                    losses=accumulator.losses,
                    goals_scored=accumulator.goals_scored,
                    goals_conceded=accumulator.goals_conceded,
                    goal_difference=accumulator.goal_difference,
                    points=accumulator.points,
                    place=place,
                )
            )

    def _ensure_season_exists(self, season_id: int) -> None:
        if self.seasons.get(season_id) is None:
            raise NotFoundError("Season not found.")

    def _build_accumulators(
        self,
        *,
        season_id: int,
        matches: list[Match],
    ) -> dict[int, TeamStandingAccumulator]:
        accumulators: dict[int, TeamStandingAccumulator] = {}
        for match in matches:
            for team_id in (match.home_team_id, match.away_team_id):
                accumulators.setdefault(
                    team_id,
                    TeamStandingAccumulator(team_id=team_id, season_id=season_id),
                )
            if (
                match.status != MatchStatus.FINISHED
                or match.home_score is None
                or match.away_score is None
            ):
                continue
            accumulators[match.home_team_id].record_match(
                goals_for=match.home_score,
                goals_against=match.away_score,
            )
            accumulators[match.away_team_id].record_match(
                goals_for=match.away_score,
                goals_against=match.home_score,
            )
        return accumulators

    def _sort_accumulators(
        self,
        accumulators: Iterable[TeamStandingAccumulator],
    ) -> list[TeamStandingAccumulator]:
        return sorted(
            accumulators,
            key=lambda item: (
                -item.points,
                -item.goal_difference,
                -item.goals_scored,
                item.team_id,
            ),
        )
