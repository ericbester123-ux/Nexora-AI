import hashlib
import uuid
from datetime import datetime

from app.core.exceptions import NotFoundError
from app.models.opportunity import Opportunity
from app.repositories.opportunity_repository import OpportunityRepository
from app.schemas.opportunity import SearchParams


class OpportunityService:
    def __init__(self, repository: OpportunityRepository):
        self._repo = repository

    async def get_by_id(self, id: uuid.UUID, user_id: uuid.UUID) -> Opportunity:
        opportunity = await self._repo.get_by_id(id)
        if opportunity is None or opportunity.user_id != user_id:
            raise NotFoundError("Opportunity not found.")
        return opportunity

    async def search(
        self,
        user_id: uuid.UUID,
        params: SearchParams,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "posted_at",
        sort_desc: bool = True,
    ) -> tuple[list[Opportunity], int]:
        return await self._repo.get_all(
            user_id=user_id,
            skip=skip,
            limit=limit,
            platform=params.platform,
            status=params.project_status,
            category=params.category,
            keyword=params.keyword,
            technology=params.technology,
            budget_min=params.budget_min,
            budget_max=params.budget_max,
            country=params.country,
            payment_verified=params.payment_verified,
            date_posted=params.date_posted,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        platform: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Opportunity], int]:
        return await self._repo.get_all(
            user_id=user_id,
            skip=skip,
            limit=limit,
            platform=platform,
            status=status,
        )

    async def update(
        self, id: uuid.UUID, user_id: uuid.UUID, **fields
    ) -> Opportunity:
        opportunity = await self.get_by_id(id, user_id)
        return await self._repo.update(opportunity, **fields)

    async def create_opportunity(
        self,
        user_id: uuid.UUID,
        platform: str,
        title: str,
        external_id: str | None = None,
        import_id: uuid.UUID | None = None,
        description: str | None = None,
        url: str | None = None,
        project_type: str | None = None,
        experience_level: str | None = None,
        duration: str | None = None,
        budget_min: float | None = None,
        budget_max: float | None = None,
        budget_type: str | None = None,
        currency: str = "USD",
        skills: list[str] | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        country: str | None = None,
        client_rating: float | None = None,
        client_reviews_count: int | None = None,
        client_payment_verified: bool | None = None,
        client_total_hired: int | None = None,
        is_remote: bool = True,
        is_negotiable: bool = False,
        posted_at: datetime | None = None,
        deadline: datetime | None = None,
    ) -> Opportunity:
        content_hash = self._compute_content_hash(title, description, budget_max, country)

        opportunity = await self._repo.create(
            user_id=user_id,
            import_id=import_id,
            platform=platform,
            external_id=external_id,
            title=title,
            description=description,
            url=url,
            project_type=project_type,
            experience_level=experience_level,
            duration=duration,
            budget_min=budget_min,
            budget_max=budget_max,
            budget_type=budget_type,
            currency=currency,
            skills=skills,
            category=category,
            subcategory=subcategory,
            country=country,
            client_rating=client_rating,
            client_reviews_count=client_reviews_count,
            client_payment_verified=client_payment_verified,
            client_total_hired=client_total_hired,
            is_remote=is_remote,
            is_negotiable=is_negotiable,
            posted_at=posted_at,
            deadline=deadline,
            content_hash=content_hash,
        )
        return opportunity

    async def get_statistics(self, user_id: uuid.UUID) -> dict:
        all_opportunities, _ = await self._repo.get_all(user_id=user_id, skip=0, limit=0)
        opportunities, _ = await self._repo.get_all(user_id=user_id, skip=0, limit=10000)
        by_platform: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_category: dict[str, int] = {}
        total_budget_max = 0.0
        budget_count = 0

        for opp in opportunities:
            by_platform[opp.platform] = by_platform.get(opp.platform, 0) + 1
            by_status[opp.status] = by_status.get(opp.status, 0) + 1
            cat = opp.category or "Uncategorized"
            by_category[cat] = by_category.get(cat, 0) + 1
            if opp.budget_max is not None:
                total_budget_max += opp.budget_max
                budget_count += 1

        return {
            "total_opportunities": len(opportunities),
            "by_platform": by_platform,
            "by_status": by_status,
            "by_category": by_category,
            "average_budget_max": round(total_budget_max / budget_count, 2) if budget_count > 0 else None,
            "total_imports": 0,
            "last_import": None,
        }

    @staticmethod
    def _compute_content_hash(title: str, description: str | None, budget: float | None, country: str | None) -> str:
        raw = f"{title}|{description or ''}|{budget or ''}|{country or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()
