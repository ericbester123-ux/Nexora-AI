"""
Async database engine and session management.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.exceptions import AppException, DatabaseError

logger = logging.getLogger(__name__)

settings = get_settings()

engine_options = {
    "echo": settings.DATABASE_ECHO,
    "pool_pre_ping": True,
}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_options.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        }
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_options)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session for the lifetime of a
    single request, committing on success and rolling back on failure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except AppException:
            # A known business/domain exception (e.g. ConflictError raised by
            # a service). Roll back the transaction but let the original
            # exception propagate unchanged so the error-handling middleware
            # can map it to the correct HTTP status code.
            await session.rollback()
            raise
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Database session rolled back due to a database error.")
            raise DatabaseError("A database error occurred while processing the request.")
        except Exception:
            await session.rollback()
            logger.exception("Database session rolled back due to an unhandled exception.")
            raise
        finally:
            await session.close()
