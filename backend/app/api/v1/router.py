"""
Aggregates all v1 endpoint routers under a single APIRouter.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import ai_settings, auth, notification_preferences, preferences, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(preferences.router)
api_router.include_router(ai_settings.router)
api_router.include_router(notification_preferences.router)
