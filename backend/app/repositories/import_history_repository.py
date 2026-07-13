import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_history import ImportHistory


class ImportHistoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[ImportHistory]:
        result = await self._session.execute(select(ImportHistory).where(ImportHistory.id == id))
        return result.scalar_one_or_none()

    async def create(self, **fields) -> ImportHistory:
        record = ImportHistory(**fields)
        self._session.add(record)
        await self._session.flush()
        return record

    async def update(self, record: ImportHistory, **fields) -> ImportHistory:
        for key, value in fields.items():
            setattr(record, key, value)
        await self._session.flush()
        return record

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        platform: str | None = None,
        status: str | None = None,
    ) -> tuple[list[ImportHistory], int]:
        query = select(ImportHistory).where(ImportHistory.user_id == user_id)
        count_query = select(func.count(ImportHistory.id)).where(ImportHistory.user_id == user_id)

        if platform:
            query = query.where(ImportHistory.platform == platform)
            count_query = count_query.where(ImportHistory.platform == platform)
        if status:
            query = query.where(ImportHistory.status == status)
            count_query = count_query.where(ImportHistory.status == status)

        query = query.order_by(ImportHistory.started_at.desc())

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count
