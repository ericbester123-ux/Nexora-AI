"""
Notification preferences endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, get_notification_preference_service
from app.schemas.preferences import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)
from app.services.preference_service import NotificationPreferenceService

router = APIRouter(prefix="/notification-preferences", tags=["Notification Preferences"])


@router.get(
    "",
    response_model=NotificationPreferencesResponse,
    summary="Get the current user's notification preferences",
)
async def get_notification_preferences(
    current_user: CurrentUser,
    service: Annotated[NotificationPreferenceService, Depends(get_notification_preference_service)],
) -> NotificationPreferencesResponse:
    pref = await service.get(current_user.id)
    return NotificationPreferencesResponse.model_validate(pref)


@router.put(
    "",
    response_model=NotificationPreferencesResponse,
    summary="Update the current user's notification preferences",
)
async def update_notification_preferences(
    payload: NotificationPreferencesUpdate,
    current_user: CurrentUser,
    service: Annotated[NotificationPreferenceService, Depends(get_notification_preference_service)],
) -> NotificationPreferencesResponse:
    pref = await service.update(current_user.id, payload)
    return NotificationPreferencesResponse.model_validate(pref)
