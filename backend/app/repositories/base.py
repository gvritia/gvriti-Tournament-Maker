from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], db: Session) -> None:
        self.model = model
        self.db = db

    def get(self, object_id: int) -> ModelT | None:
        return self.db.get(self.model, object_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        statement = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(statement).all())

    def add(self, db_object: ModelT) -> ModelT:
        self.db.add(db_object)
        self.db.flush()
        self.db.refresh(db_object)
        return db_object

    def delete(self, db_object: ModelT) -> None:
        self.db.delete(db_object)
        self.db.flush()
