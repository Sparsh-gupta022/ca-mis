"""
Declarative base for all ORM models.

Every model in app/models inherits from `Base`. Table names default to the
snake_case, lower-cased class name unless a model explicitly sets
`__tablename__`.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
