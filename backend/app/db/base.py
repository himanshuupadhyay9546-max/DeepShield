import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, Uuid

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Stores as native UUID on PostgreSQL, and CHAR(32) on SQLite.
    Accepts both uuid.UUID and str (with or without hyphens).
    """
    impl = Uuid
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                return value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            try:
                return uuid.UUID(str(value))
            except ValueError:
                return value
        return value

