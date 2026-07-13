"""
MarketplaceProvider interface - abstract base for all marketplace integrations.

This extends BaseOpportunityProvider with account management, auth, and
profile methods needed for the full connection lifecycle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketplaceUserProfile:
    external_user_id: str
    username: str | None = None
    display_name: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    projects_completed: int | None = None
    verification_status: str | None = None
    member_since: datetime | None = None
    raw_data: dict | None = None


class MarketplaceProvider(ABC):
    @abstractmethod
    def get_platform_name(self) -> str:
        ...

    @abstractmethod
    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        ...

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
        ...

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str, client_id: str, client_secret: str) -> dict:
        ...

    @abstractmethod
    async def get_user_profile(self, access_token: str) -> MarketplaceUserProfile:
        ...

    @abstractmethod
    async def get_self_user_id(self, access_token: str) -> str:
        ...

    @abstractmethod
    async def validate_token(self, access_token: str) -> bool:
        ...
