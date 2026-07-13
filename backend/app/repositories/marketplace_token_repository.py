"""
Repository for MarketplaceToken persistence.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_token import MarketplaceToken


class MarketplaceTokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_account_id(
        self, account_id: uuid.UUID, token_type: str | None = None
    ) -> list[MarketplaceToken]:
        query = select(MarketplaceToken).where(
            MarketplaceToken.account_id == account_id,
            MarketplaceToken.is_active == True,
        )
        if token_type:
            query = query.where(MarketplaceToken.token_type == token_type)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_active_access_token(
        self, account_id: uuid.UUID
    ) -> Optional[MarketplaceToken]:
        result = await self._session.execute(
            select(MarketplaceToken).where(
                MarketplaceToken.account_id == account_id,
                MarketplaceToken.token_type == "access",
                MarketplaceToken.is_active == True,
            ).order_by(MarketplaceToken.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def create(
        self, account_id: uuid.UUID, token_type: str, encrypted_token: str, expires_at=None
    ) -> MarketplaceToken:
        token = MarketplaceToken(
            account_id=account_id,
            token_type=token_type,
            encrypted_token=encrypted_token,
            expires_at=expires_at,
        )
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token

    async def deactivate_all(self, account_id: uuid.UUID) -> None:
        tokens = await self.get_by_account_id(account_id)
        for token in tokens:
            token.is_active = False
        await self._session.flush()

    async def deactivate_expired(self, account_id: uuid.UUID) -> None:
        from datetime import datetime, timezone
        result = await self._session.execute(
            select(MarketplaceToken).where(
                MarketplaceToken.account_id == account_id,
                MarketplaceToken.is_active == True,
                MarketplaceToken.expires_at.isnot(None),
                MarketplaceToken.expires_at < datetime.now(timezone.utc),
            )
        )
        for token in result.scalars().all():
            token.is_active = False
        await self._session.flush()
