"""
Dependency injection for marketplace services.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.infrastructure.providers.freelancer_provider import FreelancerProvider
from app.infrastructure.providers.marketplace_base import MarketplaceProvider
from app.models.user import User
from app.repositories.marketplace_account_repository import MarketplaceAccountRepository
from app.repositories.marketplace_token_repository import MarketplaceTokenRepository
from app.repositories.marketplace_sync_history_repository import MarketplaceSyncHistoryRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.import_history_repository import ImportHistoryRepository
from app.services.marketplace_auth_service import MarketplaceAuthService
from app.services.marketplace_sync_service import MarketplaceSyncService
from app.services.marketplace_analytics_service import MarketplaceAnalyticsService
from app.services.opportunity_service import OpportunityService


def get_marketplace_account_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MarketplaceAccountRepository:
    return MarketplaceAccountRepository(session)


def get_marketplace_token_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MarketplaceTokenRepository:
    return MarketplaceTokenRepository(session)


def get_marketplace_sync_history_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MarketplaceSyncHistoryRepository:
    return MarketplaceSyncHistoryRepository(session)


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


def get_marketplace_auth_service(
    account_repo: Annotated[MarketplaceAccountRepository, Depends(get_marketplace_account_repository)],
    token_repo: Annotated[MarketplaceTokenRepository, Depends(get_marketplace_token_repository)],
) -> MarketplaceAuthService:
    return MarketplaceAuthService(account_repo=account_repo, token_repo=token_repo)


def get_marketplace_sync_service(
    account_repo: Annotated[MarketplaceAccountRepository, Depends(get_marketplace_account_repository)],
    sync_history_repo: Annotated[MarketplaceSyncHistoryRepository, Depends(get_marketplace_sync_history_repository)],
    opportunity_repo: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
    import_history_repo: Annotated[ImportHistoryRepository, Depends(get_import_history_repository)],
    opportunity_service: Annotated[OpportunityService, Depends(get_opportunity_service)],
    auth_service: Annotated[MarketplaceAuthService, Depends(get_marketplace_auth_service)],
) -> MarketplaceSyncService:
    return MarketplaceSyncService(
        account_repo=account_repo,
        sync_history_repo=sync_history_repo,
        opportunity_repo=opportunity_repo,
        import_history_repo=import_history_repo,
        opportunity_service=opportunity_service,
        auth_service=auth_service,
    )


def get_marketplace_analytics_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MarketplaceAnalyticsService:
    return MarketplaceAnalyticsService(session)


def get_freelancer_provider() -> FreelancerProvider:
    return FreelancerProvider(sandbox=False)


def get_provider_for_platform(platform: str) -> MarketplaceProvider:
    providers = {
        "freelancer": FreelancerProvider(sandbox=False),
    }
    provider = providers.get(platform)
    if provider is None:
        raise ValueError(f"Unsupported platform: {platform}")
    return provider


CurrentUser = Annotated[User, Depends(get_current_user)]
