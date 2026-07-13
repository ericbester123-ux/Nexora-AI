"""
Marketplace connection API endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.limiter import limiter
from app.dependencies.auth import CurrentUser
from app.dependencies.marketplace import (
    get_marketplace_auth_service,
    get_marketplace_sync_service,
    get_marketplace_analytics_service,
    get_freelancer_provider,
    get_provider_for_platform,
    get_marketplace_account_repository,
    get_marketplace_token_repository,
)
from app.infrastructure.providers.freelancer_provider import FreelancerProvider
from app.services.marketplace_auth_service import MarketplaceAuthService
from app.services.marketplace_sync_service import MarketplaceSyncService
from app.services.marketplace_analytics_service import MarketplaceAnalyticsService
from app.services.opportunity_service import OpportunityService
from app.repositories.marketplace_account_repository import MarketplaceAccountRepository
from app.repositories.marketplace_token_repository import MarketplaceTokenRepository
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


# --- Schemas ---

class MarketplaceAccountResponse(BaseModel):
    id: str
    provider: str
    external_user_id: str | None = None
    username: str | None = None
    display_name: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    projects_completed: int | None = None
    verification_status: str | None = None
    member_since: str | None = None
    is_active: bool = True
    last_sync_at: str | None = None
    sync_status: str = "never"
    sync_error_message: str | None = None
    connected_at: str | None = None
    has_valid_token: bool = False


class MarketplaceAccountDetailResponse(MarketplaceAccountResponse):
    email: str | None = None
    disconnected_at: str | None = None
    token_expires_at: str | None = None


class MarketplaceConnectResponse(BaseModel):
    id: str
    provider: str
    external_user_id: str | None = None
    username: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    message: str


class MarketplaceSyncResponse(BaseModel):
    account_id: str
    status: str
    projects_found: int = 0
    projects_imported: int = 0
    projects_updated: int = 0
    projects_skipped: int = 0
    projects_failed: int = 0
    duration_ms: float | None = None


class MarketplaceSyncHistoryItem(BaseModel):
    id: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: float | None = None
    projects_found: int = 0
    projects_imported: int = 0
    projects_updated: int = 0
    projects_skipped: int = 0
    projects_failed: int = 0
    error_message: str | None = None


class MarketplaceSyncStatusResponse(BaseModel):
    account_id: str
    provider: str
    sync_status: str
    last_sync_at: str | None = None
    sync_error_message: str | None = None


class MarketplaceAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class MarketplaceExchangeCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    redirect_uri: str | None = None


class MarketplaceEmailLinkRequest(BaseModel):
    email: str = Field(..., max_length=255)


class MarketplaceProviderStats(BaseModel):
    provider: str
    total_projects_imported: int = 0
    projects_viewed: int = 0
    proposals_generated: int = 0
    proposals_submitted: int = 0
    projects_won: int = 0
    projects_lost: int = 0
    win_rate: float = 0
    average_bid_amount: float = 0
    total_syncs: int = 0
    last_sync_at: str | None = None
    last_sync_status: str | None = None


# --- Endpoints ---

@router.get(
    "/accounts",
    response_model=list[MarketplaceAccountResponse],
    summary="List all connected marketplace accounts",
)
async def list_accounts(
    current_user: CurrentUser,
    auth_service: Annotated[MarketplaceAuthService, Depends(get_marketplace_auth_service)],
) -> list[MarketplaceAccountResponse]:
    """List all connected marketplace accounts for the current user."""
    accounts = await auth_service.get_accounts(current_user.id)
    return [MarketplaceAccountResponse(**a) for a in accounts]


@router.get(
    "/accounts/{account_id}",
    response_model=MarketplaceAccountDetailResponse,
    summary="Get marketplace account details",
)
async def get_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    auth_service: Annotated[MarketplaceAuthService, Depends(get_marketplace_auth_service)],
) -> MarketplaceAccountDetailResponse:
    """Get detailed information about a connected marketplace account."""
    account = await auth_service.get_account(current_user.id, account_id)
    return MarketplaceAccountDetailResponse(**account)


@router.get(
    "/{provider}/auth-url",
    response_model=MarketplaceAuthUrlResponse,
    summary="Get OAuth authorization URL for a marketplace provider",
)
async def get_auth_url(
    provider: str,
    current_user: CurrentUser,
    account_repo: Annotated[MarketplaceAccountRepository, Depends(get_marketplace_account_repository)],
) -> MarketplaceAuthUrlResponse:
    """Get the OAuth authorization URL for connecting a marketplace account."""
    import secrets

    if provider != "freelancer":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider}")

    settings = get_settings()

    if not settings.FREELANCER_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Freelancer.com integration is not configured. Set FREELANCER_CLIENT_ID in the environment.",
        )

    freelancer_provider = FreelancerProvider(sandbox=False)

    state = secrets.token_urlsafe(32)
    redirect_uri = f"{settings.FRONTEND_URL}/api/integrations/freelancer/callback"

    auth_url = await freelancer_provider.get_auth_url(state, redirect_uri)
    auth_url = f"{auth_url}&client_id={settings.FREELANCER_CLIENT_ID}"

    return MarketplaceAuthUrlResponse(auth_url=auth_url, state=state)


@router.post(
    "/{provider}/email-link",
    response_model=MarketplaceConnectResponse,
    summary="Link a marketplace account by email reference",
)
async def link_by_email(
    provider: str,
    payload: MarketplaceEmailLinkRequest,
    current_user: CurrentUser,
    account_repo: Annotated[MarketplaceAccountRepository, Depends(get_marketplace_account_repository)],
) -> MarketplaceConnectResponse:
    """Save a Freelancer email reference on the user's profile. No OAuth is performed — the email is stored as metadata for later completion via OAuth."""
    if provider != "freelancer":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider}")

    existing = await account_repo.get_by_provider(current_user.id, provider)
    if existing:
        existing = await account_repo.update(existing, email=payload.email)
        return MarketplaceConnectResponse(
            id=str(existing.id),
            provider=provider,
            message="Freelancer email saved. You can now sign in with Freelancer to complete the connection.",
        )

    account = await account_repo.create(
        user_id=current_user.id,
        provider=provider,
        email=payload.email,
    )
    return MarketplaceConnectResponse(
        id=str(account.id),
        provider=provider,
        message="Freelancer email saved. You can now sign in with Freelancer to complete the connection.",
    )


