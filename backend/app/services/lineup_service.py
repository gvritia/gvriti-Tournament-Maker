from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.core.constants import MatchEventType
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_lineup import MatchLineup
from app.models.player import Player
from app.repositories.match import MatchRepository
from app.repositories.match_event import MatchEventRepository
from app.repositories.match_lineup import MatchLineupRepository
from app.repositories.player import PlayerRepository
from app.repositories.team import TeamRepository
from app.schemas.match_lineup import MatchLineupCreate, MatchLineupUpdate


class LineupService:
    def __init__(
        self,
        lineups: MatchLineupRepository,
        matches: MatchRepository,
        players: PlayerRepository,
        teams: TeamRepository,
        events: MatchEventRepository,
    ) -> None:
        self.lineups = lineups
        self.matches = matches
        self.players = players
        self.teams = teams
        self.events = events

    def list_match_lineups(self, match_id: int) -> list[MatchLineup]:
        self._get_match(match_id)
        return self.lineups.list_by_match(match_id)

    def get_lineup(self, lineup_id: int) -> MatchLineup:
        lineup = self.lineups.get(lineup_id)
        if lineup is None:
            raise NotFoundError("Match lineup not found.")
        return lineup

    def add_player_to_lineup(
        self,
        match_id: int,
        payload: MatchLineupCreate,
    ) -> MatchLineup:
        match = self._get_match(match_id)
        self._ensure_team_exists(payload.team_id)
        self._ensure_team_participates(match=match, team_id=payload.team_id)
        player = self._get_player(payload.player_id)
        self._ensure_player_belongs_to_team(player=player, team_id=payload.team_id)
        self._ensure_player_is_available(player=player, match=match)
        self._ensure_player_not_already_added(
            match_id=match_id,
            player_id=payload.player_id,
        )
        self._ensure_number_is_available(
            match_id=match_id,
            team_id=payload.team_id,
            number=payload.number,
        )

        lineup = MatchLineup(match_id=match_id, **payload.model_dump())
        try:
            self.lineups.add(lineup)
            self.lineups.db.commit()
            self.lineups.db.refresh(lineup)
        except IntegrityError as exc:
            self.lineups.db.rollback()
            raise ConflictError(
                "Could not add player to match lineup because of a conflict."
            ) from exc
        return lineup

    def update_lineup(
        self,
        lineup_id: int,
        payload: MatchLineupUpdate,
    ) -> MatchLineup:
        lineup = self.get_lineup(lineup_id)
        data = payload.model_dump(exclude_unset=True)
        if "number" in data and data["number"] is None:
            raise BusinessRuleError("Lineup number cannot be null.")
        if "position" in data and data["position"] is None:
            raise BusinessRuleError("Lineup position cannot be null.")

        number = data.get("number")
        if number is not None:
            self._ensure_number_is_available(
                match_id=lineup.match_id,
                team_id=lineup.team_id,
                number=number,
                current_lineup_id=lineup.id,
            )

        for field, value in data.items():
            setattr(lineup, field, value)

        try:
            self.lineups.db.commit()
            self.lineups.db.refresh(lineup)
        except IntegrityError as exc:
            self.lineups.db.rollback()
            raise ConflictError(
                "Could not update match lineup because of a conflict."
            ) from exc
        return lineup

    def delete_lineup(self, lineup_id: int) -> None:
        lineup = self.get_lineup(lineup_id)
        self.lineups.delete(lineup)
        self.lineups.db.commit()

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

    def _ensure_team_exists(self, team_id: int) -> None:
        if self.teams.get(team_id) is None:
            raise NotFoundError("Team not found.")

    def _ensure_team_participates(self, *, match: Match, team_id: int) -> None:
        if team_id not in {match.home_team_id, match.away_team_id}:
            raise BusinessRuleError("Team is not a participant of this match.")

    def _ensure_player_belongs_to_team(self, *, player: Player, team_id: int) -> None:
        if player.team_id != team_id:
            raise BusinessRuleError("Player does not belong to this team.")

    def _ensure_player_not_already_added(
        self,
        *,
        match_id: int,
        player_id: int,
    ) -> None:
        if (
            self.lineups.get_by_match_and_player(
                match_id=match_id,
                player_id=player_id,
            )
            is not None
        ):
            raise ConflictError("Player is already in this match lineup.")

    def _ensure_number_is_available(
        self,
        *,
        match_id: int,
        team_id: int,
        number: int,
        current_lineup_id: int | None = None,
    ) -> None:
        existing = self.lineups.get_by_match_team_and_number(
            match_id=match_id,
            team_id=team_id,
            number=number,
            exclude_lineup_id=current_lineup_id,
        )
        if existing is not None:
            raise ConflictError("This team already has this number in the lineup.")

    def _ensure_player_is_available(self, *, player: Player, match: Match) -> None:
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
            raise ConflictError("Player is suspended for this match.")

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
                raise ConflictError("Player is suspended for this match.")

    def _latest_player_event_before_match(
        self,
        *,
        player_id: int,
        season_id: int,
        match_datetime: datetime,
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
