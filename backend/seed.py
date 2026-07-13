#!/usr/bin/env python
"""
Seed command for creating development data.

Usage:
    python -m app.seed
    python seed.py

This creates:
- Admin user (admin@nexora.ai / XeroaAI!)
- Sample projects
- Sample proposals
- Sample jobs
- Dashboard statistics data
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
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
from app.seed import seed_development_data


async def main():
    """Run the seed."""
    # Create engine with the same URL as the app
    from app.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        try:
            result = await seed_development_data(session)
            print("Seed completed successfully!")
            print(f"  Admin user created: {result.get('admin_user', False)}")
            print(f"  Sample projects: {result.get('sample_projects', 0)}")
            print(f"  Sample proposals: {result.get('sample_proposals', 0)}")
        except Exception as e:
            print(f"Seed failed: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())