import uuid

import pytest
from app.infrastructure.providers.freelancer_mock import MockFreelancerProvider


@pytest.fixture
def provider():
    return MockFreelancerProvider()


class TestMockFreelancerProvider:
    async def test_fetch_opportunities_returns_list(self, provider):
        opportunities = await provider.fetch_opportunities(user_id=uuid.uuid4())
        assert len(opportunities) == 5
        assert all(o.platform == "freelancer" for o in opportunities)

    async def test_fetch_opportunities_returns_normalized(self, provider):
        opportunities = await provider.fetch_opportunities(user_id=uuid.uuid4())
        opp = opportunities[0]
        assert opp.title is not None
        assert opp.external_id is not None
        assert opp.budget_max is not None
        assert opp.platform == "freelancer"

    async def test_fetch_opportunity_details_found(self, provider):
        opp = await provider.fetch_opportunity_details("fl-1001")
        assert opp is not None
        assert opp.title == "Full-Stack Web Developer for SaaS Platform"

    async def test_fetch_opportunity_details_not_found(self, provider):
        opp = await provider.fetch_opportunity_details("nonexistent")
        assert opp is None

    async def test_validate_payload_valid(self, provider):
        assert await provider.validate_payload({"title": "Test"}) is True

    async def test_validate_payload_invalid(self, provider):
        assert await provider.validate_payload({}) is False

    async def test_health_check_returns_true(self, provider):
        assert await provider.health_check() is True
