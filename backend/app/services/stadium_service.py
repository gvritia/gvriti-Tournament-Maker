from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.models.stadium import Stadium
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.schemas.stadium import StadiumCreate, StadiumUpdate


class StadiumService:
    def __init__(self, stadiums: StadiumRepository, teams: TeamRepository) -> None:
        self.stadiums = stadiums
        self.teams = teams

    def list_stadiums(self, *, offset: int = 0, limit: int = 100) -> list[Stadium]:
        return self.stadiums.list(offset=offset, limit=limit)

    def get_stadium(self, stadium_id: int) -> Stadium:
        stadium = self.stadiums.get(stadium_id)
        if stadium is None:
            raise NotFoundError("Stadium not found.")
        return stadium

    def create_stadium(self, payload: StadiumCreate) -> Stadium:
        if payload.home_team_id is not None:
            self._ensure_team_exists(payload.home_team_id)
        if self.stadiums.get_by_name(payload.name) is not None:
            raise ConflictError("A stadium with this name already exists.")

        stadium = Stadium(
            owner_id=self.stadiums.require_owner_id(),
            **payload.model_dump(),
        )
        try:
            self.stadiums.add(stadium)
            self.stadiums.db.commit()
            self.stadiums.db.refresh(stadium)
        except IntegrityError as exc:
            self.stadiums.db.rollback()
            raise ConflictError(
                "Could not create stadium because of a conflict."
            ) from exc
        return stadium

    def update_stadium(self, stadium_id: int, payload: StadiumUpdate) -> Stadium:
        stadium = self.get_stadium(stadium_id)
        data = payload.model_dump(exclude_unset=True)

        if data.get("home_team_id") is not None:
            self._ensure_team_exists(data["home_team_id"])

        new_name = data.get("name")
        if new_name is not None:
            existing = self.stadiums.get_by_name(new_name)
            if existing is not None and existing.id != stadium_id:
                raise ConflictError("A stadium with this name already exists.")

        for field, value in data.items():
            setattr(stadium, field, value)

        try:
            self.stadiums.db.commit()
            self.stadiums.db.refresh(stadium)
        except IntegrityError as exc:
            self.stadiums.db.rollback()
            raise ConflictError(
                "Could not update stadium because of a conflict."
            ) from exc
        return stadium

    def delete_stadium(self, stadium_id: int) -> None:
        stadium = self.get_stadium(stadium_id)
        self.stadiums.delete(stadium)
        self.stadiums.db.commit()

    def _ensure_team_exists(self, team_id: int) -> None:
        if self.teams.get(team_id) is None:
            raise NotFoundError("Team not found.")
