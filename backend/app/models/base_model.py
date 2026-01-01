"""
Base model mixins for common database patterns.

This module provides reusable mixins that can be inherited
by SQLAlchemy models to provide common functionality.
"""

from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.

    The created_at column is set when a row is first inserted.
    The updated_at column is automatically updated on every UPDATE.

    Example:
        class User(Base, TimestampMixin):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String(100))
    """

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated",
    )
