import uuid
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity


class OpportunityRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[Opportunity]:
        result = await self._session.execute(select(Opportunity).where(Opportunity.id == id))
        return result.scalar_one_or_none()

    async def get_by_platform_external(self, platform: str, external_id: str) -> Optional[Opportunity]:
        result = await self._session.execute(
            select(Opportunity).where(Opportunity.platform == platform, Opportunity.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_by_content_hash(self, content_hash: str, user_id: uuid.UUID) -> Optional[Opportunity]:
        result = await self._session.execute(
            select(Opportunity).where(Opportunity.content_hash == content_hash, Opportunity.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **fields) -> Opportunity:
        opportunity = Opportunity(**fields)
        self._session.add(opportunity)
        await self._session.flush()
        return opportunity

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        platform: str | None = None,
        status: str | None = None,
        category: str | None = None,
        keyword: str | None = None,
        technology: str | None = None,
        budget_min: float | None = None,
        budget_max: float | None = None,
        country: str | None = None,
        payment_verified: bool | None = None,
        date_posted: str | None = None,
        sort_by: str = "posted_at",
        sort_desc: bool = True,
    ) -> tuple[list[Opportunity], int]:
        query = select(Opportunity).where(Opportunity.user_id == user_id)
        count_query = select(func.count(Opportunity.id)).where(Opportunity.user_id == user_id)

        if platform:
            query = query.where(Opportunity.platform == platform)
            count_query = count_query.where(Opportunity.platform == platform)
        if status:
            query = query.where(Opportunity.status == status)
            count_query = count_query.where(Opportunity.status == status)
        if category:
            query = query.where(Opportunity.category == category)
            count_query = count_query.where(Opportunity.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(
                or_(Opportunity.title.ilike(pattern), Opportunity.description.ilike(pattern))
            )
            count_query = count_query.where(
                or_(Opportunity.title.ilike(pattern), Opportunity.description.ilike(pattern))
            )
        if technology and technology.strip():
            query = query.where(Opportunity.skills.any(technology))
            count_query = count_query.where(Opportunity.skills.any(technology))
        if budget_min is not None:
            query = query.where(Opportunity.budget_max >= budget_min)
            count_query = count_query.where(Opportunity.budget_max >= budget_min)
        if budget_max is not None:
            query = query.where(Opportunity.budget_min <= budget_max)
            count_query = count_query.where(Opportunity.budget_min <= budget_max)
        if country:
            query = query.where(Opportunity.country == country)
            count_query = count_query.where(Opportunity.country == country)
        if payment_verified is not None:
            query = query.where(Opportunity.client_payment_verified == payment_verified)
            count_query = count_query.where(Opportunity.client_payment_verified == payment_verified)

        sort_column = getattr(Opportunity, sort_by, Opportunity.posted_at)
        query = query.order_by(sort_column.desc() if sort_desc else sort_column.asc())

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, opportunity: Opportunity, **fields) -> Opportunity:
        for key, value in fields.items():
            setattr(opportunity, key, value)
        await self._session.flush()
        return opportunity

    async def delete(self, opportunity: Opportunity) -> None:
        await self._session.delete(opportunity)
        await self._session.flush()
