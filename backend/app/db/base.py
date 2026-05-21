from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def enum_column(enum_cls: type[Enum]) -> SAEnum:
    return SAEnum(
        enum_cls,
        values_callable=lambda values: [item.value for item in values],
        native_enum=False,
    )
