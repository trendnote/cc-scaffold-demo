"""
Seed script to insert sample data into the database.

This script creates sample users and documents for development and testing.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import async_session_maker
from app.models import Document, User


async def seed_sample_data():
    """Insert sample users and documents into the database."""
    async with async_session_maker() as session:
        try:
            # Sample users
            users = [
                User(
                    email="admin@company.com",
                    name="Admin User",
                    department="Management",
                    access_level=3,
                ),
                User(
                    email="engineer@company.com",
                    name="Engineer User",
                    department="Engineering",
                    access_level=2,
                ),
                User(
                    email="intern@company.com",
                    name="Intern User",
                    department="Engineering",
                    access_level=1,
                ),
            ]
            session.add_all(users)

            # Sample documents
            documents = [
                Document(
                    title="Company Handbook",
                    content="This is the company handbook with general policies and procedures...",
                    document_type="PDF",
                    source="/docs/handbook.pdf",
                    access_level=1,
                    doc_metadata={
                        "page_count": 50,
                        "version": "2024.1",
                        "tags": ["policy", "handbook"],
                    },
                ),
                Document(
                    title="Engineering Best Practices",
                    content="Best practices for software engineering at our company...",
                    document_type="MARKDOWN",
                    source="/docs/engineering-bp.md",
                    access_level=2,
                    department="Engineering",
                    doc_metadata={
                        "tags": ["engineering", "best-practices"],
                        "author": "Engineering Team",
                    },
                ),
                Document(
                    title="Confidential Strategy 2025",
                    content="Company strategy and financial projections for 2025...",
                    document_type="DOCX",
                    source="/docs/strategy-2025.docx",
                    access_level=3,
                    department="Management",
                    doc_metadata={
                        "confidential": True,
                        "tags": ["strategy", "finance"],
                        "year": 2025,
                    },
                ),
            ]
            session.add_all(documents)

            await session.commit()
            print("✅ Sample data inserted successfully!")
            print(f"   - Inserted {len(users)} users")
            print(f"   - Inserted {len(documents)} documents")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error inserting sample data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_sample_data())
