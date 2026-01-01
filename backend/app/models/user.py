"""
User model for authentication and authorization.

This model stores user information including access levels
and department assignments for document access control.
"""

import uuid

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db.base import Base
from .base_model import TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for the RAG platform.

    Attributes:
        id (UUID): Primary key
        email (str): Unique email address (indexed)
        name (str): Full name of the user
        department (str): Department name for access control (indexed)
        access_level (int): Access level (1=L1/Public, 2=L2/Internal, 3=L3/Confidential)
        is_active (bool): Whether the user account is active

    Relationships:
        search_queries: All search queries made by this user
        feedbacks: All feedback provided by this user
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the user",
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address (unique, indexed)",
    )
    name = Column(
        String(100),
        nullable=False,
        comment="User's full name",
    )
    department = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Department for access control",
    )
    access_level = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Access level: 1=Public, 2=Internal, 3=Confidential",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active",
    )

    # Relationships
    search_queries = relationship(
        "SearchQuery",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    feedbacks = relationship(
        "UserFeedback",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        """String representation of the User."""
        return f"<User(email='{self.email}', department='{self.department}', access_level={self.access_level})>"
