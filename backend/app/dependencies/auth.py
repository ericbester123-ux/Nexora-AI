"""
FastAPI dependency providers.

Centralizes construction of repositories and services so endpoints only
need to declare a single `Depends(...)` and never instantiate concrete
classes themselves — this is our dependency-injection boundary.
"""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import TokenType, decode_token
from app.database.session import get_db
from app.models.user import User
from app.infrastructure.llm import LLMProvider
from app.infrastructure.llm import get_llm_provider as create_llm_provider
from app.repositories.ai_usage_log_repository import AIUsageLogRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.preference_repository import (
    AIPreferenceRepository,
    NotificationPreferenceRepository,
    UserPreferenceRepository,
)
from app.repositories.proposal_note_repository import ProposalNoteRepository
from app.repositories.proposal_repository import ProposalRepository
from app.repositories.proposal_status_history_repository import (
    ProposalStatusHistoryRepository,
)
from app.repositories.proposal_template_repository import ProposalTemplateRepository
from app.repositories.proposal_version_repository import ProposalVersionRepository
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.technology_repository import TechnologyRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.client_service import ClientService
from app.services.preference_service import (
    AIPreferenceService,
    NotificationPreferenceService,
    UserPreferenceService,
)
from app.services.proposal_generation_service import ProposalGenerationService
from app.services.proposal_note_service import ProposalNoteService
from app.services.proposal_review_service import ProposalReviewService
from app.services.proposal_service import ProposalService
from app.services.proposal_template_service import ProposalTemplateService
from app.services.proposal_evaluator import ProposalEvaluator
from app.services.proposal_improver import ProposalImprover
from app.services.prompt_builder import PromptBuilder
from app.services.scoring_service import ScoringService
from app.services.technology_service import TechnologyService
from app.repositories.project_repository import ProjectRepository
from app.services.project_service import ProjectService
from app.services.user_service import UserService

_bearer_scheme = HTTPBearer(auto_error=False)


# --- Repository dependencies ---


def get_user_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(session)


def get_revoked_token_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RevokedTokenRepository:
    return RevokedTokenRepository(session)


def get_user_preference_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserPreferenceRepository:
    return UserPreferenceRepository(session)


def get_ai_preference_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AIPreferenceRepository:
    return AIPreferenceRepository(session)


def get_notification_preference_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferenceRepository:
    return NotificationPreferenceRepository(session)


def get_proposal_template_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProposalTemplateRepository:
    return ProposalTemplateRepository(session)


def get_proposal_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProposalRepository:
    return ProposalRepository(session)


# --- Service dependencies ---


def get_category_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryRepository:
    return CategoryRepository(session)


