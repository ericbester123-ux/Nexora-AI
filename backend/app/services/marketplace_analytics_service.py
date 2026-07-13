"""
MarketplaceAnalyticsService tracks sync and opportunity metrics per provider.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_account import MarketplaceAccount
from app.models.marketplace_sync_history import MarketplaceSyncHistory
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.repositories.marketplace_account_repository import MarketplaceAccountRepository
from app.repositories.marketplace_sync_history_repository import MarketplaceSyncHistoryRepository


class MarketplaceAnalyticsService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._account_repo = MarketplaceAccountRepository(session)
        self._sync_history_repo = MarketplaceSyncHistoryRepository(session)

    async def get_provider_stats(self, user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
        account = await self._account_repo.get_by_id(account_id)
        if not account or account.user_id != user_id:
            return {}

        # Count opportunities from this provider
        opp_count_result = await self._session.execute(
            select(func.count(Opportunity.id)).where(
                Opportunity.user_id == user_id,
                Opportunity.platform == account.provider,
            )
        )
        total_projects = opp_count_result.scalar() or 0

        # Count opportunities viewed (status != 'new')
        viewed_result = await self._session.execute(
            select(func.count(Opportunity.id)).where(
                Opportunity.user_id == user_id,
                Opportunity.platform == account.provider,
                Opportunity.status != "new",
            )
        )
        viewed_projects = viewed_result.scalar() or 0

        # Count proposals generated for opportunities from this provider
        proposals_result = await self._session.execute(
            select(func.count(Proposal.id)).where(
                Proposal.user_id == user_id,
                Proposal.opportunity_id.isnot(None),
            )
        )
        proposals_generated = proposals_result.scalar() or 0

        # Count proposals submitted
        submitted_result = await self._session.execute(
            select(func.count(Proposal.id)).where(
                Proposal.user_id == user_id,
                Proposal.status == "submitted",
            )
        )
        proposals_submitted = submitted_result.scalar() or 0

        # Count won proposals
        won_result = await self._session.execute(
            select(func.count(Proposal.id)).where(
                Proposal.user_id == user_id,
                Proposal.status == "won",
            )
        )
        projects_won = won_result.scalar() or 0

        # Count lost proposals
        lost_result = await self._session.execute(
            select(func.count(Proposal.id)).where(
                Proposal.user_id == user_id,
                Proposal.status == "lost",
            )
        )
        projects_lost = lost_result.scalar() or 0

        # Average bid
        avg_bid_result = await self._session.execute(
            select(func.avg(Proposal.bid_amount)).where(
                Proposal.user_id == user_id,
                Proposal.bid_amount.isnot(None),
            )
        )
        avg_bid = float(avg_bid_result.scalar() or 0)

        # Win rate
        total_decided = projects_won + projects_lost
        win_rate = (projects_won / total_decided * 100) if total_decided > 0 else 0

        # Sync count
        sync_count = await self._sync_history_repo.count_by_account_id(account_id)

        # Last sync
        last_sync = await self._sync_history_repo.get_latest_by_account_id(account_id)

        return {
            "provider": account.provider,
            "total_projects_imported": total_projects,
            "projects_viewed": viewed_projects,
            "proposals_generated": proposals_generated,
            "proposals_submitted": proposals_submitted,
            "projects_won": projects_won,
            "projects_lost": projects_lost,
            "win_rate": round(win_rate, 1),
            "average_bid_amount": round(avg_bid, 2),
            "total_syncs": sync_count,
            "last_sync_at": last_sync.completed_at.isoformat() if last_sync and last_sync.completed_at else None,
            "last_sync_status": last_sync.status if last_sync else None,
        }
