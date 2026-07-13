"""
Authentication endpoints: register, login, logout, refresh, current user,
and password change.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from app.services.auth_service import AuthService
from app.dependencies.auth import CurrentBearerCredentials, CurrentUser, get_auth_service
from app.core.limiter import limiter
from app.core.config import get_settings
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordChangeRequest,
    RefreshRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request,
    payload: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> RegisterResponse:
    """
    Create a new user account.

    Returns **409 Conflict** if the email is already registered.
    The account is created but not activated - user must complete subscription
    before being able to log in.
    """
    user = await auth_service.register(payload)
    return RegisterResponse(message="Account created successfully. Please complete your subscription to activate your account.", email=user.email)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain a token pair",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Authenticate with email and password.

    Returns **401 Unauthorized** for invalid credentials or a deactivated
    account. The error message is intentionally generic to avoid leaking
    which emails are registered.
    """
    _user, tokens = await auth_service.authenticate(payload.email, payload.password)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new token pair",
)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def refresh(
    request: Request,
    payload: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Exchange a valid, unexpired refresh token for a brand new access/refresh
    token pair (refresh token rotation).
    """
    return await auth_service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the current access token and optional refresh token",
)
async def logout(
    payload: LogoutRequest,
    credentials: CurrentBearerCredentials,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """
    Log out the authenticated user by revoking the presented bearer token.

    Passing the current refresh token also revokes it immediately.
    """
    await auth_service.logout(credentials.credentials, payload.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
)
async def current_user(current_user: CurrentUser) -> UserResponse:
    """Return the authenticated user's public profile."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/password",
    response_model=MessageResponse,
    summary="Change the current authenticated user's password",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def change_password(
    request: Request,
    payload: PasswordChangeRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Change the authenticated user's password after verifying the old one."""
    await auth_service.change_password(
        current_user.id,
        payload.current_password,
        payload.new_password,
    )
    return MessageResponse(message="Password changed successfully.")
