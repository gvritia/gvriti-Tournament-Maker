from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.player import Player
from app.repositories.player import PlayerRepository
from app.repositories.team import TeamRepository
from app.schemas.player import PlayerCreate, PlayerUpdate


class PlayerService:
    def __init__(self, players: PlayerRepository, teams: TeamRepository) -> None:
        self.players = players
        self.teams = teams

    def list_players(self, *, offset: int = 0, limit: int = 100) -> list[Player]:
        return self.players.list(offset=offset, limit=limit)

    def get_player(self, player_id: int) -> Player:
        player = self.players.get(player_id)
        if player is None:
            raise NotFoundError("Player not found.")
        return player

    def create_player(self, payload: PlayerCreate) -> Player:
        self._ensure_team_exists(payload.team_id)
        self._ensure_number_is_available(
            team_id=payload.team_id,
            number=payload.number,
        )

        player = Player(**payload.model_dump())
        try:
            self.players.add(player)
            self.players.db.commit()
            self.players.db.refresh(player)
        except IntegrityError as exc:
            self.players.db.rollback()
            raise ConflictError(
                "This team already has a player with this number."
            ) from exc
        return player

    def update_player(self, player_id: int, payload: PlayerUpdate) -> Player:
        player = self.get_player(player_id)
        data = payload.model_dump(exclude_unset=True)

        if data.get("team_id") is None and "team_id" in data:
            raise BusinessRuleError("Player team_id cannot be null.")

        team_id = data.get("team_id", player.team_id)
        number = data.get("number", player.number)
        if "team_id" in data:
            self._ensure_team_exists(team_id)
        if "team_id" in data or "number" in data:
            self._ensure_number_is_available(
                team_id=team_id,
                number=number,
                current_player_id=player_id,
            )

        for field, value in data.items():
            setattr(player, field, value)

        try:
            self.players.db.commit()
            self.players.db.refresh(player)
        except IntegrityError as exc:
            self.players.db.rollback()
            raise ConflictError(
                "This team already has a player with this number."
            ) from exc
        return player

    def delete_player(self, player_id: int) -> None:
        player = self.get_player(player_id)
        self.players.delete(player)
        self.players.db.commit()

    def _ensure_team_exists(self, team_id: int) -> None:
        if self.teams.get(team_id) is None:
            raise NotFoundError("Team not found.")

    def _ensure_number_is_available(
        self,
        *,
        team_id: int,
        number: int,
        current_player_id: int | None = None,
    ) -> None:
        existing = self.players.get_by_team_and_number(team_id=team_id, number=number)
        if existing is not None and existing.id != current_player_id:
            raise ConflictError("This team already has a player with this number.")
