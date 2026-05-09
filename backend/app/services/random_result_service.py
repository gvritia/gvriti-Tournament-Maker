from random import Random

from sqlalchemy.exc import IntegrityError

from app.core.constants import CupStage, MatchEventType, MatchStatus, PlayerPosition
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.player import Player
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.player import PlayerRepository
from app.schemas.random_result import RandomResultGenerate, RandomResultRead

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
    ) -> None:
        self.matches = matches
        self.events = events
        self.players = players

    def generate_for_match(
        self,
        match_id: int,
        payload: RandomResultGenerate,
    ) -> RandomResultRead:
        match = self._get_match(match_id)
        self._ensure_match_can_be_generated(match)
        self._ensure_match_has_no_events(match.id)

        home_players = self._get_team_players(match.home_team_id)
        away_players = self._get_team_players(match.away_team_id)
        rng = Random(payload.seed)
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

        try:
            for event in generated_events:
                self.events.add(event)
            match.home_score = home_score
            match.away_score = away_score
            match.status = MatchStatus.FINISHED
            self.matches.db.commit()
            self.matches.db.refresh(match)
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(
                "Could not generate random match result because of a conflict."
            ) from exc

        return RandomResultRead(
            match=match,
            events=self.events.list_by_match(match.id),
        )

    def _get_match(self, match_id: int) -> Match:
        match = self.matches.get(match_id)
        if match is None:
            raise NotFoundError("Match not found.")
        return match

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
            match_id=match.id,
            team_id=team_id,
            player_id=player_id,
            assist_player_id=assist_player_id,
            event_type=event_type,
            minute=rng.randint(REGULAR_MINUTE_MIN, REGULAR_MINUTE_MAX),
        )
