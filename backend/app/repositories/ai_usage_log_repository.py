import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage_log import AIUsageLog


class AIUsageLogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, **fields) -> AIUsageLog:
        log = AIUsageLog(**fields)
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log
