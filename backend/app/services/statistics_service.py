from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.core.constants import MatchEventType
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match_event import MatchEvent
from app.models.stats import PlayerSeasonStats
from app.repositories.match_event import MatchEventRepository
from app.repositories.season import SeasonRepository
from app.repositories.stats import PlayerSeasonStatsRepository

PLAYER_STAT_METRICS = {
    "goals",
    "assists",
    "saves",
    "yellow_cards",
    "red_cards",
}


@dataclass
class PlayerStatsAccumulator:
    player_id: int
    season_id: int
    goals: int = 0
    assists: int = 0
    saves: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


class StatisticsService:
    def __init__(
        self,
        seasons: SeasonRepository,
        events: MatchEventRepository,
        player_stats: PlayerSeasonStatsRepository,
    ) -> None:
        self.seasons = seasons
        self.events = events
        self.player_stats = player_stats

    def get_player_stats_for_season(self, season_id: int) -> list[PlayerSeasonStats]:
        self._ensure_season_exists(season_id)
        return self.player_stats.list_by_season(season_id)

    def recalculate_player_stats_for_season(
        self,
        season_id: int,
    ) -> list[PlayerSeasonStats]:
        self._ensure_season_exists(season_id)
        try:
            self.rebuild_player_stats_for_season(season_id)
            self.player_stats.db.commit()
        except IntegrityError as exc:
            self.player_stats.db.rollback()
            raise ConflictError(
                "Could not recalculate player statistics because of a conflict."
            ) from exc
        return self.player_stats.list_by_season(season_id)

    def rebuild_player_stats_for_season(self, season_id: int) -> None:
        events = self.events.list_finished_events_by_season(season_id)
        accumulators = self._build_accumulators(season_id=season_id, events=events)

        self.player_stats.delete_by_season(season_id)
        for accumulator in self._sort_accumulators(accumulators.values()):
            self.player_stats.add(
                PlayerSeasonStats(
                    player_id=accumulator.player_id,
                    season_id=accumulator.season_id,
                    goals=accumulator.goals,
                    assists=accumulator.assists,
                    saves=accumulator.saves,
                    yellow_cards=accumulator.yellow_cards,
                    red_cards=accumulator.red_cards,
                )
            )

    def get_leaders(
        self,
        *,
        season_id: int,
        metric: str,
        limit: int,
    ) -> list[PlayerSeasonStats]:
        self._ensure_season_exists(season_id)
        self._ensure_metric_is_supported(metric)
        return self.player_stats.list_leaders(
            season_id=season_id,
            metric=metric,
            limit=limit,
        )

    def _ensure_season_exists(self, season_id: int) -> None:
        if self.seasons.get(season_id) is None:
            raise NotFoundError("Season not found.")

    def _ensure_metric_is_supported(self, metric: str) -> None:
        if metric not in PLAYER_STAT_METRICS:
            raise BusinessRuleError("Unsupported player statistics metric.")

    def _build_accumulators(
        self,
        *,
        season_id: int,
        events: list[MatchEvent],
    ) -> dict[int, PlayerStatsAccumulator]:
        accumulators: dict[int, PlayerStatsAccumulator] = {}
        for event in events:
            player_stats = self._get_or_create_accumulator(
                accumulators=accumulators,
                player_id=event.player_id,
                season_id=season_id,
            )

            if event.event_type == MatchEventType.GOAL:
                player_stats.goals += 1
                if event.assist_player_id is not None:
                    assist_stats = self._get_or_create_accumulator(
                        accumulators=accumulators,
                        player_id=event.assist_player_id,
                        season_id=season_id,
                    )
                    assist_stats.assists += 1
            elif event.event_type == MatchEventType.ASSIST:
                player_stats.assists += 1
            elif event.event_type == MatchEventType.SAVE:
                player_stats.saves += 1
            elif event.event_type == MatchEventType.YELLOW_CARD:
                player_stats.yellow_cards += 1
            elif event.event_type == MatchEventType.RED_CARD:
                player_stats.red_cards += 1
        return accumulators

    def _get_or_create_accumulator(
        self,
        *,
        accumulators: dict[int, PlayerStatsAccumulator],
        player_id: int,
        season_id: int,
    ) -> PlayerStatsAccumulator:
        return accumulators.setdefault(
            player_id,
            PlayerStatsAccumulator(player_id=player_id, season_id=season_id),
        )

    def _sort_accumulators(
        self,
        accumulators: Iterable[PlayerStatsAccumulator],
    ) -> list[PlayerStatsAccumulator]:
        return sorted(accumulators, key=lambda item: item.player_id)
