from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.core.constants import MatchEventType, PlayerPosition
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
from app.schemas.match_lineup import (
    MatchLineupCreate,
    MatchLineupGenerate,
    MatchLineupUpdate,
)

POSITION_ORDER = {
    "goalkeeper": 0,
    "defender": 1,
    "midfielder": 2,
    "forward": 3,
}


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

        lineup = MatchLineup(
            owner_id=self.lineups.require_owner_id(),
            match_id=match_id,
            **payload.model_dump(),
        )
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

    def generate_lineup(
        self,
        match_id: int,
        payload: MatchLineupGenerate,
    ) -> list[MatchLineup]:
        match = self._get_match(match_id)
        self._ensure_team_exists(payload.team_id)
        self._ensure_team_participates(match=match, team_id=payload.team_id)
        self._ensure_preferred_player_ids_are_unique(payload.preferred_player_ids)

        existing_lineups = self.lineups.list_by_match_and_team(
            match_id=match_id,
            team_id=payload.team_id,
        )
        if existing_lineups and not payload.replace_existing:
            raise ConflictError("This team already has a lineup for this match.")

        team_players = self.players.list_by_team(payload.team_id)
        if not team_players:
            raise BusinessRuleError("Team has no players for lineup generation.")

        selected_players = self._select_players_for_generated_lineup(
            match=match,
            team_id=payload.team_id,
            team_players=team_players,
            preferred_player_ids=payload.preferred_player_ids,
            lineup_size=payload.lineup_size,
        )
        if len(selected_players) < payload.lineup_size:
            raise ConflictError("Not enough eligible players for lineup generation.")

        starting_size = (
            payload.starting_size
            if payload.starting_size is not None
            else min(11, payload.lineup_size)
        )
        selected_players = self._apply_starting_goalkeeper_rule(
            match=match,
            team_players=team_players,
            selected_players=selected_players,
            lineup_size=payload.lineup_size,
            starting_size=starting_size,
        )

        generated_lineups: list[MatchLineup] = []
        try:
            if payload.replace_existing:
                for lineup in existing_lineups:
                    self.lineups.delete(lineup)
            for index, player in enumerate(selected_players):
                lineup = MatchLineup(
                    owner_id=self.lineups.require_owner_id(),
                    match_id=match_id,
                    team_id=payload.team_id,
                    player_id=player.id,
                    is_starting=index < starting_size,
                    position=player.position.value,
                    number=player.number,
                )
                self.lineups.add(lineup)
                generated_lineups.append(lineup)
            self.lineups.db.commit()
            for lineup in generated_lineups:
                self.lineups.db.refresh(lineup)
        except IntegrityError as exc:
            self.lineups.db.rollback()
            raise ConflictError(
                "Could not generate lineup because of a conflict."
            ) from exc
        return generated_lineups

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
        if not self._is_player_available(player=player, match=match):
            raise ConflictError("Player is suspended for this match.")

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

    def _ensure_preferred_player_ids_are_unique(
        self,
        preferred_player_ids: list[int],
    ) -> None:
        if len(set(preferred_player_ids)) != len(preferred_player_ids):
            raise BusinessRuleError("Preferred player ids must be unique.")

    def _select_players_for_generated_lineup(
        self,
        *,
        match: Match,
        team_id: int,
        team_players: list[Player],
        preferred_player_ids: list[int],
        lineup_size: int,
    ) -> list[Player]:
        selected_players: list[Player] = []
        selected_player_ids: set[int] = set()

        for player_id in preferred_player_ids:
            player = self._get_player(player_id)
            self._ensure_player_belongs_to_team(player=player, team_id=team_id)
            if self._is_player_available(player=player, match=match):
                selected_players.append(player)
                selected_player_ids.add(player.id)

        for player in self._sort_lineup_candidates(team_players):
            if len(selected_players) >= lineup_size:
                break
            if player.id in selected_player_ids:
                continue
            if not self._is_player_available(player=player, match=match):
                continue
            selected_players.append(player)
            selected_player_ids.add(player.id)
        return selected_players[:lineup_size]

    def _apply_starting_goalkeeper_rule(
        self,
        *,
        match: Match,
        team_players: list[Player],
        selected_players: list[Player],
        lineup_size: int,
        starting_size: int,
    ) -> list[Player]:
        if starting_size <= 0:
            return selected_players

        starting_players = selected_players[:starting_size]
        starting_goalkeepers = [
            player for player in starting_players if self._is_goalkeeper(player)
        ]
        if len(starting_goalkeepers) == 1:
            return selected_players

        eligible_players = [
            player
            for player in self._sort_lineup_candidates(team_players)
            if self._is_player_available(player=player, match=match)
        ]
        eligible_goalkeepers = [
            player for player in eligible_players if self._is_goalkeeper(player)
        ]
        if not eligible_goalkeepers:
            return selected_players

        selected_goalkeepers = [
            player for player in selected_players if self._is_goalkeeper(player)
        ]
        goalkeeper = (
            selected_goalkeepers[0] if selected_goalkeepers else eligible_goalkeepers[0]
        )
        selected_player_ids = {player.id for player in selected_players}
        used_player_ids = {goalkeeper.id}

        field_candidates = [
            player
            for player in selected_players
            if player.id not in used_player_ids and not self._is_goalkeeper(player)
        ]
        field_candidates.extend(
            player
            for player in eligible_players
            if player.id not in selected_player_ids
            and player.id not in used_player_ids
            and not self._is_goalkeeper(player)
        )

        required_field_starters = starting_size - 1
        if len(field_candidates) < required_field_starters:
            raise ConflictError(
                "Could not generate a valid starting lineup with exactly one "
                "goalkeeper."
            )

        ordered_players = [
            goalkeeper,
            *field_candidates[:required_field_starters],
        ]
        used_player_ids.update(player.id for player in ordered_players)

        bench_slots = lineup_size - len(ordered_players)
        bench_candidates = [
            player for player in selected_players if player.id not in used_player_ids
        ]
        bench_candidates.extend(
            player
            for player in eligible_players
            if player.id not in selected_player_ids and player.id not in used_player_ids
        )
        ordered_players.extend(bench_candidates[:bench_slots])

        if len(ordered_players) < lineup_size:
            raise ConflictError("Not enough eligible players for lineup generation.")
        return ordered_players

    def _is_goalkeeper(self, player: Player) -> bool:
        return player.position == PlayerPosition.GOALKEEPER

    def _sort_lineup_candidates(self, players: list[Player]) -> list[Player]:
        return sorted(
            players,
            key=lambda player: (
                POSITION_ORDER.get(player.position.value, len(POSITION_ORDER)),
                player.number,
                player.id,
            ),
        )

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
