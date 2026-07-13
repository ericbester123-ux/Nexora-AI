"""
Repository for MarketplaceSyncHistory persistence.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_sync_history import MarketplaceSyncHistory


class MarketplaceSyncHistoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[MarketplaceSyncHistory]:
        result = await self._session.execute(
            select(MarketplaceSyncHistory).where(MarketplaceSyncHistory.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_account_id(
        self, account_id: uuid.UUID, limit: int = 20
    ) -> list[MarketplaceSyncHistory]:
        result = await self._session.execute(
            select(MarketplaceSyncHistory)
            .where(MarketplaceSyncHistory.account_id == account_id)
            .order_by(MarketplaceSyncHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, account_id: uuid.UUID, **fields) -> MarketplaceSyncHistory:
        record = MarketplaceSyncHistory(account_id=account_id, **fields)
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def update(self, record: MarketplaceSyncHistory, **fields) -> MarketplaceSyncHistory:
        for key, value in fields.items():
            setattr(record, key, value)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def get_latest_by_account_id(self, account_id: uuid.UUID) -> Optional[MarketplaceSyncHistory]:
        result = await self._session.execute(
            select(MarketplaceSyncHistory)
            .where(MarketplaceSyncHistory.account_id == account_id)
            .order_by(MarketplaceSyncHistory.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_account_id(self, account_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(MarketplaceSyncHistory.id)).where(
                MarketplaceSyncHistory.account_id == account_id
            )
        )
        return result.scalar() or 0
