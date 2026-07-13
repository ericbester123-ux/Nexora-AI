"""
Freelancer integration endpoints.
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.limiter import limiter
from app.dependencies.auth import CurrentUser, get_auth_service, get_user_service
from app.dependencies.opportunities import get_import_service
from app.schemas.auth import MessageResponse
from app.services.auth_service import AuthService
from app.services.import_service import ImportService
from app.services.user_service import UserService

router = APIRouter(prefix="/integrations/freelancer", tags=["Freelancer Integration"])


class FreelancerConnectRequest(BaseModel):
    oauth_token: str = Field(..., min_length=1, description="Freelancer OAuth2 access token")
    refresh_token: str | None = Field(default=None, min_length=1, description="Freelancer OAuth2 refresh token")
    expires_in: int | None = Field(default=None, ge=0, description="Token expiry in seconds")


class FreelancerConnectResponse(BaseModel):
    freelancer_user_id: str
    freelancer_username: str
    connected_at: datetime
    message: str


class FreelancerSyncRequest(BaseModel):
    max_results: int | None = Field(default=20, ge=1, le=100)
    query: str = Field(default="", description="Search query for projects")


class FreelancerSyncResponse(BaseModel):
    projects_synced: int
    projects_new: int
    projects_updated: int
    import_id: uuid.UUID


class FreelancerStatusResponse(BaseModel):
    is_connected: bool
    freelancer_user_id: str | None = None
    freelancer_username: str | None = None
    connected_at: datetime | None = None
    token_expires_at: datetime | None = None


@router.get(
    "/status",
    response_model=FreelancerStatusResponse,
    summary="Check Freelancer connection status",
)
async def get_freelancer_status(current_user: CurrentUser) -> FreelancerStatusResponse:
    """Check if the user has connected their Freelancer account."""
    return FreelancerStatusResponse(
        is_connected=current_user.freelancer_user_id is not None,
        freelancer_user_id=current_user.freelancer_user_id,
        connected_at=current_user.freelancer_connected_at,
        token_expires_at=current_user.freelancer_token_expires_at,
    )


@router.post(
    "/connect",
    response_model=FreelancerConnectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect Freelancer account",
)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def connect_freelancer(
    request: Request,
    payload: FreelancerConnectRequest,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> FreelancerConnectResponse:
    """
    Connect a Freelancer account by providing OAuth2 tokens.
    
    The user must obtain an OAuth2 token from Freelancer's developer portal.
    """
    if current_user.freelancer_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Freelancer account already connected. Disconnect first to connect a different account.",
        )

    # Validate token by fetching user profile from Freelancer
    from freelancersdk.session import Session
    from freelancersdk.resources.users.users import get_self_user_id
    from freelancersdk.resources.users.exceptions import UsersNotFoundException

    try:
        session = Session(oauth_token=payload.oauth_token, url="https://www.freelancer.com")
        freelancer_user_id = get_self_user_id(session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Freelancer token: {str(e)}",
        )

    # Check if this Freelancer account is already linked to another user
    from app.dependencies.opportunities import _get_provider_registry
    from app.infrastructure.providers.freelancer_real import FreelancerProvider
    from app.dependencies.opportunities import _get_provider_registry
    from app.database.session import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.user import User

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.freelancer_user_id == str(freelancer_user_id))
        )
        existing = result.scalar_one_or_none()
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Freelancer account is already linked to another user.",
            )

    # Calculate token expiry
    token_expires_at = None
    if payload.expires_in:
        token_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timezone.timedelta(seconds=payload.expires_in)

    # Store tokens
    await user_service.update_profile(
        current_user.id,
        freelancer_user_id=str(freelancer_user_id),
        freelancer_oauth_token=payload.oauth_token,
        freelancer_refresh_token=payload.refresh_token,
        freelancer_token_expires_at=token_expires_at,
        freelancer_connected_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )

    # Get username for response
    from freelancersdk.resources.users.users import get_user
    try:
        user_info = get_user(session, freelancer_user_id)
        freelancer_username = user_info.get("username", str(freelancer_user_id))
    except Exception:
        freelancer_username = str(freelancer_user_id)

    return FreelancerConnectResponse(
        freelancer_user_id=str(freelancer_user_id),
        freelancer_username=freelancer_username,
        connected_at=datetime.now(timezone.utc).replace(tzinfo=None),
        message="Freelancer account connected successfully.",
    )


@router.delete(
    "/disconnect",
    response_model=MessageResponse,
    summary="Disconnect Freelancer account",
)
async def disconnect_freelancer(
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """Disconnect the Freelancer account."""
    if not current_user.freelancer_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Freelancer account connected.",
        )

    await user_service.update_profile(
        current_user.id,
        freelancer_user_id=None,
        freelancer_oauth_token=None,
        freelancer_refresh_token=None,
        freelancer_token_expires_at=None,
        freelancer_connected_at=None,
    )

    return MessageResponse(message="Freelancer account disconnected successfully.")


@router.post(
    "/sync",
    response_model=FreelancerSyncResponse,
    summary="Sync latest projects from Freelancer",
)
async def sync_freelancer_projects(
    payload: FreelancerSyncRequest,
    current_user: CurrentUser,
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> FreelancerSyncResponse:
    """
    Sync latest projects from Freelancer.com.
    
    Fetches projects matching the query and imports them as opportunities.
    """
    if not current_user.freelancer_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Freelancer account not connected. Connect first.",
        )

    if not current_user.freelancer_oauth_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Freelancer token available. Reconnect account.",
        )

    # Check if token is expired and try to refresh
    if current_user.freelancer_token_expires_at:
        from datetime import datetime
        if datetime.now() >= current_user.freelancer_token_expires_at:
            # Try to refresh token
            if current_user.freelancer_refresh_token:
                await _refresh_freelancer_token(current_user, user_service)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Freelancer token expired. Please reconnect your account.",
                )

    result = await import_service.import_opportunities(
        user_id=current_user.id,
        platform="freelancer",
        max_results=payload.max_results,
    )

    return FreelancerSyncResponse(
        projects_synced=result.opportunities_found,
        projects_new=result.imported,
        projects_updated=result.updated,
        import_id=result.id,
    )


async def _refresh_freelancer_token(
    current_user: CurrentUser,
    user_service: UserService,
) -> None:
    """Refresh Freelancer OAuth token using refresh token."""
    from freelancersdk.session import Session
    from freelancersdk.exceptions import InvalidAuthTokenException
    import requests

    try:
        # Use the refresh token to get new access token
        token_url = "https://www.freelancer.com/api/users/0.1/self/access_token"
        response = requests.post(
            token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": current_user.freelancer_refresh_token,
            },
            headers={"Authorization": f"Bearer {current_user.freelancer_oauth_token}"},
        )
        if response.status_code == 200:
            data = response.json()
            new_expires_at = None
            if data.get("expires_in"):
                new_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timezone.timedelta(seconds=data["expires_in"])
            await user_service.update_profile(
                current_user.id,
                freelancer_oauth_token=data["access_token"],
                freelancer_refresh_token=data.get("refresh_token"),
                freelancer_token_expires_at=new_expires_at,
            )
    except Exception:
        # If refresh fails, clear tokens so user must reconnect
        await user_service.update_profile(
            current_user.id,
            freelancer_oauth_token=None,
            freelancer_refresh_token=None,
            freelancer_token_expires_at=None,
        )