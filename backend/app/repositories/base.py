from typing import Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(
        self,
        model: type[ModelT],
        db: Session,
        owner_id: int | None = None,
    ) -> None:
        self.model = model
        self.db = db
        self.owner_id = owner_id

    def get(self, object_id: int) -> ModelT | None:
        if self.owner_id is not None and self._has_owner_id():
            return self.db.scalar(
                select(self.model).where(
                    self.model.id == object_id,
                    self.model.owner_id == self.owner_id,
                )
            )
        return self.db.get(self.model, object_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        statement = select(self.model).offset(offset).limit(limit)
        statement = self._filter_owner(statement)
        return list(self.db.scalars(statement).all())

    def add(self, db_object: ModelT) -> ModelT:
        self.db.add(db_object)
        self.db.flush()
        self.db.refresh(db_object)
        return db_object

    def delete(self, db_object: ModelT) -> None:
        self.db.delete(db_object)
        self.db.flush()

    def require_owner_id(self) -> int:
        if self.owner_id is None:
            raise RuntimeError("Repository owner_id is required.")
        return self.owner_id

    def _has_owner_id(self) -> bool:
        return hasattr(self.model, "owner_id")

    def _filter_owner(self, statement: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        if self.owner_id is not None and self._has_owner_id():
            return statement.where(self.model.owner_id == self.owner_id)
        return statement
