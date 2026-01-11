"""Pytest configuration for backend tests."""
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from datetime import timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.core.security import create_access_token
import os

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Test database URL - use same DB as development for now
# TODO: Create separate test database in future
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://raguser:ragpassword@localhost:5432/rag_platform"
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Async database session fixture for testing.

    Creates a new database session for each test and rolls back
    all changes after the test completes.
    """
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ===== JWT Token Fixtures for Security Testing (Task 4.3b) =====

@pytest.fixture
def test_secret_key():
    """테스트용 JWT 비밀 키"""
    return "test-secret-key-for-testing-only"


@pytest.fixture
def l1_user_token(test_secret_key):
    """
    L1 일반 사용자 토큰

    권한:
    - Access Level: 1
    - Department: Engineering
    """
    token = create_access_token(
        data={
            "sub": "user@example.com",
            "user_id": "user_123",
            "access_level": 1,
            "department": "Engineering"
        },
        secret_key=test_secret_key,
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
def l2_user_token(test_secret_key):
    """
    L2 팀장 토큰

    권한:
    - Access Level: 2
    - Department: Engineering
    """
    token = create_access_token(
        data={
            "sub": "teamlead@example.com",
            "user_id": "teamlead_123",
            "access_level": 2,
            "department": "Engineering"
        },
        secret_key=test_secret_key,
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
def l2_hr_token(test_secret_key):
    """
    L2 HR 팀장 토큰

    권한:
    - Access Level: 2
    - Department: HR
    """
    token = create_access_token(
        data={
            "sub": "hr_teamlead@example.com",
            "user_id": "hr_teamlead_123",
            "access_level": 2,
            "department": "HR"
        },
        secret_key=test_secret_key,
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
def l3_user_token(test_secret_key):
    """
    L3 관리자 토큰

    권한:
    - Access Level: 3
    - Department: Management
    """
    token = create_access_token(
        data={
            "sub": "admin@example.com",
            "user_id": "admin_123",
            "access_level": 3,
            "department": "Management"
        },
        secret_key=test_secret_key,
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
def expired_token(test_secret_key):
    """만료된 토큰"""
    token = create_access_token(
        data={
            "sub": "user@example.com",
            "user_id": "user_123",
            "access_level": 1,
            "department": "Engineering"
        },
        secret_key=test_secret_key,
        expires_delta=timedelta(seconds=-1)  # 이미 만료됨
    )
    return token


@pytest.fixture
def invalid_token():
    """잘못된 토큰"""
    return "invalid.jwt.token"
