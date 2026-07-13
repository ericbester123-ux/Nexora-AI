import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalizedOpportunity:
    external_id: str | None
    platform: str
    title: str
    description: str | None = None
    url: str | None = None
    project_type: str | None = None
    experience_level: str | None = None
    duration: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    budget_type: str | None = None
    currency: str = "USD"
    skills: list[str] | None = None
    category: str | None = None
    subcategory: str | None = None
    country: str | None = None
    client_rating: float | None = None
    client_reviews_count: int | None = None
    client_payment_verified: bool | None = None
    client_total_hired: int | None = None
    is_remote: bool = True
    is_negotiable: bool = False
    posted_at: datetime | None = None
    deadline: datetime | None = None
    raw_data: dict | None = field(default_factory=dict)


class BaseOpportunityProvider(ABC):
    @abstractmethod
    async def fetch_opportunities(self, user_id: uuid.UUID, **kwargs) -> list[NormalizedOpportunity]:
        ...

    @abstractmethod
    async def fetch_opportunity_details(self, external_id: str) -> NormalizedOpportunity | None:
        ...

    @abstractmethod
    async def validate_payload(self, payload: dict) -> bool:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
