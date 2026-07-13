import uuid

import pytest
from app.domain.events.opportunity_events import (
    DomainEvent,
    EventBus,
    ImportCompleted,
    OpportunityImported,
    OpportunitySkipped,
    OpportunityUpdated,
)


class TestDomainEvents:
    def test_event_has_id_and_timestamp(self):
        event = OpportunityImported(
            opportunity_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            platform="freelancer",
            title="Test",
        )
        assert event.event_id is not None
        assert event.occurred_at is not None
        assert event.platform == "freelancer"
        assert event.title == "Test"

    def test_opportunity_imported_event(self):
        opp_id = uuid.uuid4()
        user_id = uuid.uuid4()
        event = OpportunityImported(
            opportunity_id=opp_id,
            user_id=user_id,
            platform="upwork",
            title="Project X",
        )
        assert event.opportunity_id == opp_id
        assert event.user_id == user_id
        assert event.platform == "upwork"
        assert event.title == "Project X"

    def test_opportunity_updated_event(self):
        event = OpportunityUpdated(
            opportunity_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            platform="freelancer",
            title="Updated",
        )
        assert event.title == "Updated"

    def test_opportunity_skipped_event(self):
        event = OpportunitySkipped(platform="freelancer", reason="duplicate", external_id="fl-001")
        assert event.platform == "freelancer"
        assert event.reason == "duplicate"
        assert event.external_id == "fl-001"

    def test_import_completed_event(self):
        event = ImportCompleted(
            import_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            platform="freelancer",
            imported=5,
            updated=2,
            skipped=1,
            failed=0,
        )
        assert event.imported == 5
        assert event.updated == 2
        assert event.skipped == 1
        assert event.failed == 0


class TestEventBus:
    @pytest.mark.asyncio
    async def test_register_and_publish(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.register(OpportunityImported, handler)
        event = OpportunityImported(
            opportunity_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            platform="freelancer",
            title="Test",
        )
        await bus.publish(event)
        assert len(received) == 1
        assert received[0].title == "Test"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        bus = EventBus()
        results = []

        def handler1(event):
            results.append("h1")

        def handler2(event):
            results.append("h2")

        bus.register(OpportunityImported, handler1)
        bus.register(OpportunityImported, handler2)
        await bus.publish(
            OpportunityImported(
                opportunity_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                platform="freelancer",
                title="Test",
            )
        )
        assert "h1" in results
        assert "h2" in results

    @pytest.mark.asyncio
    async def test_no_handler_no_error(self):
        bus = EventBus()
        await bus.publish(
            OpportunityImported(
                opportunity_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                platform="freelancer",
                title="Test",
            )
        )
