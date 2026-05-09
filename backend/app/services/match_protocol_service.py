from sqlalchemy.exc import IntegrityError

from app.core.constants import MatchStatus, TournamentType
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.player import Player
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.player import PlayerRepository
from app.repositories.team import TeamRepository
from app.schemas.match_event import MatchEventCreate, MatchEventUpdate, MatchFinish
from app.services.standings_service import StandingsService
from app.services.statistics_service import StatisticsService


class MatchProtocolService:
    def __init__(
        self,
        matches: MatchRepository,
        events: MatchEventRepository,
        players: PlayerRepository,
        teams: TeamRepository,
        standings: StandingsService,
        statistics: StatisticsService,
    ) -> None:
        self.matches = matches
        self.events = events
        self.players = players
        self.teams = teams
        self.standings = standings
        self.statistics = statistics

    def list_match_events(self, match_id: int) -> list[MatchEvent]:
        self._get_match(match_id)
        return self.events.list_by_match(match_id)

    def get_event(self, event_id: int) -> MatchEvent:
        event = self.events.get(event_id)
        if event is None:
            raise NotFoundError("Match event not found.")
        return event

    def add_event(self, match_id: int, payload: MatchEventCreate) -> MatchEvent:
        match = self._get_match(match_id)
        self._ensure_protocol_can_be_changed(match)
        self._validate_event_payload(
            match=match,
            team_id=payload.team_id,
            player_id=payload.player_id,
            assist_player_id=payload.assist_player_id,
        )

        event = MatchEvent(match_id=match_id, **payload.model_dump())
        try:
            self.events.add(event)
            self.events.db.commit()
            self.events.db.refresh(event)
        except IntegrityError as exc:
            self.events.db.rollback()
            raise ConflictError(
                "Could not add match event because of a conflict."
            ) from exc
        return event

    def update_event(
        self,
        event_id: int,
        payload: MatchEventUpdate,
    ) -> MatchEvent:
        event = self.get_event(event_id)
        match = self._get_match(event.match_id)
        self._ensure_protocol_can_be_changed(match)
        data = payload.model_dump(exclude_unset=True)

        if "team_id" in data and data["team_id"] is None:
            raise BusinessRuleError("Event team_id cannot be null.")
        if "player_id" in data and data["player_id"] is None:
            raise BusinessRuleError("Event player_id cannot be null.")
        if "event_type" in data and data["event_type"] is None:
            raise BusinessRuleError("Event event_type cannot be null.")
        if "minute" in data and data["minute"] is None:
            raise BusinessRuleError("Event minute cannot be null.")

        team_id = data.get("team_id", event.team_id)
        player_id = data.get("player_id", event.player_id)
        assist_player_id = data.get("assist_player_id", event.assist_player_id)
        self._validate_event_payload(
            match=match,
            team_id=team_id,
            player_id=player_id,
            assist_player_id=assist_player_id,
        )

        for field, value in data.items():
            setattr(event, field, value)

        try:
            self.events.db.commit()
            self.events.db.refresh(event)
        except IntegrityError as exc:
            self.events.db.rollback()
            raise ConflictError(
                "Could not update match event because of a conflict."
            ) from exc
        return event

    def delete_event(self, event_id: int) -> None:
        event = self.get_event(event_id)
        match = self._get_match(event.match_id)
        self._ensure_protocol_can_be_changed(match)
        self.events.delete(event)
        self.events.db.commit()

    def finish_match(self, match_id: int, payload: MatchFinish) -> Match:
        match = self._get_match(match_id)
        if match.status == MatchStatus.CANCELLED:
            raise BusinessRuleError("Cancelled match cannot be finished.")
        if match.status == MatchStatus.FINISHED:
            raise BusinessRuleError("Match is already finished.")

        home_goals = self.events.count_match_goals_for_team(
            match_id=match.id,
            team_id=match.home_team_id,
        )
        away_goals = self.events.count_match_goals_for_team(
            match_id=match.id,
            team_id=match.away_team_id,
        )
        if payload.home_score != home_goals or payload.away_score != away_goals:
            raise BusinessRuleError("Final score must match recorded goal events.")

        match.home_score = payload.home_score
        match.away_score = payload.away_score
        match.status = MatchStatus.FINISHED
        try:
            self._recalculate_finished_match_totals(match)
            self.matches.db.commit()
            self.matches.db.refresh(match)
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(
                "Could not finish match because of a conflict."
            ) from exc
        return match

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

    def _get_player(self, player_id: int) -> Player:
        player = self.players.get(player_id)
        if player is None:
            raise NotFoundError("Player not found.")
        return player

    def _ensure_protocol_can_be_changed(self, match: Match) -> None:
        if match.status in {MatchStatus.FINISHED, MatchStatus.CANCELLED}:
            raise BusinessRuleError(
                "Match protocol cannot be changed after match is finished or cancelled."
            )

    def _validate_event_payload(
        self,
        *,
        match: Match,
        team_id: int,
        player_id: int,
        assist_player_id: int | None,
    ) -> None:
        self._ensure_team_exists(team_id)
        self._ensure_team_participates(match=match, team_id=team_id)
        player = self._get_player(player_id)
        self._ensure_player_belongs_to_team(player=player, team_id=team_id)

        if assist_player_id is not None:
            assist_player = self._get_player(assist_player_id)
            self._ensure_player_belongs_to_team(
                player=assist_player,
                team_id=team_id,
            )

    def _ensure_team_exists(self, team_id: int) -> None:
        if self.teams.get(team_id) is None:
            raise NotFoundError("Team not found.")

    def _ensure_team_participates(self, *, match: Match, team_id: int) -> None:
        if team_id not in {match.home_team_id, match.away_team_id}:
            raise BusinessRuleError("Team is not a participant of this match.")

    def _ensure_player_belongs_to_team(self, *, player: Player, team_id: int) -> None:
        if player.team_id != team_id:
            raise BusinessRuleError("Player does not belong to this team.")
