import uuid
from datetime import datetime, timezone

import pytest
from app.core.exceptions import NotFoundError
from app.models.opportunity import Opportunity
from app.schemas.opportunity import SearchParams
from app.services.opportunity_service import OpportunityService


class FakeOpportunityRepository:
    def __init__(self):
        self._opportunities: dict[uuid.UUID, Opportunity] = {}

    async def get_by_id(self, id):
        return self._opportunities.get(id)

    async def get_by_platform_external(self, platform, external_id):
        for o in self._opportunities.values():
            if o.platform == platform and o.external_id == external_id:
                return o
        return None

    async def get_by_content_hash(self, content_hash, user_id):
        for o in self._opportunities.values():
            if o.content_hash == content_hash and o.user_id == user_id:
                return o
        return None

    async def create(self, **fields):
        fields.setdefault("status", "new")
        fields.setdefault("is_remote", True)
        fields.setdefault("is_negotiable", False)
        fields.setdefault("is_ai_scored", False)
        fields.setdefault("currency", "USD")
        opp = Opportunity(id=uuid.uuid4(), **fields)
        self._opportunities[opp.id] = opp
        return opp

    async def get_all(self, user_id, skip=0, limit=20, platform=None, status=None, category=None, keyword=None, technology=None, budget_min=None, budget_max=None, country=None, payment_verified=None, date_posted=None, sort_by="posted_at", sort_desc=True):
        items = [o for o in self._opportunities.values() if o.user_id == user_id]
        if platform:
            items = [o for o in items if o.platform == platform]
        if status:
            items = [o for o in items if o.status == status]
        if category:
            items = [o for o in items if o.category == category]
        if keyword:
            items = [o for o in items if keyword.lower() in (o.title or "").lower() or keyword.lower() in (o.description or "").lower()]
        if technology:
            items = [o for o in items if o.skills and technology in o.skills]
        if budget_min is not None:
            items = [o for o in items if (o.budget_max or 0) >= budget_min]
        if budget_max is not None:
            items = [o for o in items if (o.budget_min or 0) <= budget_max]
        if country:
            items = [o for o in items if o.country == country]
        if payment_verified is not None:
            items = [o for o in items if o.client_payment_verified == payment_verified]
        sort_key = lambda o: (o.posted_at or o.created_at or o.id)
        return sorted(items, key=sort_key, reverse=True)[skip:skip + limit], len(items)

    async def update(self, opportunity, **fields):
        for k, v in fields.items():
            setattr(opportunity, k, v)
        return opportunity

    async def delete(self, opportunity):
        self._opportunities.pop(opportunity.id, None)


@pytest.fixture
def service() -> OpportunityService:
    return OpportunityService(repository=FakeOpportunityRepository())


@pytest.fixture
async def existing_opportunity(service: OpportunityService) -> Opportunity:
    return await service.create_opportunity(
        user_id=uuid.uuid4(),
        platform="freelancer",
        external_id="fl-001",
        title="Test Opportunity",
        description="A test opportunity",
        budget_max=5000.0,
        country="US",
    )


class TestCreate:
    async def test_create_returns_opportunity(self, service: OpportunityService):
        user_id = uuid.uuid4()
        result = await service.create_opportunity(
            user_id=user_id,
            platform="freelancer",
            external_id="fl-001",
            title="Python Developer",
            budget_max=5000.0,
            skills=["Python", "Django"],
        )
        assert result.title == "Python Developer"
        assert result.platform == "freelancer"
        assert result.external_id == "fl-001"
        assert result.user_id == user_id
        assert result.skills == ["Python", "Django"]
        assert result.status == "new"
        assert result.content_hash is not None

    async def test_create_sets_content_hash(self, service: OpportunityService):
        result = await service.create_opportunity(
            user_id=uuid.uuid4(),
            platform="freelancer",
            external_id="fl-002",
            title="Same Title",
            description="Same desc",
            budget_max=1000.0,
            country="US",
        )
        result2 = await service.create_opportunity(
            user_id=uuid.uuid4(),
            platform="freelancer",
            external_id="fl-003",
            title="Same Title",
            description="Same desc",
            budget_max=1000.0,
            country="US",
        )
        assert result.content_hash == result2.content_hash


class TestGetById:
    async def test_get_by_id_returns_opportunity(self, service: OpportunityService, existing_opportunity: Opportunity):
        result = await service.get_by_id(existing_opportunity.id, user_id=existing_opportunity.user_id)
        assert result.id == existing_opportunity.id
        assert result.title == existing_opportunity.title

    async def test_get_by_id_raises_not_found_wrong_user(self, service: OpportunityService, existing_opportunity: Opportunity):
        with pytest.raises(NotFoundError):
            await service.get_by_id(existing_opportunity.id, user_id=uuid.uuid4())

    async def test_get_by_id_raises_not_found_missing(self, service: OpportunityService):
        with pytest.raises(NotFoundError):
            await service.get_by_id(uuid.uuid4(), user_id=uuid.uuid4())


class TestGetAll:
    async def test_get_all_returns_user_opportunities(self, service: OpportunityService):
        user_id = uuid.uuid4()
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="A")
        await service.create_opportunity(user_id=user_id, platform="upwork", title="B")
        items, total = await service.get_all(user_id=user_id)
        assert total == 2

    async def test_get_all_filters_by_platform(self, service: OpportunityService):
        user_id = uuid.uuid4()
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="A")
        await service.create_opportunity(user_id=user_id, platform="upwork", title="B")
        items, total = await service.get_all(user_id=user_id, platform="freelancer")
        assert total == 1


class TestSearch:
    async def test_search_by_keyword(self, service: OpportunityService):
        user_id = uuid.uuid4()
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="Python Developer")
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="React Developer")
        params = SearchParams(keyword="python")
        items, total = await service.search(user_id=user_id, params=params)
        assert total == 1

    async def test_search_by_budget_range(self, service: OpportunityService):
        user_id = uuid.uuid4()
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="Small", budget_max=1000.0)
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="Large", budget_max=10000.0)
        params = SearchParams(budget_min=5000.0)
        items, total = await service.search(user_id=user_id, params=params)
        assert total == 1


class TestStatistics:
    async def test_statistics(self, service: OpportunityService):
        user_id = uuid.uuid4()
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="A", category="Web Dev")
        await service.create_opportunity(user_id=user_id, platform="freelancer", title="B", category="Web Dev")
        await service.create_opportunity(user_id=user_id, platform="upwork", title="C", category="Mobile")
        stats = await service.get_statistics(user_id=user_id)
        assert stats["total_opportunities"] == 3
        assert stats["by_platform"]["freelancer"] == 2
        assert stats["by_platform"]["upwork"] == 1
        assert stats["by_category"]["Web Dev"] == 2
        assert stats["by_category"]["Mobile"] == 1