@router.post(
    "/{provider}/exchange-code",
    response_model=MarketplaceConnectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Exchange OAuth code for tokens and connect account",
)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def exchange_code_and_connect(
    request: Request,
    provider: str,
    payload: MarketplaceExchangeCodeRequest,
    current_user: CurrentUser,
    auth_service: Annotated[MarketplaceAuthService, Depends(get_marketplace_auth_service)],
    sync_service: Annotated[MarketplaceSyncService, Depends(get_marketplace_sync_service)],
) -> MarketplaceConnectResponse:
    """Exchange authorization code for access token and connect the marketplace account."""
    if provider != "freelancer":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider}")

    settings = get_settings()
    freelancer_provider = FreelancerProvider(sandbox=False)
    redirect_uri = payload.redirect_uri or f"{settings.FRONTEND_URL}/api/integrations/freelancer/callback"

    result = await auth_service.exchange_and_connect(
        user_id=current_user.id,
        provider=freelancer_provider,
        code=payload.code,
        redirect_uri=redirect_uri,
    )

    # Auto-sync projects immediately after connection
    try:
        await sync_service.sync_account(
            user_id=current_user.id,
            account_id=uuid.UUID(result["id"]),
            provider=freelancer_provider,
            marketplace_provider=freelancer_provider,
            max_results=200,
        )
        result["message"] += " Projects synced successfully."
    except Exception:
        result["message"] += " Connection successful. Sync will retry shortly."

    return MarketplaceConnectResponse(**result)


@router.post(
    "/{provider}/direct-connect",
    response_model=MarketplaceConnectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect using existing OAuth token (direct connect)",
)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def direct_connect(
    request: Request,
    provider: str,
    current_user: CurrentUser,
    auth_service: Annotated[MarketplaceAuthService, Depends(get_marketplace_auth_service)],
    account_repo: Annotated[MarketplaceAccountRepository, Depends(get_marketplace_account_repository)],
    token_repo: Annotated[MarketplaceTokenRepository, Depends(get_marketplace_token_repository)],
) -> MarketplaceConnectResponse:
    """
    Connect a marketplace account using an existing OAuth token.
    The token should be obtained from the provider's developer portal.
    """
    if provider != "freelancer":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider}")

    from pydantic import BaseModel, Field as PydanticField

    class DirectConnectRequest(BaseModel):
        oauth_token: str = PydanticField(..., min_length=1)
        refresh_token: str | None = None
        expires_in: int | None = None

    body = DirectConnectRequest(**await request.json())
    freelancer_provider = FreelancerProvider(sandbox=False)

    # Validate token
    try:
        external_user_id = await freelancer_provider.get_self_user_id(body.oauth_token)
        profile = await freelancer_provider.get_user_profile(body.oauth_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token: {str(e)}",
        )

    # Check if already connected
    existing = await account_repo.get_by_external_id(provider, external_user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{provider.title()} account already connected.",
        )

    from datetime import datetime, timezone, timedelta
    from app.core.security import encrypt_token

    expires_at = None
    if body.expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=body.expires_in)

    account = await account_repo.create(
        user_id=current_user.id,
        provider=provider,
        external_user_id=profile.external_user_id,
        username=profile.username,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        profile_url=profile.profile_url,
        rating=profile.rating,
        reviews_count=profile.reviews_count,
        projects_completed=profile.projects_completed,
        verification_status=profile.verification_status,
        member_since=profile.member_since,
        connected_at=datetime.now(timezone.utc),
    )

    await token_repo.create(
        account_id=account.id,
        token_type="access",
        encrypted_token=encrypt_token(body.oauth_token),
        expires_at=expires_at,
    )
    if body.refresh_token:
        await token_repo.create(
            account_id=account.id,
            token_type="refresh",
            encrypted_token=encrypt_token(body.refresh_token),
        )

    return MarketplaceConnectResponse(
        id=str(account.id),
        provider=provider,
        external_user_id=profile.external_user_id,
        username=profile.username,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        message=f"{provider.title()} account connected successfully.",
    )


