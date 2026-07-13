"""
Repository for MarketplaceAccount persistence.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.marketplace_account import MarketplaceAccount


class MarketplaceAccountRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[MarketplaceAccount]:
        result = await self._session.execute(
            select(MarketplaceAccount)
            .where(MarketplaceAccount.id == id)
            .options(selectinload(MarketplaceAccount.tokens), selectinload(MarketplaceAccount.sync_history))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[MarketplaceAccount]:
        result = await self._session.execute(
            select(MarketplaceAccount)
            .where(MarketplaceAccount.user_id == user_id, MarketplaceAccount.is_active == True)
            .options(selectinload(MarketplaceAccount.tokens))
            .order_by(MarketplaceAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_provider(
        self, user_id: uuid.UUID, provider: str
    ) -> Optional[MarketplaceAccount]:
        result = await self._session.execute(
            select(MarketplaceAccount)
            .where(
                MarketplaceAccount.user_id == user_id,
                MarketplaceAccount.provider == provider,
                MarketplaceAccount.is_active == True,
            )
            .options(selectinload(MarketplaceAccount.tokens))
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(
        self, provider: str, external_user_id: str
    ) -> Optional[MarketplaceAccount]:
        result = await self._session.execute(
            select(MarketplaceAccount)
            .where(
                MarketplaceAccount.provider == provider,
                MarketplaceAccount.external_user_id == external_user_id,
                MarketplaceAccount.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, **fields) -> MarketplaceAccount:
        account = MarketplaceAccount(user_id=user_id, **fields)
        self._session.add(account)
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def update(self, account: MarketplaceAccount, **fields) -> MarketplaceAccount:
        for key, value in fields.items():
            setattr(account, key, value)
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def delete(self, account: MarketplaceAccount) -> None:
        account.is_active = False
        account.disconnected_at = func.now()
        await self._session.flush()

    async def hard_delete(self, account: MarketplaceAccount) -> None:
        await self._session.delete(account)
        await self._session.flush()

    async def count_by_user_id(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(MarketplaceAccount.id)).where(
                MarketplaceAccount.user_id == user_id,
                MarketplaceAccount.is_active == True,
            )
        )
        return result.scalar() or 0
