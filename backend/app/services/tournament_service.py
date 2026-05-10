from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.models.tournament import Tournament
from app.repositories.season import SeasonRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.tournament import TournamentCreate, TournamentUpdate


class TournamentService:
    def __init__(
        self,
        tournaments: TournamentRepository,
        seasons: SeasonRepository,
    ) -> None:
        self.tournaments = tournaments
        self.seasons = seasons

    def list_tournaments(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Tournament]:
        return self.tournaments.list(offset=offset, limit=limit)

    def get_tournament(self, tournament_id: int) -> Tournament:
        tournament = self.tournaments.get(tournament_id)
        if tournament is None:
            raise NotFoundError("Tournament not found.")
        return tournament

    def create_tournament(self, payload: TournamentCreate) -> Tournament:
        self._ensure_season_exists(payload.season_id)
        self._ensure_name_is_available(
            season_id=payload.season_id,
            name=payload.name,
        )

        tournament = Tournament(
            owner_id=self.tournaments.require_owner_id(),
            **payload.model_dump(),
        )
        try:
            self.tournaments.add(tournament)
            self.tournaments.db.commit()
            self.tournaments.db.refresh(tournament)
        except IntegrityError as exc:
            self.tournaments.db.rollback()
            raise ConflictError(
                "A tournament with this name already exists in the season."
            ) from exc
        return tournament

    def update_tournament(
        self,
        tournament_id: int,
        payload: TournamentUpdate,
    ) -> Tournament:
        tournament = self.get_tournament(tournament_id)
        data = payload.model_dump(exclude_unset=True)

        if data.get("season_id") is None and "season_id" in data:
            raise NotFoundError("Season not found.")

        season_id = data.get("season_id", tournament.season_id)
        name = data.get("name", tournament.name)
        if "season_id" in data:
            self._ensure_season_exists(season_id)
        if "season_id" in data or "name" in data:
            self._ensure_name_is_available(
                season_id=season_id,
                name=name,
                current_tournament_id=tournament_id,
            )

        for field, value in data.items():
            setattr(tournament, field, value)

        try:
            self.tournaments.db.commit()
            self.tournaments.db.refresh(tournament)
        except IntegrityError as exc:
            self.tournaments.db.rollback()
            raise ConflictError(
                "A tournament with this name already exists in the season."
            ) from exc
        return tournament

    def delete_tournament(self, tournament_id: int) -> None:
        tournament = self.get_tournament(tournament_id)
        self.tournaments.delete(tournament)
        self.tournaments.db.commit()

    def _ensure_season_exists(self, season_id: int) -> None:
        if self.seasons.get(season_id) is None:
            raise NotFoundError("Season not found.")

    def _ensure_name_is_available(
        self,
        *,
        season_id: int,
        name: str,
        current_tournament_id: int | None = None,
    ) -> None:
        existing = self.tournaments.get_by_season_and_name(
            season_id=season_id,
            name=name,
        )
        if existing is not None and existing.id != current_tournament_id:
            raise ConflictError(
                "A tournament with this name already exists in the season."
            )
