"""
Repository for revoked JWT persistence operations.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.revoked_token import RevokedToken


class RevokedTokenRepository:
    """Data access layer for revoked JWT IDs."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def exists(self, jti: str) -> bool:
        """Return whether the given JWT ID has been revoked."""
        result = await self._session.execute(
            select(RevokedToken.id).where(RevokedToken.jti == jti)
        )
        return result.scalar_one_or_none() is not None

    async def revoke(
        self,
        *,
        jti: str,
        user_id: uuid.UUID,
        token_type: str,
        expires_at: datetime,
    ) -> RevokedToken:
        """Persist a revoked token ID if it has not already been stored."""
        existing = await self._session.execute(
            select(RevokedToken).where(RevokedToken.jti == jti)
        )
        token = existing.scalar_one_or_none()
        if token is not None:
            return token

        token = RevokedToken(
            jti=jti,
            user_id=user_id,
            token_type=token_type,
            expires_at=expires_at,
        )
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token
