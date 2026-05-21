from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.models.referee import Referee
from app.repositories.referee import RefereeRepository
from app.schemas.referee import RefereeCreate, RefereeUpdate


class RefereeService:
    def __init__(self, referees: RefereeRepository) -> None:
        self.referees = referees

    def list_referees(self, *, offset: int = 0, limit: int = 100) -> list[Referee]:
        return self.referees.list(offset=offset, limit=limit)

    def get_referee(self, referee_id: int) -> Referee:
        referee = self.referees.get(referee_id)
        if referee is None:
            raise NotFoundError("Referee not found.")
        return referee

    def create_referee(self, payload: RefereeCreate) -> Referee:
        full_name = payload.full_name.strip()
        if self.referees.get_by_full_name(full_name) is not None:
            raise ConflictError("A referee with this full name already exists.")

        referee = Referee(
            owner_id=self.referees.require_owner_id(),
            full_name=full_name,
        )
        try:
            self.referees.add(referee)
            self.referees.db.commit()
            self.referees.db.refresh(referee)
        except IntegrityError as exc:
            self.referees.db.rollback()
            raise ConflictError(
                "Could not create referee because of a conflict."
            ) from exc
        return referee

    def update_referee(self, referee_id: int, payload: RefereeUpdate) -> Referee:
        referee = self.get_referee(referee_id)
        data = payload.model_dump(exclude_unset=True)

        full_name = data.get("full_name")
        if full_name is not None:
            full_name = full_name.strip()
            existing = self.referees.get_by_full_name(full_name)
            if existing is not None and existing.id != referee_id:
                raise ConflictError("A referee with this full name already exists.")
            data["full_name"] = full_name

        for field, value in data.items():
            setattr(referee, field, value)

        try:
            self.referees.db.commit()
            self.referees.db.refresh(referee)
        except IntegrityError as exc:
            self.referees.db.rollback()
            raise ConflictError(
                "Could not update referee because of a conflict."
            ) from exc
        return referee

    def delete_referee(self, referee_id: int) -> None:
        referee = self.get_referee(referee_id)
        self.referees.delete(referee)
        self.referees.db.commit()
