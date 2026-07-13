"""
Shared pytest fixtures.

Sets required environment variables *before* any application module is
imported (since `Settings` validates them eagerly), then provides an
isolated in-memory SQLite database and an async HTTP client wired up with
dependency overrides for integration tests.
"""

import os

# Environment variables must be set before importing anything from `app`,
# since `app.core.config.Settings` is instantiated (and validates required
# fields) at import time via the lru_cache'd `get_settings()`.
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only-not-for-production-use"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
os.environ["LOG_JSON"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["RATE_LIMIT_AUTH"] = "1000/minute"
os.environ["RATE_LIMIT_DEFAULT"] = "1000/minute"

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.models import (  # noqa: F401 - register metadata
    AIPreference,
    AuditLog,
    Client,
    ImportHistory,
    NotificationPreference,
    Opportunity,
    Project,
    ProjectCategory,
    ProjectCategoryLink,
    ProjectTechnology,
    ProposalNote,
    ProposalStatusHistory,
    ProposalTemplate,
    Technology,
    ProposalVersion,
    AIUsageLog,
    User,
    UserPreference,
)
from app.main import app


@pytest_asyncio.fixture
async def db_engine():
    """A fresh in-memory SQLite engine per test, with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def session_factory(db_engine):
    """Session factory for tests that need direct DB access."""
    return async_sessionmaker(bind=db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(db_engine):
    """An httpx AsyncClient wired to the FastAPI app with the test database."""
    session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
