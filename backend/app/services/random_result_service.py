from random import Random

from sqlalchemy.exc import IntegrityError

from app.core.constants import (
    CupStage,
    MatchEventType,
    MatchStatus,
    PlayerPosition,
    TournamentType,
)
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_lineup import MatchLineup
from app.models.player import Player
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.match_lineup import MatchLineupRepository
from app.repositories.player import PlayerRepository
from app.repositories.referee import RefereeRepository
from app.repositories.season import SeasonRepository
from app.schemas.random_result import (
    RandomResultGenerate,
    RandomResultRead,
    RandomSeasonResultRead,
)
from app.services.standings_service import StandingsService
from app.services.statistics_service import StatisticsService

MAX_GOALS_PER_TEAM = 5
MAX_YELLOW_CARDS_PER_TEAM = 5
MAX_RED_CARDS_PER_TEAM = 1
MAX_SAVES_PER_TEAM = 10
REGULAR_MINUTE_MIN = 1
REGULAR_MINUTE_MAX = 90


class RandomResultService:
    def __init__(
        self,
        matches: MatchRepository,
        events: MatchEventRepository,
        players: PlayerRepository,
        lineups: MatchLineupRepository,
        referees: RefereeRepository,
        seasons: SeasonRepository,
        standings: StandingsService,
        statistics: StatisticsService,
    ) -> None:
        self.matches = matches
        self.events = events
        self.players = players
        self.lineups = lineups
        self.referees = referees
        self.seasons = seasons
        self.standings = standings
        self.statistics = statistics

    def generate_for_match(
        self,
        match_id: int,
        payload: RandomResultGenerate,
    ) -> RandomResultRead:
        match = self._get_match(match_id)
        self._ensure_match_can_be_generated(match)
        self._ensure_match_has_no_events(match.id)

        rng = Random(payload.seed)

        try:
            self._prepare_match_protocol_data(
                match=match,
                reserved_referee_ids_by_datetime={},
            )
            home_score, away_score, generated_events = self._build_generated_result(
                match=match,
                home_players=self._get_protocol_players(
                    match_id=match.id,
                    team_id=match.home_team_id,
                ),
                away_players=self._get_protocol_players(
                    match_id=match.id,
                    team_id=match.away_team_id,
                ),
                rng=rng,
            )
            self._apply_generated_result(
                match=match,
                home_score=home_score,
                away_score=away_score,
                generated_events=generated_events,
            )
            self.matches.db.flush()
            self._recalculate_finished_match_totals(match)
            self.matches.db.commit()
            self.matches.db.refresh(match)
        except (BusinessRuleError, ConflictError, NotFoundError):
            self.matches.db.rollback()
            raise
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(
                "Could not generate random match result because of a conflict."
            ) from exc

        return RandomResultRead(
            match=match,
            events=self.events.list_by_match(match.id),
        )

    def generate_for_season(
        self,
        season_id: int,
        payload: RandomResultGenerate,
    ) -> RandomSeasonResultRead:
        self._ensure_season_exists(season_id)
        matches = self.matches.list_by_season(season_id)
        if not matches:
            raise BusinessRuleError("Season has no matches to generate.")

        matches_to_generate = [
            match for match in matches if self._should_generate_in_season(match)
        ]

        for match in matches_to_generate:
            self._ensure_match_can_be_generated(match)
            self._ensure_match_has_no_events(match.id)
        rng = Random(payload.seed)
        try:
            reserved_referee_ids_by_datetime: dict[object, set[int]] = {}
            for match in matches_to_generate:
                self._prepare_match_protocol_data(
                    match=match,
                    reserved_referee_ids_by_datetime=reserved_referee_ids_by_datetime,
                )
                home_score, away_score, generated_events = self._build_generated_result(
                    match=match,
                    home_players=self._get_protocol_players(
                        match_id=match.id,
                        team_id=match.home_team_id,
                    ),
                    away_players=self._get_protocol_players(
                        match_id=match.id,
                        team_id=match.away_team_id,
                    ),
                    rng=rng,
                )
                self._apply_generated_result(
                    match=match,
                    home_score=home_score,
                    away_score=away_score,
                    generated_events=generated_events,
                )
                self.matches.db.flush()
            self.matches.db.flush()
            self.standings.rebuild_for_season(season_id)
            self.statistics.rebuild_player_stats_for_season(season_id)
            self.matches.db.commit()
            for match in matches_to_generate:
                self.matches.db.refresh(match)
        except (BusinessRuleError, ConflictError, NotFoundError):
            self.matches.db.rollback()
            raise
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(
                "Could not generate random season results because of a conflict."
            ) from exc

        return RandomSeasonResultRead(
            season_id=season_id,
            generated_count=len(matches_to_generate),
            results=[
                RandomResultRead(
                    match=match,
                    events=self.events.list_by_match(match.id),
                )
                for match in matches_to_generate
            ],
        )

    def _should_generate_in_season(self, match: Match) -> bool:
        if match.status in {MatchStatus.FINISHED, MatchStatus.CANCELLED}:
            return False
        return not self.events.list_by_match(match.id)

    def _recalculate_finished_match_totals(self, match: Match) -> None:
        self.matches.db.flush()
        if match.tournament.type == TournamentType.CHAMPIONSHIP:
            self.standings.rebuild_for_season(match.season_id)
        self.statistics.rebuild_player_stats_for_season(match.season_id)

    def _get_match(self, match_id: int) -> Match:
        match = self.matches.get(match_id)
        if match is None:
            raise NotFoundError("Match not found.")
        return match

    def _ensure_season_exists(self, season_id: int) -> None:
        if self.seasons.get(season_id) is None:
            raise NotFoundError("Season not found.")

    def _ensure_match_can_be_generated(self, match: Match) -> None:
        if match.status in {MatchStatus.FINISHED, MatchStatus.CANCELLED}:
            raise BusinessRuleError(
                "Random result cannot be generated for finished or cancelled matches."
            )

    def _ensure_match_has_no_events(self, match_id: int) -> None:
        if self.events.list_by_match(match_id):
            raise ConflictError(
                "Random result cannot be generated for a match with protocol events."
            )

    def _get_team_players(self, team_id: int) -> list[Player]:
        players = self.players.list_by_team(team_id)
        if not players:
            raise BusinessRuleError(
                "Random result generation requires players for both teams."
            )
        return players

    def _prepare_match_protocol_data(
        self,
        *,
        match: Match,
        reserved_referee_ids_by_datetime: dict[object, set[int]],
    ) -> None:
        self._ensure_match_has_referee(
            match=match,
            reserved_referee_ids_by_datetime=reserved_referee_ids_by_datetime,
        )
        self._ensure_match_has_protocol_lineup(
            match=match,
            team_id=match.home_team_id,
        )
        self._ensure_match_has_protocol_lineup(
            match=match,
            team_id=match.away_team_id,
        )
        self.matches.db.flush()

    def _ensure_match_has_referee(
        self,
        *,
        match: Match,
        reserved_referee_ids_by_datetime: dict[object, set[int]],
    ) -> None:
        reserved_referee_ids = reserved_referee_ids_by_datetime.setdefault(
            match.match_datetime,
            set(),
        )
        if match.referee_id is not None:
            if match.referee_id in reserved_referee_ids:
                raise ConflictError(
                    "Referee is already assigned to a parallel generated match."
                )
            existing_match = self.matches.get_referee_match_at(
                referee_id=match.referee_id,
                match_datetime=match.match_datetime,
                exclude_match_id=match.id,
            )
            if existing_match is not None:
                raise ConflictError("Referee is already assigned to a parallel match.")
            reserved_referee_ids.add(match.referee_id)
            return

        referees = self.referees.list_all_ordered()
        if not referees:
            raise BusinessRuleError(
                "Protocol generation requires a referee or at least one referee "
                "available for automatic assignment."
            )

        for referee in referees:
            if referee.id in reserved_referee_ids:
                continue
            existing_match = self.matches.get_referee_match_at(
                referee_id=referee.id,
                match_datetime=match.match_datetime,
            )
            if existing_match is None:
                match.referee_id = referee.id
                reserved_referee_ids.add(referee.id)
                return

        raise ConflictError("No referee is available for protocol generation.")

    def _ensure_match_has_protocol_lineup(self, *, match: Match, team_id: int) -> None:
        existing_lineups = self.lineups.list_by_match_and_team(
            match_id=match.id,
            team_id=team_id,
        )
        if existing_lineups:
            self._validate_existing_protocol_lineup(existing_lineups)
            return

        for player in self._select_generated_starting_lineup(
            match=match,
            team_id=team_id,
        ):
            self.lineups.add(
                MatchLineup(
                    owner_id=self.lineups.require_owner_id(),
                    match_id=match.id,
                    team_id=team_id,
                    player_id=player.id,
                    is_starting=True,
                    position=player.position.value,
                    number=player.number,
                )
            )

    def _validate_existing_protocol_lineup(
        self,
        lineups: list[MatchLineup],
    ) -> None:
        starting_lineups = [lineup for lineup in lineups if lineup.is_starting]
        if len(starting_lineups) < 11:
            raise ConflictError(
                "Protocol generation requires each existing team lineup to have "
                "at least 11 starters."
            )
        goalkeeper_count = sum(
            1
            for lineup in starting_lineups
            if lineup.position == PlayerPosition.GOALKEEPER.value
        )
        if goalkeeper_count != 1:
            raise ConflictError(
                "Protocol generation requires each starting lineup to have exactly "
                "one goalkeeper."
            )

    def _select_generated_starting_lineup(
        self,
        *,
        match: Match,
        team_id: int,
    ) -> list[Player]:
        eligible_players = [
            player
            for player in self._sort_lineup_candidates(self._get_team_players(team_id))
            if self._is_player_available(player=player, match=match)
        ]
        goalkeepers = [
            player
            for player in eligible_players
            if player.position == PlayerPosition.GOALKEEPER
        ]
        field_players = [
            player
            for player in eligible_players
            if player.position != PlayerPosition.GOALKEEPER
        ]
        if not goalkeepers:
            raise ConflictError(
                "Protocol generation requires an eligible goalkeeper for each team."
            )
        if len(field_players) < 10:
            raise ConflictError(
                "Protocol generation requires at least ten eligible field players "
                "for each team."
            )
        return [goalkeepers[0], *field_players[:10]]

    def _get_protocol_players(self, *, match_id: int, team_id: int) -> list[Player]:
        starting_lineups = [
            lineup
            for lineup in self.lineups.list_by_match_and_team(
                match_id=match_id,
                team_id=team_id,
            )
            if lineup.is_starting
        ]
        players_by_id = {
            player.id: player for player in self.players.list_by_team(team_id)
        }
        protocol_players = [
            players_by_id[lineup.player_id]
            for lineup in starting_lineups
            if lineup.player_id in players_by_id
        ]
        if not protocol_players:
            raise ConflictError("Protocol generation requires match lineups.")
        return protocol_players

    def _is_player_available(self, *, player: Player, match: Match) -> bool:
        red_event = self._latest_player_event_before_match(
            player_id=player.id,
            season_id=match.season_id,
            match_datetime=match.match_datetime,
            event_type=MatchEventType.RED_CARD,
        )
        if red_event is not None and self._is_next_team_match(
            player=player,
            event=red_event,
            target_match=match,
        ):
            return False

        yellow_events = self.events.list_player_events_before_match(
            player_id=player.id,
            season_id=match.season_id,
            match_datetime=match.match_datetime,
            event_type=MatchEventType.YELLOW_CARD,
        )
        if len(yellow_events) >= 5:
            threshold_event = yellow_events[(len(yellow_events) // 5) * 5 - 1]
            if self._is_next_team_match(
                player=player,
                event=threshold_event,
                target_match=match,
            ):
                return False
        return True

    def _latest_player_event_before_match(
        self,
        *,
        player_id: int,
        season_id: int,
        match_datetime,
        event_type: MatchEventType,
    ) -> MatchEvent | None:
        events = self.events.list_player_events_before_match(
            player_id=player_id,
            season_id=season_id,
            match_datetime=match_datetime,
            event_type=event_type,
        )
        return events[-1] if events else None

    def _is_next_team_match(
        self,
        *,
        player: Player,
        event: MatchEvent,
        target_match: Match,
    ) -> bool:
        event_match = self._get_match(event.match_id)
        next_match = self.matches.get_next_team_match_after(
            team_id=player.team_id,
            season_id=target_match.season_id,
            after_match_datetime=event_match.match_datetime,
        )
        return next_match is not None and next_match.id == target_match.id

    def _sort_lineup_candidates(self, players: list[Player]) -> list[Player]:
        return sorted(
            players,
            key=lambda player: (
                0 if player.position == PlayerPosition.GOALKEEPER else 1,
                player.number,
                player.id,
            ),
        )

    def _build_generated_result(
        self,
        *,
        match: Match,
        home_players: list[Player],
        away_players: list[Player],
        rng: Random,
    ) -> tuple[int, int, list[MatchEvent]]:
        home_score, away_score = self._generate_score(match=match, rng=rng)
        generated_events = [
            *self._generate_goal_events(
                match=match,
                team_id=match.home_team_id,
                players=home_players,
                goals=home_score,
                rng=rng,
            ),
            *self._generate_goal_events(
                match=match,
                team_id=match.away_team_id,
                players=away_players,
                goals=away_score,
                rng=rng,
            ),
            *self._generate_save_events(
                match=match,
                team_id=match.home_team_id,
                players=home_players,
                opponent_goals=away_score,
                rng=rng,
            ),
            *self._generate_save_events(
                match=match,
                team_id=match.away_team_id,
                players=away_players,
                opponent_goals=home_score,
                rng=rng,
            ),
            *self._generate_card_events(
                match=match,
                team_id=match.home_team_id,
                players=home_players,
                rng=rng,
            ),
            *self._generate_card_events(
                match=match,
                team_id=match.away_team_id,
                players=away_players,
                rng=rng,
            ),
        ]
        return home_score, away_score, generated_events

    def _apply_generated_result(
        self,
        *,
        match: Match,
        home_score: int,
        away_score: int,
        generated_events: list[MatchEvent],
    ) -> None:
        for event in generated_events:
            self.events.add(event)
        match.home_score = home_score
        match.away_score = away_score
        match.status = MatchStatus.FINISHED

    def _generate_score(self, *, match: Match, rng: Random) -> tuple[int, int]:
        home_score = self._weighted_goal_count(rng)
        away_score = self._weighted_goal_count(rng)
        if match.stage in {CupStage.SEMIFINAL, CupStage.FINAL}:
            home_score, away_score = self._break_cup_draw(
                home_score=home_score,
                away_score=away_score,
                rng=rng,
            )
        return home_score, away_score

    def _weighted_goal_count(self, rng: Random) -> int:
        return rng.choices(
            population=list(range(MAX_GOALS_PER_TEAM + 1)),
            weights=[22, 28, 24, 15, 8, 3],
            k=1,
        )[0]

    def _break_cup_draw(
        self,
        *,
        home_score: int,
        away_score: int,
        rng: Random,
    ) -> tuple[int, int]:
        if home_score != away_score:
            return home_score, away_score
        home_wins = rng.choice([True, False])
        if home_wins:
            if home_score < MAX_GOALS_PER_TEAM:
                return home_score + 1, away_score
            return home_score, away_score - 1
        if away_score < MAX_GOALS_PER_TEAM:
            return home_score, away_score + 1
        return home_score - 1, away_score

    def _generate_goal_events(
        self,
        *,
        match: Match,
        team_id: int,
        players: list[Player],
        goals: int,
        rng: Random,
    ) -> list[MatchEvent]:
        events: list[MatchEvent] = []
        for _ in range(goals):
            scorer = rng.choice(players)
            assist_player = self._pick_assist_player(
                players=players,
                scorer_id=scorer.id,
                rng=rng,
            )
            events.append(
                self._build_event(
                    match=match,
                    team_id=team_id,
                    player_id=scorer.id,
                    event_type=MatchEventType.GOAL,
                    rng=rng,
                    assist_player_id=(
                        assist_player.id if assist_player is not None else None
                    ),
                )
            )
        return events

    def _pick_assist_player(
        self,
        *,
        players: list[Player],
        scorer_id: int,
        rng: Random,
    ) -> Player | None:
        candidates = [player for player in players if player.id != scorer_id]
        if not candidates or rng.random() > 0.65:
            return None
        return rng.choice(candidates)

    def _generate_save_events(
        self,
        *,
        match: Match,
        team_id: int,
        players: list[Player],
        opponent_goals: int,
        rng: Random,
    ) -> list[MatchEvent]:
        goalkeeper = self._pick_goalkeeper(players, rng)
        save_count = rng.randint(
            0,
            min(MAX_SAVES_PER_TEAM, opponent_goals + rng.randint(2, 7)),
        )
        return [
            self._build_event(
                match=match,
                team_id=team_id,
                player_id=goalkeeper.id,
                event_type=MatchEventType.SAVE,
                rng=rng,
            )
            for _ in range(save_count)
        ]

    def _pick_goalkeeper(self, players: list[Player], rng: Random) -> Player:
        goalkeepers = [
            player for player in players if player.position == PlayerPosition.GOALKEEPER
        ]
        if goalkeepers:
            return rng.choice(goalkeepers)
        return rng.choice(players)

    def _generate_card_events(
        self,
        *,
        match: Match,
        team_id: int,
        players: list[Player],
        rng: Random,
    ) -> list[MatchEvent]:
        events: list[MatchEvent] = []
        yellow_count = rng.randint(0, MAX_YELLOW_CARDS_PER_TEAM)
        red_count = 1 if rng.random() < 0.12 else 0
        for _ in range(yellow_count):
            events.append(
                self._build_event(
                    match=match,
                    team_id=team_id,
                    player_id=rng.choice(players).id,
                    event_type=MatchEventType.YELLOW_CARD,
                    rng=rng,
                )
            )
        for _ in range(min(red_count, MAX_RED_CARDS_PER_TEAM)):
            events.append(
                self._build_event(
                    match=match,
                    team_id=team_id,
                    player_id=rng.choice(players).id,
                    event_type=MatchEventType.RED_CARD,
                    rng=rng,
                )
            )
        return events

    def _build_event(
        self,
        *,
        match: Match,
        team_id: int,
        player_id: int,
        event_type: MatchEventType,
        rng: Random,
        assist_player_id: int | None = None,
    ) -> MatchEvent:
        return MatchEvent(
            owner_id=self.events.require_owner_id(),
            match_id=match.id,
            team_id=team_id,
            player_id=player_id,
            assist_player_id=assist_player_id,
            event_type=event_type,
            minute=rng.randint(REGULAR_MINUTE_MIN, REGULAR_MINUTE_MAX),
        )
