"""
Aggregates all ORM models so that a single import
(`app.models`) registers the full metadata with
`Base.metadata` — this is required for Alembic's `--autogenerate` to detect
every table.
"""

from app.models.revoked_token import RevokedToken
from app.models.technology import Technology
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.ai_preference import AIPreference
from app.models.notification_preference import NotificationPreference
from app.models.project import Project, ProjectCategoryLink, ProjectTechnology
from app.models.project_category import ProjectCategory
from app.models.client import Client
from app.models.proposal import Proposal
from app.models.proposal_template import ProposalTemplate
from app.models.opportunity import Opportunity
from app.models.import_history import ImportHistory
from app.models.proposal_version import ProposalVersion
from app.models.ai_usage_log import AIUsageLog
from app.models.proposal_note import ProposalNote
from app.models.audit_log import AuditLog
from app.models.marketplace_account import MarketplaceAccount
from app.models.marketplace_token import MarketplaceToken
from app.models.marketplace_sync_history import MarketplaceSyncHistory
from app.models.proposal_status_history import ProposalStatusHistory

__all__ = ["Proposal", "RevokedToken", "Technology", "User", "UserPreference", "AIPreference", "NotificationPreference", "Project", "ProjectCategoryLink", "ProjectTechnology", "ProjectCategory", "Client", "ProposalTemplate", "Opportunity", "ImportHistory", "ProposalVersion", "AIUsageLog", "ProposalNote", "AuditLog", "ProposalStatusHistory", "MarketplaceAccount", "MarketplaceToken", "MarketplaceSyncHistory"]
