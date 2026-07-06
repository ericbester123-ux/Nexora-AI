"""
User preferences endpoints (project discovery / matching configuration).
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, get_user_preference_service
from app.schemas.preferences import UserPreferencesResponse, UserPreferencesUpdate
from app.services.preference_service import UserPreferenceService

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get(
    "",
    response_model=UserPreferencesResponse,
    summary="Get the current user's project-matching preferences",
)
async def get_preferences(
    current_user: CurrentUser,
    service: Annotated[UserPreferenceService, Depends(get_user_preference_service)],
) -> UserPreferencesResponse:
    pref = await service.get(current_user.id)
    return UserPreferencesResponse.model_validate(pref)


@router.put(
    "",
    response_model=UserPreferencesResponse,
    summary="Update the current user's project-matching preferences",
)
async def update_preferences(
    payload: UserPreferencesUpdate,
    current_user: CurrentUser,
    service: Annotated[UserPreferenceService, Depends(get_user_preference_service)],
) -> UserPreferencesResponse:
    pref = await service.update(current_user.id, payload)
    return UserPreferencesResponse.model_validate(pref)
