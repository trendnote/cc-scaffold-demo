"""
User feedback model for search result quality tracking.

This model stores user ratings and comments about search
responses to improve the RAG system over time.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base import Base


class UserFeedback(Base):
    """
    User feedback model for search responses.

    Stores user ratings (1-5 stars) and optional comments
    about search result quality.

    Attributes:
        id (UUID): Primary key
        query_id (UUID): Foreign key to search_queries table
        user_id (UUID): Foreign key to users table
        rating (int): User rating from 1 to 5
        comment (str): Optional text comment
        timestamp (datetime): When the feedback was submitted

    Relationships:
        query: The search query this feedback is for
        user: The user who provided this feedback
    """

    __tablename__ = "user_feedback"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the feedback",
    )
    query_id = Column(
        UUID(as_uuid=True),
        ForeignKey("search_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The query this feedback is for",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The user who provided this feedback",
    )
    rating = Column(
        Integer,
        nullable=False,
        comment="User rating from 1 to 5",
    )
    comment = Column(
        Text,
        nullable=True,
        comment="Optional text comment from user",
    )
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the feedback was submitted",
    )

    # Relationships
    query = relationship("SearchQuery", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")

    def __repr__(self) -> str:
        """String representation of the UserFeedback."""
        return f"<UserFeedback(query_id='{self.query_id}', rating={self.rating})>"
