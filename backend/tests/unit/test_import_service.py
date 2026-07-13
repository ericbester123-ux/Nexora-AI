import uuid
from datetime import datetime, timezone

import pytest
from app.core.exceptions import BadRequestError
from app.domain.events.opportunity_events import EventBus, ImportCompleted, OpportunityImported, OpportunitySkipped, OpportunityUpdated
from app.infrastructure.providers.base import BaseOpportunityProvider, NormalizedOpportunity
from app.infrastructure.providers.registry import ProviderRegistry
from app.models.import_history import ImportHistory
from app.models.opportunity import Opportunity
from app.repositories.import_history_repository import ImportHistoryRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.import_service import ImportService
from app.services.opportunity_service import OpportunityService


class FakeProvider(BaseOpportunityProvider):
    def __init__(self, opportunities: list[NormalizedOpportunity] | None = None):
        self._opportunities = opportunities or []

    async def fetch_opportunities(self, user_id: uuid.UUID, **kwargs) -> list[NormalizedOpportunity]:
        return list(self._opportunities)

    async def fetch_opportunity_details(self, external_id: str) -> NormalizedOpportunity | None:
        for o in self._opportunities:
            if o.external_id == external_id:
                return o
        return None

    async def validate_payload(self, payload: dict) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


class FakeOpportunityRepo:
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
        opp = Opportunity(id=uuid.uuid4(), **fields)
        self._opportunities[opp.id] = opp
        return opp

    async def update(self, opportunity, **fields):
        for k, v in fields.items():
            setattr(opportunity, k, v)
        return opportunity


class FakeImportHistoryRepo:
    def __init__(self):
        self._records: dict[uuid.UUID, ImportHistory] = {}

    async def get_by_id(self, id):
        return self._records.get(id)

    async def create(self, **fields):
        record = ImportHistory(id=uuid.uuid4(), **fields)
        self._records[record.id] = record
        return record

    async def update(self, record, **fields):
        for k, v in fields.items():
            setattr(record, k, v)
        return record

    async def get_all(self, user_id, skip=0, limit=20, platform=None, status=None):
        items = [r for r in self._records.values() if r.user_id == user_id]
        if platform:
            items = [r for r in items if r.platform == platform]
        if status:
            items = [r for r in items if r.status == status]
        return sorted(items, key=lambda r: r.started_at, reverse=True)[skip:skip + limit], len(items)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def provider_registry():
    registry = ProviderRegistry()
    registry.register("freelancer", FakeProvider())
    return registry


@pytest.fixture
def import_service(provider_registry, event_bus):
    opp_repo = FakeOpportunityRepo()
    import_repo = FakeImportHistoryRepo()
    opp_service = OpportunityService(repository=opp_repo)
    return ImportService(
        provider_registry=provider_registry,
        opportunity_repository=opp_repo,
        import_history_repository=import_repo,
        opportunity_service=opp_service,
        event_bus=event_bus,
    )


@pytest.fixture
def import_service_with_provider(provider_registry, event_bus):
    opp_repo = FakeOpportunityRepo()
    import_repo = FakeImportHistoryRepo()
    opp_service = OpportunityService(repository=opp_repo)
    provider = FakeProvider([
        NormalizedOpportunity(
            external_id="fl-001",
            platform="freelancer",
            title="Test Project",
            description="A test",
            budget_max=5000.0,
            country="US",
            category="Web Dev",
            skills=["Python"],
        ),
        NormalizedOpportunity(
            external_id="fl-002",
            platform="freelancer",
            title="Another Project",
            description="Another test",
            budget_max=3000.0,
            country="GB",
            category="Mobile",
            skills=["React Native"],
        ),
    ])
    provider_registry.register("freelancer", provider)
    return ImportService(
        provider_registry=provider_registry,
        opportunity_repository=opp_repo,
        import_history_repository=import_repo,
        opportunity_service=opp_service,
        event_bus=event_bus,
    )


class TestImportService:
    async def test_import_opportunities_creates_records(self, import_service_with_provider):
        user_id = uuid.uuid4()
        result = await import_service_with_provider.import_opportunities(
            user_id=user_id,
            platform="freelancer",
        )
        assert result.status == "completed"
        assert result.opportunities_found == 2
        assert result.imported == 2
        assert result.updated == 0
        assert result.skipped == 0
        assert result.failed == 0
        assert result.platform == "freelancer"
        assert result.started_at is not None
        assert result.completed_at is not None

    async def test_import_skips_duplicates(self, import_service_with_provider):
        user_id = uuid.uuid4()
        await import_service_with_provider.import_opportunities(user_id=user_id, platform="freelancer")
        result = await import_service_with_provider.import_opportunities(user_id=user_id, platform="freelancer")
        assert result.skipped == 2
        assert result.imported == 0

    async def test_import_updates_existing_opportunity(self, import_service_with_provider):
        user_id = uuid.uuid4()
        await import_service_with_provider.import_opportunities(user_id=user_id, platform="freelancer")
        provider = import_service_with_provider._registry.get("freelancer")
        provider._opportunities[0].budget_max = 6000.0
        result = await import_service_with_provider.import_opportunities(user_id=user_id, platform="freelancer")
        assert result.updated == 1
        assert result.skipped == 1

    async def test_import_raises_for_unsupported_platform(self, import_service):
        with pytest.raises(BadRequestError):
            await import_service.import_opportunities(user_id=uuid.uuid4(), platform="nonexistent")

    async def test_import_limits_max_results(self, import_service_with_provider):
        user_id = uuid.uuid4()
        result = await import_service_with_provider.import_opportunities(
            user_id=user_id,
            platform="freelancer",
            max_results=1,
        )
        assert result.opportunities_found == 1

    async def test_import_records_failures(self, event_bus):
        class FailingProvider(FakeProvider):
            async def fetch_opportunities(self, user_id, **kwargs):
                return [
                    NormalizedOpportunity(external_id="fl-001", platform="freelancer", title="Good"),
                ]

            async def validate_payload(self, payload):
                return True

            async def health_check(self):
                return True

        registry = ProviderRegistry()
        registry.register("freelancer", FailingProvider())
        opp_repo = FakeOpportunityRepo()
        import_repo = FakeImportHistoryRepo()
        opp_service = OpportunityService(repository=opp_repo)

        service = ImportService(
            provider_registry=registry,
            opportunity_repository=opp_repo,
            import_history_repository=import_repo,
            opportunity_service=opp_service,
            event_bus=event_bus,
        )
        result = await service.import_opportunities(user_id=uuid.uuid4(), platform="freelancer")
        assert result.imported == 1

    async def test_domain_events_are_published(self, provider_registry, event_bus):
        received = []

        def capture(event):
            received.append(type(event).__name__)

        event_bus.register(OpportunityImported, capture)
        event_bus.register(ImportCompleted, capture)
        opp_repo = FakeOpportunityRepo()
        import_repo = FakeImportHistoryRepo()
        opp_service = OpportunityService(repository=opp_repo)

        provider = FakeProvider([
            NormalizedOpportunity(external_id="fl-001", platform="freelancer", title="Event Test"),
        ])
        provider_registry.register("freelancer", provider)

        service = ImportService(
            provider_registry=provider_registry,
            opportunity_repository=opp_repo,
            import_history_repository=import_repo,
            opportunity_service=opp_service,
            event_bus=event_bus,
        )
        await service.import_opportunities(user_id=uuid.uuid4(), platform="freelancer")
        assert "OpportunityImported" in received
        assert "ImportCompleted" in received