def get_category_service(
    category_repository: Annotated[CategoryRepository, Depends(get_category_repository)],
) -> CategoryService:
    return CategoryService(category_repository)


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    revoked_token_repository: Annotated[
        RevokedTokenRepository,
        Depends(get_revoked_token_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
        revoked_token_repository=revoked_token_repository,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repository)


def get_proposal_template_service(
    repo: Annotated[ProposalTemplateRepository, Depends(get_proposal_template_repository)],
) -> ProposalTemplateService:
    return ProposalTemplateService(repo)


def get_proposal_service(
    proposal_repository: Annotated[ProposalRepository, Depends(get_proposal_repository)],
) -> ProposalService:
    return ProposalService(repository=proposal_repository)


def get_project_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectRepository:
    return ProjectRepository(session)


def get_project_service(
    project_repository: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> ProjectService:
    return ProjectService(project_repository)


def get_user_preference_service(
    preference_repository: Annotated[UserPreferenceRepository, Depends(get_user_preference_repository)],
) -> UserPreferenceService:
    return UserPreferenceService(preference_repository)


def get_ai_preference_service(
    ai_preference_repository: Annotated[AIPreferenceRepository, Depends(get_ai_preference_repository)],
) -> AIPreferenceService:
    return AIPreferenceService(ai_preference_repository)


def get_notification_preference_service(
    notification_preference_repository: Annotated[
        NotificationPreferenceRepository,
        Depends(get_notification_preference_repository),
    ],
) -> NotificationPreferenceService:
    return NotificationPreferenceService(notification_preference_repository)


def get_technology_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TechnologyRepository:
    return TechnologyRepository(session)


def get_technology_service(
    technology_repository: Annotated[TechnologyRepository, Depends(get_technology_repository)],
) -> TechnologyService:
    return TechnologyService(repository=technology_repository)


def get_client_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ClientRepository:
    return ClientRepository(session)


def get_client_service(
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
) -> ClientService:
    return ClientService(client_repository)


# --- LLM / Proposal Generation dependencies ---


def get_opportunity_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OpportunityRepository:
    return OpportunityRepository(session)


def get_proposal_version_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProposalVersionRepository:
    return ProposalVersionRepository(session)


def get_ai_usage_log_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AIUsageLogRepository:
    return AIUsageLogRepository(session)


def get_llm_provider() -> LLMProvider:
    return create_llm_provider()


def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


def get_scoring_service(
    opportunity_repository: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
) -> ScoringService:
    from app.services.opportunity_service import OpportunityService

    opp_service = OpportunityService(opportunity_repository)
    return ScoringService(opp_service)


def get_proposal_generation_service(
    proposal_repository: Annotated[ProposalRepository, Depends(get_proposal_repository)],
    proposal_version_repository: Annotated[ProposalVersionRepository, Depends(get_proposal_version_repository)],
    ai_usage_log_repository: Annotated[AIUsageLogRepository, Depends(get_ai_usage_log_repository)],
    opportunity_repository: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
    proposal_template_repository: Annotated[ProposalTemplateRepository, Depends(get_proposal_template_repository)],
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    llm_provider: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> ProposalGenerationService:
    return ProposalGenerationService(
        proposal_repository=proposal_repository,
        proposal_version_repository=proposal_version_repository,
        ai_usage_log_repository=ai_usage_log_repository,
        opportunity_repository=opportunity_repository,
        proposal_template_repository=proposal_template_repository,
        scoring_service=scoring_service,
        llm_provider=llm_provider,
    )


# --- Proposal Improver / Evaluator ---


def get_proposal_improver(
    proposal_repository: Annotated[ProposalRepository, Depends(get_proposal_repository)],
    proposal_version_repository: Annotated[ProposalVersionRepository, Depends(get_proposal_version_repository)],
    ai_usage_log_repository: Annotated[AIUsageLogRepository, Depends(get_ai_usage_log_repository)],
    opportunity_repository: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
    llm_provider: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> ProposalImprover:
    return ProposalImprover(
        proposal_repository=proposal_repository,
        proposal_version_repository=proposal_version_repository,
        ai_usage_log_repository=ai_usage_log_repository,
        opportunity_repository=opportunity_repository,
        llm_provider=llm_provider,
    )


def get_proposal_evaluator(
    ai_usage_log_repository: Annotated[AIUsageLogRepository, Depends(get_ai_usage_log_repository)],
    opportunity_repository: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
    llm_provider: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> ProposalEvaluator:
    return ProposalEvaluator(
        ai_usage_log_repository=ai_usage_log_repository,
        opportunity_repository=opportunity_repository,
        llm_provider=llm_provider,
    )


# --- Proposal Review dependencies ---


def get_proposal_note_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProposalNoteRepository:
    return ProposalNoteRepository(session)


def get_audit_log_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuditLogRepository:
    return AuditLogRepository(session)


def get_proposal_status_history_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProposalStatusHistoryRepository:
    return ProposalStatusHistoryRepository(session)


def get_audit_service(
    audit_log_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AuditService:
    return AuditService(audit_log_repository)


def get_proposal_note_service(
    proposal_note_repository: Annotated[ProposalNoteRepository, Depends(get_proposal_note_repository)],
) -> ProposalNoteService:
    return ProposalNoteService(proposal_note_repository)


def get_proposal_review_service(
    proposal_repository: Annotated[ProposalRepository, Depends(get_proposal_repository)],
    proposal_version_repository: Annotated[ProposalVersionRepository, Depends(get_proposal_version_repository)],
    proposal_status_history_repository: Annotated[
        ProposalStatusHistoryRepository, Depends(get_proposal_status_history_repository)
    ],
    audit_log_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    opportunity_repository: Annotated[OpportunityRepository, Depends(get_opportunity_repository)],
) -> ProposalReviewService:
    return ProposalReviewService(
        proposal_repository=proposal_repository,
        proposal_version_repository=proposal_version_repository,
        proposal_status_history_repository=proposal_status_history_repository,
        audit_log_repository=audit_log_repository,
        opportunity_repository=opportunity_repository,
    )


# --- Auth resolvers ---


async def get_current_bearer_credentials(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> HTTPAuthorizationCredentials:
    """Return bearer credentials or raise the standard authentication error."""
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials.")
    return credentials


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_current_bearer_credentials)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    revoked_token_repository: Annotated[
        RevokedTokenRepository,
        Depends(get_revoked_token_repository),
    ],
) -> User:
    """
    Resolve the authenticated user from the `Authorization: Bearer <token>`
    header. Used as a dependency on any endpoint that requires
    authentication.

    Raises:
        AuthenticationError: if the header is missing, the token is
            invalid/expired, or the token is not an access token.
        NotFoundError: if the token is valid but the user no longer exists.
    """
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials.")

    payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    if await revoked_token_repository.exists(payload.jti):
        raise AuthenticationError("Token has been revoked.")

    user = await user_repository.get_by_id(uuid.UUID(payload.sub))
    if user is None:
        raise NotFoundError("The account associated with this token no longer exists.")
    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    return user


CurrentBearerCredentials = Annotated[
    HTTPAuthorizationCredentials,
    Depends(get_current_bearer_credentials),
]
CurrentUser = Annotated[User, Depends(get_current_user)]
