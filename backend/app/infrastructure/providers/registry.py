from app.infrastructure.providers.base import BaseOpportunityProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, BaseOpportunityProvider] = {}

    def register(self, platform: str, provider: BaseOpportunityProvider) -> None:
        self._providers[platform.lower()] = provider

    def get(self, platform: str) -> BaseOpportunityProvider | None:
        return self._providers.get(platform.lower())

    def get_all(self) -> dict[str, BaseOpportunityProvider]:
        return dict(self._providers)

    def get_platforms(self) -> list[str]:
        return list(self._providers.keys())
