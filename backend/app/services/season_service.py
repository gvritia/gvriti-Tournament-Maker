from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.season import Season
from app.repositories.season import SeasonRepository
from app.schemas.season import SeasonCreate, SeasonUpdate


class SeasonService:
    def __init__(self, seasons: SeasonRepository) -> None:
        self.seasons = seasons

    def list_seasons(self, *, offset: int = 0, limit: int = 100) -> list[Season]:
        return self.seasons.list(offset=offset, limit=limit)

    def get_season(self, season_id: int) -> Season:
        season = self.seasons.get(season_id)
        if season is None:
            raise NotFoundError("Season not found.")
        return season

    def create_season(self, payload: SeasonCreate) -> Season:
        if self.seasons.get_by_name(payload.name) is not None:
            raise ConflictError("A season with this name already exists.")

        season = Season(**payload.model_dump())
        try:
            self.seasons.add(season)
            self.seasons.db.commit()
            self.seasons.db.refresh(season)
        except IntegrityError as exc:
            self.seasons.db.rollback()
            raise ConflictError("A season with this name already exists.") from exc
        return season

    def update_season(self, season_id: int, payload: SeasonUpdate) -> Season:
        season = self.get_season(season_id)
        data = payload.model_dump(exclude_unset=True)

        new_name = data.get("name")
        if new_name is not None:
            existing = self.seasons.get_by_name(new_name)
            if existing is not None and existing.id != season_id:
                raise ConflictError("A season with this name already exists.")

        start_date = data.get("start_date", season.start_date)
        end_date = data.get("end_date", season.end_date)
        if end_date < start_date:
            raise BusinessRuleError(
                "Season end_date must be greater than or equal to start_date."
            )

        for field, value in data.items():
            setattr(season, field, value)

        try:
            self.seasons.db.commit()
            self.seasons.db.refresh(season)
        except IntegrityError as exc:
            self.seasons.db.rollback()
            raise ConflictError("A season with this name already exists.") from exc
        return season

    def delete_season(self, season_id: int) -> None:
        season = self.get_season(season_id)
        self.seasons.delete(season)
        self.seasons.db.commit()
