"""
Freelancer integration endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Annotated
from pydantic import BaseModel, Field
from urllib.parse import urlencode

from app.core.config import get_settings
from app.core.limiter import limiter
from app.dependencies.auth import CurrentUser, get_user_service
from app.dependencies.opportunities import get_import_service
from app.schemas.auth import MessageResponse
from app.services.import_service import ImportService
from app.services.user_service import UserService

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class FreelancerConnectRequest(BaseModel):
    """Request to connect a Freelancer account."""
    oauth_token: str = Field(..., min_length=1, description="OAuth2 token from Freelancer.com")
    refresh_token: str | None = Field(default=None, description="Refresh token for OAuth2")
    expires_in: int | None = Field(default=None, ge=0, description="Token expiry in seconds")
    freelancer_user_id: str | None = Field(default=None, description="Freelancer user ID")


class FreelancerConnectResponse(BaseModel):
    """Response after connecting Freelancer account."""
    success: bool
    message: str
    freelancer_user_id: str | None = None
    connected_at: str | None = None


class FreelancerSyncRequest(BaseModel):
    """Request to sync Freelancer projects."""
    query: str = Field(default="", description="Search query for projects")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    filters: dict = Field(default_factory=dict, description="Additional filters")


class FreelancerSyncResponse(BaseModel):
    """Response after syncing Freelancer projects."""
    success: bool
    message: str
    opportunities_found: int
    opportunities_imported: int
    opportunities_updated: int
    duplicates_skipped: int


class FreelancerExchangeCodeRequest(BaseModel):
    """Request to exchange authorization code for access token."""
    code: str = Field(..., min_length=1, description="Authorization code from callback")
    state: str = Field(..., min_length=1, description="State parameter from callback")


@router.post(
    "/freelancer/connect",
    response_model=FreelancerConnectResponse,
    summary="Connect a Freelancer.com account",
)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def connect_freelancer(
    request: Request,
    payload: FreelancerConnectRequest,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> FreelancerConnectResponse:
    """
    Connect a Freelancer.com account using OAuth2 token.

    The token should be obtained from the Freelancer.com OAuth2 flow.
    See https://developers.freelancer.com for OAuth2 setup.
    """
    from datetime import datetime, timezone
    
    connected_at = datetime.now(timezone.utc)
    expires_at = None
    if payload.expires_in:
        expires_at = datetime.fromtimestamp(
            datetime.now().timestamp() + payload.expires_in, tz=timezone.utc
        )

    updated_user = await user_service.update_freelancer_profile(
        current_user.id,
        freelancer_user_id=payload.freelancer_user_id,
        freelancer_oauth_token=payload.oauth_token,
        freelancer_refresh_token=payload.refresh_token,
        freelancer_token_expires_at=expires_at,
        freelancer_connected_at=connected_at,
    )

    return FreelancerConnectResponse(
        success=True,
        message="Freelancer account connected successfully.",
        freelancer_user_id=updated_user.freelancer_user_id,
        connected_at=connected_at.isoformat(),
    )


@router.post(
    "/freelancer/disconnect",
    response_model=MessageResponse,
    summary="Disconnect Freelancer account",
)
async def disconnect_freelancer(
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """Disconnect the Freelancer.com account."""
    await user_service.update_freelancer_profile(
        current_user.id,
        freelancer_user_id=None,
        freelancer_oauth_token=None,
        freelancer_refresh_token=None,
        freelancer_token_expires_at=None,
        freelancer_connected_at=None,
    )
    return MessageResponse(message="Freelancer account disconnected successfully.")


@router.get(
    "/freelancer/status",
    response_model=dict,
    summary="Get Freelancer connection status",
)
async def freelancer_status(current_user: CurrentUser) -> dict:
    """Check if Freelancer account is connected."""
    return {
        "connected": current_user.freelancer_user_id is not None,
        "freelancer_user_id": current_user.freelancer_user_id,
        "connected_at": current_user.freelancer_connected_at.isoformat() if current_user.freelancer_connected_at else None,
        "token_expires_at": current_user.freelancer_token_expires_at.isoformat() if current_user.freelancer_token_expires_at else None,
    }


# --- OAuth2 Popup Flow ---

class FreelancerAuthUrlResponse(BaseModel):
    """Response with the Freelancer OAuth authorization URL."""
    auth_url: str
    state: str


@router.get(
    "/freelancer/auth-url",
    response_model=FreelancerAuthUrlResponse,
    summary="Get Freelancer OAuth authorization URL for popup",
)
async def freelancer_auth_url(
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> FreelancerAuthUrlResponse:
    """
    Generate the Freelancer OAuth2 authorization URL for the popup flow.
    
    The frontend should open this URL in a popup window and listen for the callback.
    """
    settings = get_settings()
    
    # Generate a secure state parameter
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Store state in user's session (we'll use freelancer_user_id field temporarily for state)
    # In production, use a proper session store or JWT
    await user_service.update_freelancer_profile(
        current_user.id,
        freelancer_user_id=state,  # temporarily store state here
    )
    
    # Build the authorization URL
    # Freelancer OAuth2: https://developers.freelancer.com/docs/authentication/oauth2
    auth_params = {
        "response_type": "code",
        "client_id": settings.FREELANCER_CLIENT_ID,
        "redirect_uri": f"{settings.FRONTEND_URL}/integrations/freelancer/callback",
        "scope": "basic profile projects",
        "state": state,
        "prompt": "consent",
    }
    
    auth_url = f"https://www.freelancer.com/oauth/authorize?{urlencode(auth_params)}"
    
    return FreelancerAuthUrlResponse(auth_url=auth_url, state=state)


@router.get(
    "/freelancer/callback",
    response_class=HTMLResponse,
    summary="Freelancer OAuth2 callback (popup target)",
)
async def freelancer_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
) -> HTMLResponse:
    """
    OAuth2 callback endpoint - target of the popup.
    
    This page receives the authorization code and sends it to the opener window
    via postMessage, then closes itself.
    """
    # Read the frontend URL from settings
    settings = get_settings()
    frontend_url = settings.FRONTEND_URL
    
    if error:
        error_msg = error_description or error
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authentication Failed</title></head>
        <body style="font-family: system-ui; padding: 2rem; text-align: center;">
            <h1 style="color: #dc2626;">Authentication Failed</h1>
            <p>{error_msg}</p>
            <button onclick="window.close()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Close Window</button>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    if not code or not state:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authentication Failed</title></head>
        <body style="font-family: system-ui; padding: 2rem; text-align: center;">
            <h1 style="color: #dc2626;">Authentication Failed</h1>
            <p>Missing authorization code or state parameter.</p>
            <button onclick="window.close()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Close Window</button>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    # Success - send the code to the opener window via postMessage
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Authentication Successful</title></head>
    <body style="font-family: system-ui; padding: 2rem; text-align: center;">
        <h1 style="color: #16a34a;">Authentication Successful</h1>
        <p>You can now close this window.</p>
        <script>
            // Send the authorization code to the opener window
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'FREELANCER_OAUTH_CALLBACK',
                    code: '{code}',
                    state: '{state}'
                }}, '{frontend_url}');
            }}
            // Close the popup after a short delay
            setTimeout(() => window.close(), 1000);
        </script>
        <button onclick="window.close()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Close Window</button>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post(
    "/freelancer/exchange-code",
    response_model=FreelancerConnectResponse,
    summary="Exchange authorization code for access token",
)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def freelancer_exchange_code(
    request: Request,
    payload: FreelancerExchangeCodeRequest,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> FreelancerConnectResponse:
    """
    Exchange the authorization code for an access token.
    
    Called by the frontend after receiving the code via postMessage from the popup.
    """
    from freelancersdk.session import Session
    from freelancersdk.resources.users.users import get_self_user_id
    from freelancersdk.resources.users.exceptions import UsersNotFoundException
    from freelancersdk.exceptions import AuthTokenNotSuppliedException
    import requests
    
    settings = get_settings()
    
    # Exchange code for access token
    token_url = "https://www.freelancer.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": payload.code,
        "redirect_uri": f"{settings.FRONTEND_URL}/integrations/freelancer/callback",
        "client_id": settings.FREELANCER_CLIENT_ID,
        "client_secret": settings.FREELANCER_CLIENT_SECRET,
    }
    
    response = requests.post(token_url, data=token_data)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {response.text}",
        )
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received from Freelancer",
        )
    
    # Verify the token by getting the user's Freelancer ID
    try:
        session = Session(oauth_token=access_token, url="https://www.freelancer.com")
        freelancer_user_id = get_self_user_id(session)
    except (UsersNotFoundException, AuthTokenNotSuppliedException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid access token: {str(e)}",
        )
    
    from datetime import datetime, timezone
    connected_at = datetime.now(timezone.utc)
    expires_at = None
    if expires_in:
        expires_at = datetime.fromtimestamp(
            datetime.now().timestamp() + expires_in, tz=timezone.utc
        )
    
    updated_user = await user_service.update_freelancer_profile(
        current_user.id,
        freelancer_user_id=str(freelancer_user_id),
        freelancer_oauth_token=access_token,
        freelancer_refresh_token=refresh_token,
        freelancer_token_expires_at=expires_at,
        freelancer_connected_at=connected_at,
    )
    
    return FreelancerConnectResponse(
        success=True,
        message="Freelancer account connected successfully.",
        freelancer_user_id=str(freelancer_user_id),
        connected_at=connected_at.isoformat(),
    )


# --- Sync endpoint

@router.post(
    "/freelancer/sync",
    response_model=FreelancerSyncResponse,
    summary="Sync latest projects from Freelancer.com",
)
@limiter.limit(get_settings().RATE_LIMIT_DEFAULT)
async def sync_freelancer(
    request: Request,
    payload: FreelancerSyncRequest,
    current_user: CurrentUser,
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> FreelancerSyncResponse:
    """
    Sync latest projects from Freelancer.com.
    
    Fetches projects matching the query and imports them as opportunities.
    Each opportunity is then scored by AI for relevance.
    """
    if not current_user.freelancer_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Freelancer account not connected. Connect your account first.",
        )

    if not current_user.freelancer_oauth_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Freelancer OAuth token missing. Please reconnect your account.",
        )

    # Import opportunities from Freelancer
    result = await import_service.import_opportunities(
        user_id=current_user.id,
        platform="freelancer",
        max_results=payload.limit,
    )

    return FreelancerSyncResponse(
        success=result.status in ("completed", "completed_with_errors"),
        message=f"Sync completed: {result.imported} new, {result.updated} updated, {result.skipped} skipped",
        opportunities_found=result.opportunities_found,
        opportunities_imported=result.imported,
        opportunities_updated=result.updated,
        duplicates_skipped=result.skipped,
    )


@router.post(
    "/freelancer/sync/live",
    response_model=dict,
    summary="Search live projects from Freelancer.com (without importing)",
)
@limiter.limit(get_settings().RATE_LIMIT_DEFAULT)
async def search_live_freelancer(
    request: Request,
    payload: FreelancerSyncRequest,
    current_user: CurrentUser,
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> dict:
    """
    Search live projects from Freelancer.com without importing.
    
    Useful for browsing available projects before deciding to import.
    """
    if not current_user.freelancer_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Freelancer account not connected.",
        )

    provider = import_service._registry.get("freelancer")
    if not provider:
        return {"items": [], "total": 0, "message": "Freelancer provider not configured"}

    try:
        opportunities = await provider.fetch_opportunities(
            user_id=current_user.id,
            query=payload.query,
            limit=payload.limit,
            offset=payload.offset,
            **payload.filters,
        )

        items = []
        for opp in opportunities:
            items.append({
                "external_id": opp.external_id,
                "platform": opp.platform,
                "title": opp.title,
                "description": opp.description,
                "url": opp.url,
                "project_type": opp.project_type,
                "experience_level": opp.experience_level,
                "duration": opp.duration,
                "budget_min": opp.budget_min,
                "budget_max": opp.budget_max,
                "budget_type": opp.budget_type,
                "currency": opp.currency,
                "skills": opp.skills,
                "category": opp.category,
                "subcategory": opp.subcategory,
                "country": opp.country,
                "client_rating": opp.client_rating,
                "client_reviews_count": opp.client_reviews_count,
                "client_payment_verified": opp.client_payment_verified,
                "client_total_hired": opp.client_total_hired,
                "is_remote": opp.is_remote,
                "is_negotiable": opp.is_negotiable,
                "posted_at": opp.posted_at.isoformat() if opp.posted_at else None,
                "deadline": opp.deadline.isoformat() if opp.deadline else None,
            })

        return {"items": items, "total": len(items)}
    except Exception as e:
        return {"items": [], "total": 0, "error": str(e)}