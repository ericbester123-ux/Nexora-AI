"""
User profile endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.config import get_settings
from app.core.limiter import limiter
from app.dependencies.auth import CurrentUser, get_auth_service, get_user_service
from app.schemas.auth import MessageResponse, PasswordChangeRequest
from app.schemas.user import UserProfileUpdate, UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user's profile",
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update the current authenticated user's profile",
)
async def update_me(
    payload: UserProfileUpdate,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    updated = await user_service.update_profile(current_user.id, payload)
    return UserResponse.model_validate(updated)


@router.put(
    "/change-password",
    response_model=MessageResponse,
    summary="Change the current authenticated user's password",
)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def change_password(
    request: Request,
    payload: PasswordChangeRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    await auth_service.change_password(
        current_user.id,
        payload.current_password,
        payload.new_password,
    )
    return MessageResponse(message="Password changed successfully.")
