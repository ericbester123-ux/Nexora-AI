"""
Aggregates all ORM models so that a single import
(`app.models`) registers the full metadata with
`Base.metadata` — this is required for Alembic's `--autogenerate` to detect
every table.
"""

from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.ai_preference import AIPreference
from app.models.notification_preference import NotificationPreference

__all__ = ["RevokedToken", "User", "UserPreference", "AIPreference", "NotificationPreference"]