@router.delete(
    "/accounts/{account_id}",
    response_model=MessageResponse,
    summary="Disconnect a marketplace account",
)
async def disconnect_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    auth_service: Annotated[MarketplaceAuthService, Depends(get_marketplace_auth_service)],
) -> MessageResponse:
    """Disconnect a marketplace account."""
    await auth_service.disconnect(current_user.id, account_id)
    return MessageResponse(message="Account disconnected successfully.")


@router.post(
    "/accounts/{account_id}/reconnect",
    response_model=MessageResponse,
    summary="Reconnect a marketplace account (token refresh)",
)
async def reconnect_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    auth_service: Annotated[MarketplaceAuthService, Depends(get_marketplace_auth_service)],
) -> MessageResponse:
    """Reconnect a marketplace account by refreshing its tokens."""
    freelancer_provider = FreelancerProvider(sandbox=False)
    message = await auth_service.reconnect(
        user_id=current_user.id,
        account_id=account_id,
        provider=freelancer_provider,
    )
    return MessageResponse(message=message)


@router.post(
    "/accounts/{account_id}/sync",
    response_model=MarketplaceSyncResponse,
    summary="Sync projects from a marketplace account",
)
async def sync_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    sync_service: Annotated[MarketplaceSyncService, Depends(get_marketplace_sync_service)],
    max_results: int = Query(default=50, ge=1, le=100),
) -> MarketplaceSyncResponse:
    """Sync latest projects from a connected marketplace account."""
    freelancer_provider = FreelancerProvider(sandbox=False)
    result = await sync_service.sync_account(
        user_id=current_user.id,
        account_id=account_id,
        provider=freelancer_provider,
        marketplace_provider=freelancer_provider,
        max_results=max_results,
    )
    return MarketplaceSyncResponse(**result)


@router.get(
    "/accounts/{account_id}/sync-history",
    response_model=list[MarketplaceSyncHistoryItem],
    summary="Get sync history for a marketplace account",
)
async def get_sync_history(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    sync_service: Annotated[MarketplaceSyncService, Depends(get_marketplace_sync_service)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[MarketplaceSyncHistoryItem]:
    """Get sync history for a marketplace account."""
    history = await sync_service.get_sync_history(current_user.id, account_id, limit=limit)
    return [MarketplaceSyncHistoryItem(**h) for h in history]


@router.get(
    "/sync-status",
    response_model=list[MarketplaceSyncStatusResponse],
    summary="Get sync status for all connected accounts",
)
async def get_all_sync_status(
    current_user: CurrentUser,
    sync_service: Annotated[MarketplaceSyncService, Depends(get_marketplace_sync_service)],
) -> list[MarketplaceSyncStatusResponse]:
    """Get sync status for all connected marketplace accounts."""
    statuses = await sync_service.get_all_sync_status(current_user.id)
    return [MarketplaceSyncStatusResponse(**s) for s in statuses]


@router.get(
    "/accounts/{account_id}/stats",
    response_model=MarketplaceProviderStats,
    summary="Get analytics stats for a marketplace account",
)
async def get_account_stats(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    analytics_service: Annotated[MarketplaceAnalyticsService, Depends(get_marketplace_analytics_service)],
) -> MarketplaceProviderStats:
    """Get analytics statistics for a marketplace account."""
    stats = await analytics_service.get_provider_stats(current_user.id, account_id)
    return MarketplaceProviderStats(**stats)
