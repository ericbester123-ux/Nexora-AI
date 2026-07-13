from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db
from app.domain.events.opportunity_events import EventBus
from app.dependencies.auth import get_ai_preference_service, get_user_preference_service
from app.infrastructure.providers import ProviderRegistry
from app.infrastructure.providers.freelancer_mock import MockFreelancerProvider
from app.infrastructure.providers.freelancer_real import FreelancerProvider
from app.repositories.import_history_repository import ImportHistoryRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.import_service import ImportService
from app.services.opportunity_service import OpportunityService
from app.services.preference_service import AIPreferenceService, UserPreferenceService
from app.services.scoring_service import ScoringService

_event_bus: EventBus | None = None
_provider_registry: ProviderRegistry | None = None


def _get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def _get_provider_registry() -> ProviderRegistry:
    global _provider_registry
    if _provider_registry is None:
        settings = get_settings()
        registry = ProviderRegistry()
        registry.register("freelancer", MockFreelancerProvider())
        
        # Register real Freelancer provider if OAuth token is configured
        if settings.FREELANCER_OAUTH_TOKEN:
            sandbox = settings.FREELANCER_API_URL and "sandbox" in settings.FREELANCER_API_URL
            registry.register("freelancer", FreelancerProvider(
                oauth_token=settings.FREELANCER_OAUTH_TOKEN,
                sandbox=sandbox,
            ))
        else:
            # Keep mock as fallback when no token is configured
            registry.register("freelancer", MockFreelancerProvider())
        _provider_registry = registry
    return _provider_registry


def get_opportunity_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OpportunityRepository:
    return OpportunityRepository(session)


def get_import_history_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ImportHistoryRepository:
    return ImportHistoryRepository(session)


def get_opportunity_service(
    repo: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
) -> OpportunityService:
    return OpportunityService(repo)


def get_import_service(
    opportunity_repo: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
    import_history_repo: Annotated[ImportHistoryRepository, Depends(get_import_history_repository)],
    opportunity_service: Annotated[OpportunityService, Depends(get_opportunity_service)],
) -> ImportService:
    return ImportService(
        provider_registry=_get_provider_registry(),
        opportunity_repository=opportunity_repo,
        import_history_repository=import_history_repo,
        opportunity_service=opportunity_service,
        event_bus=_get_event_bus(),
    )


def get_scoring_service(
    opportunity_service: Annotated[OpportunityService, Depends(get_opportunity_service)],
) -> ScoringService:
    return ScoringService(opportunity_service)
