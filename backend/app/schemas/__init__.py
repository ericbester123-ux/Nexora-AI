"""
Aggregates all Pydantic schemas for easy import.
"""

from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.preferences import (
    AIPreferencesResponse,
    AIPreferencesUpdate,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from app.schemas.user import (
    UserCreate,
    UserProfileUpdate,
    UserResponse,
    UserRole,
    UserUpdate,
)

__all__ = [
    "LoginRequest",
    "LogoutRequest",
    "MessageResponse",
    "PasswordChangeRequest",
    "RefreshRequest",
    "TokenResponse",
    "UserCreate",
    "UserProfileUpdate",
    "UserResponse",
    "UserRole",
    "UserUpdate",
    "UserPreferencesResponse",
    "UserPreferencesUpdate",
    "AIPreferencesResponse",
    "AIPreferencesUpdate",
    "NotificationPreferencesResponse",
    "NotificationPreferencesUpdate",
]
