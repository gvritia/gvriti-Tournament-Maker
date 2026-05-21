from sqlalchemy.exc import IntegrityError

from app.core.constants import TournamentStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.season import Season
from app.models.tournament import Tournament
from app.repositories.season import SeasonRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.season import SeasonRolloverCreate


class SeasonRolloverResult:
    def __init__(self, season: Season, tournaments: list[Tournament]) -> None:
        self.season = season
        self.tournaments = tournaments


class SeasonRolloverService:
    def __init__(
        self,
        seasons: SeasonRepository,
        tournaments: TournamentRepository,
    ) -> None:
        self.seasons = seasons
        self.tournaments = tournaments

    def create_next_season(
        self,
        source_season_id: int,
        payload: SeasonRolloverCreate,
    ) -> SeasonRolloverResult:
        source_season = self.seasons.get(source_season_id)
        if source_season is None:
            raise NotFoundError("Season not found.")

        if self.seasons.get_by_name(payload.name) is not None:
            raise ConflictError("A season with this name already exists.")

        next_season = Season(
            owner_id=self.seasons.require_owner_id(),
            name=payload.name,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status,
        )

        copied_tournaments: list[Tournament] = []
        try:
            self.seasons.add(next_season)

            if payload.copy_tournaments:
                for tournament in self.tournaments.list_by_season(source_season.id):
                    copied_tournament = Tournament(
                        owner_id=self.tournaments.require_owner_id(),
                        season_id=next_season.id,
                        name=tournament.name,
                        type=tournament.type,
                        status=TournamentStatus.PLANNED,
                    )
                    self.tournaments.add(copied_tournament)
                    copied_tournaments.append(copied_tournament)

            self.seasons.db.commit()
            self.seasons.db.refresh(next_season)
            for tournament in copied_tournaments:
                self.tournaments.db.refresh(tournament)
        except IntegrityError as exc:
            self.seasons.db.rollback()
            raise ConflictError("A season with this name already exists.") from exc

        return SeasonRolloverResult(
            season=next_season,
            tournaments=copied_tournaments,
        )
