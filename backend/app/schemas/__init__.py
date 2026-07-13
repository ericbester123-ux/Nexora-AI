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
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.preferences import (
    AIPreferencesResponse,
    AIPreferencesUpdate,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from app.schemas.proposal import ProposalCreate, ProposalResponse, ProposalUpdate
from app.schemas.proposal_template import (
    ProposalTemplateCreate,
    ProposalTemplateResponse,
    ProposalTemplateUpdate,
)
from app.schemas.technology import TechnologyCreate, TechnologyResponse, TechnologyUpdate
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
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    "ClientCreate",
    "ClientResponse",
    "ClientUpdate",
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
    "ProposalCreate",
    "ProposalResponse",
    "ProposalUpdate",
    "ProposalTemplateCreate",
    "ProposalTemplateResponse",
    "ProposalTemplateUpdate",
    "TechnologyCreate",
    "TechnologyResponse",
    "TechnologyUpdate",
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
