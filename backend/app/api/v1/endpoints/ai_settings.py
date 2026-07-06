"""
AI settings endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, get_ai_preference_service
from app.schemas.preferences import AIPreferencesResponse, AIPreferencesUpdate
from app.services.preference_service import AIPreferenceService

router = APIRouter(prefix="/ai-settings", tags=["AI Settings"])


@router.get(
    "",
    response_model=AIPreferencesResponse,
    summary="Get the current user's AI settings",
)
async def get_ai_settings(
    current_user: CurrentUser,
    service: Annotated[AIPreferenceService, Depends(get_ai_preference_service)],
) -> AIPreferencesResponse:
    pref = await service.get(current_user.id)
    return AIPreferencesResponse.model_validate(pref)


@router.put(
    "",
    response_model=AIPreferencesResponse,
    summary="Update the current user's AI settings",
)
async def update_ai_settings(
    payload: AIPreferencesUpdate,
    current_user: CurrentUser,
    service: Annotated[AIPreferenceService, Depends(get_ai_preference_service)],
) -> AIPreferencesResponse:
    pref = await service.update(current_user.id, payload)
    return AIPreferencesResponse.model_validate(pref)
