import uuid
from datetime import datetime, timezone
from typing import Any, Callable


class DomainEvent:
    def __init__(self) -> None:
        self.event_id: str = uuid.uuid4().hex
        self.occurred_at: datetime = datetime.now(timezone.utc)


class OpportunityImported(DomainEvent):
    def __init__(self, opportunity_id: uuid.UUID, user_id: uuid.UUID, platform: str, title: str) -> None:
        super().__init__()
        self.opportunity_id = opportunity_id
        self.user_id = user_id
        self.platform = platform
        self.title = title


class OpportunityUpdated(DomainEvent):
    def __init__(self, opportunity_id: uuid.UUID, user_id: uuid.UUID, platform: str, title: str) -> None:
        super().__init__()
        self.opportunity_id = opportunity_id
        self.user_id = user_id
        self.platform = platform
        self.title = title


class OpportunitySkipped(DomainEvent):
    def __init__(self, platform: str, reason: str, external_id: str | None = None) -> None:
        super().__init__()
        self.platform = platform
        self.reason = reason
        self.external_id = external_id


class ImportCompleted(DomainEvent):
    def __init__(
        self, import_id: uuid.UUID, user_id: uuid.UUID, platform: str, imported: int, updated: int, skipped: int, failed: int
    ) -> None:
        super().__init__()
        self.import_id = import_id
        self.user_id = user_id
        self.platform = platform
        self.imported = imported
        self.updated = updated
        self.skipped = skipped
        self.failed = failed


EventHandler = Callable[[DomainEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    def register(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            handler(event)
