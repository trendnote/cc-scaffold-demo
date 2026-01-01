"""
Document model for storing document metadata.

This model stores metadata about documents that are indexed
in the RAG system. The actual content chunks and embeddings
are stored in Milvus vector database.
"""

import uuid

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from ..db.base import Base
from .base_model import TimestampMixin


class Document(Base, TimestampMixin):
    """
    Document metadata model.

    Stores metadata about documents indexed in the RAG system.
    The actual document chunks and embeddings are stored in Milvus.

    Attributes:
        id (UUID): Primary key
        title (str): Document title
        content (str): Full document content (for reference)
        document_type (str): File type (PDF, DOCX, TXT, MARKDOWN)
        source (str): Original file path or URL
        access_level (int): Required access level to view this document
        department (str): Department that owns this document (nullable)
        metadata (dict): Additional metadata in JSON format

    Metadata JSON structure:
        {
            "page_count": int,
            "file_size_bytes": int,
            "author": str,
            "created_date": str,
            "tags": List[str],
            "version": str,
            ...
        }
    """

    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the document",
    )
    title = Column(
        String(500),
        nullable=False,
        comment="Document title",
    )
    content = Column(
        Text,
        nullable=False,
        comment="Full document content for reference",
    )
    document_type = Column(
        String(50),
        nullable=False,
        comment="Document type: PDF, DOCX, TXT, MARKDOWN",
    )
    source = Column(
        String(500),
        nullable=False,
        comment="Original file path or URL",
    )
    access_level = Column(
        Integer,
        nullable=False,
        default=1,
        index=True,
        comment="Required access level: 1=Public, 2=Internal, 3=Confidential",
    )
    department = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Department that owns this document (nullable for public docs)",
    )
    doc_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional metadata in JSON format (with GIN index)",
    )

    def __repr__(self) -> str:
        """String representation of the Document."""
        title_preview = self.title[:30] + "..." if len(self.title) > 30 else self.title
        return (
            f"<Document(title='{title_preview}', "
            f"type='{self.document_type}', "
            f"access_level={self.access_level})>"
        )
