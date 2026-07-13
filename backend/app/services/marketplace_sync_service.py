"""
MarketplaceSyncService handles syncing projects from connected marketplace accounts.
"""

import uuid
from datetime import datetime, timezone

from app.core.exceptions import BadRequestError, NotFoundError
from app.infrastructure.providers.base import BaseOpportunityProvider
from app.infrastructure.providers.marketplace_base import MarketplaceProvider
from app.models.marketplace_account import MarketplaceAccount
from app.repositories.marketplace_account_repository import MarketplaceAccountRepository
from app.repositories.marketplace_sync_history_repository import MarketplaceSyncHistoryRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.import_history_repository import ImportHistoryRepository
from app.services.opportunity_service import OpportunityService
from app.services.marketplace_auth_service import MarketplaceAuthService
from app.core.security import decrypt_token


class MarketplaceSyncService:
    def __init__(
        self,
        account_repo: MarketplaceAccountRepository,
        sync_history_repo: MarketplaceSyncHistoryRepository,
        opportunity_repo: OpportunityRepository,
        import_history_repo: ImportHistoryRepository,
        opportunity_service: OpportunityService,
        auth_service: MarketplaceAuthService,
    ):
        self._account_repo = account_repo
        self._sync_history_repo = sync_history_repo
        self._opportunity_repo = opportunity_repo
        self._import_history_repo = import_history_repo
        self._opportunity_service = opportunity_service
        self._auth_service = auth_service

    async def sync_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        provider: BaseOpportunityProvider,
        marketplace_provider: MarketplaceProvider | None = None,
        max_results: int = 50,
    ) -> dict:
        account = await self._account_repo.get_by_id(account_id)
        if not account or account.user_id != user_id or not account.is_active:
            raise NotFoundError("Account not found")

        # Get access token
        access_token = await self._auth_service.get_provider_token(account_id)
        if not access_token:
            raise BadRequestError("No valid access token. Please reconnect your account.")

        # Initialize provider with token if needed
        if hasattr(provider, "_init_session"):
            provider._init_session(access_token)

        # Create sync history record
        started_at = datetime.now(timezone.utc)
        sync_record = await self._sync_history_repo.create(
            account_id=account_id,
            status="in_progress",
            started_at=started_at,
        )

        # Update account sync status
        await self._account_repo.update(account, sync_status="syncing")

        try:
            # Fetch opportunities from provider
            raw_opportunities = await provider.fetch_opportunities(
                user_id=user_id,
                limit=max_results,
            )

            if max_results and len(raw_opportunities) > max_results:
                raw_opportunities = raw_opportunities[:max_results]

            imported = 0
            updated = 0
            skipped = 0
            failed = 0

            # Try to auto-refresh token if we get auth errors
            for normalized in raw_opportunities:
                try:
                    result = await self._process_opportunity(user_id, normalized, account_id)
                    if result == "imported":
                        imported += 1
                    elif result == "updated":
                        updated += 1
                    else:
                        skipped += 1
                except Exception:
                    failed += 1

            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            sync_status = "completed" if failed == 0 else "completed_with_errors"

            # Update sync history record
            await self._sync_history_repo.update(
                sync_record,
                status=sync_status,
                completed_at=completed_at,
                duration_ms=duration_ms,
                projects_found=len(raw_opportunities),
                projects_imported=imported,
                projects_updated=updated,
                projects_skipped=skipped,
                projects_failed=failed,
            )

            # Update account sync status
            await self._account_repo.update(
                account,
                last_sync_at=completed_at,
                sync_status="healthy" if sync_status == "completed" else "error",
                sync_error_message=None if sync_status == "completed" else f"{failed} projects failed",
            )

            return {
                "account_id": str(account_id),
                "status": sync_status,
                "projects_found": len(raw_opportunities),
                "projects_imported": imported,
                "projects_updated": updated,
                "projects_skipped": skipped,
                "projects_failed": failed,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            await self._sync_history_repo.update(
                sync_record,
                status="failed",
                completed_at=completed_at,
                duration_ms=duration_ms,
                error_message=str(e),
            )

            await self._account_repo.update(
                account,
                last_sync_at=completed_at,
                sync_status="error",
                sync_error_message=str(e),
            )

            raise BadRequestError(f"Sync failed: {str(e)}")

    async def _process_opportunity(
        self,
        user_id: uuid.UUID,
        normalized,
        account_id: uuid.UUID,
    ) -> str:
        existing = None
        if normalized.external_id:
            existing = await self._opportunity_repo.get_by_platform_external(
                normalized.platform, normalized.external_id
            )

        if existing is None:
            content_hash = self._opportunity_service._compute_content_hash(
                normalized.title, normalized.description, normalized.budget_max, normalized.country
            )
            existing = await self._opportunity_repo.get_by_content_hash(content_hash, user_id)

        if existing:
            was_updated = False
            for field, value in {
                "budget_min": normalized.budget_min,
                "budget_max": normalized.budget_max,
                "client_rating": normalized.client_rating,
                "client_reviews_count": normalized.client_reviews_count,
                "client_payment_verified": normalized.client_payment_verified,
                "client_total_hired": normalized.client_total_hired,
                "deadline": normalized.deadline,
                "description": normalized.description,
            }.items():
                if value is not None and getattr(existing, field) != value:
                    setattr(existing, field, value)
                    was_updated = True

            if was_updated:
                await self._opportunity_repo.update(existing)
                return "updated"
            return "skipped"

        # Create the opportunity
        import_id = None  # Will use a sync-based import record in production

        opportunity_data = {
            "user_id": user_id,
            "import_id": import_id,
            "platform": normalized.platform,
            "title": normalized.title,
            "external_id": normalized.external_id,
            "description": normalized.description,
            "url": normalized.url,
            "project_type": normalized.project_type,
            "experience_level": normalized.experience_level,
            "duration": normalized.duration,
            "budget_min": normalized.budget_min,
            "budget_max": normalized.budget_max,
            "budget_type": normalized.budget_type,
            "currency": normalized.currency,
            "skills": normalized.skills,
            "category": normalized.category,
            "subcategory": normalized.subcategory,
            "country": normalized.country,
            "client_rating": normalized.client_rating,
            "client_reviews_count": normalized.client_reviews_count,
            "client_payment_verified": normalized.client_payment_verified,
            "client_total_hired": normalized.client_total_hired,
            "is_remote": normalized.is_remote,
            "is_negotiable": normalized.is_negotiable,
            "posted_at": normalized.posted_at,
            "deadline": normalized.deadline,
        }

        # Remove None values for optional fields
        opportunity_data = {k: v for k, v in opportunity_data.items() if v is not None}

        await self._opportunity_service.create_opportunity(**opportunity_data)
        return "imported"

    async def get_sync_history(self, user_id: uuid.UUID, account_id: uuid.UUID, limit: int = 20) -> list[dict]:
        account = await self._account_repo.get_by_id(account_id)
        if not account or account.user_id != user_id:
            raise NotFoundError("Account not found")

        history = await self._sync_history_repo.get_by_account_id(account_id, limit=limit)
        return [
            {
                "id": str(h.id),
                "status": h.status,
                "started_at": h.started_at.isoformat() if h.started_at else None,
                "completed_at": h.completed_at.isoformat() if h.completed_at else None,
                "duration_ms": h.duration_ms,
                "projects_found": h.projects_found,
                "projects_imported": h.projects_imported,
                "projects_updated": h.projects_updated,
                "projects_skipped": h.projects_skipped,
                "projects_failed": h.projects_failed,
                "error_message": h.error_message,
            }
            for h in history
        ]

    async def get_all_sync_status(self, user_id: uuid.UUID) -> list[dict]:
        accounts = await self._account_repo.get_by_user_id(user_id)
        return [
            {
                "account_id": str(a.id),
                "provider": a.provider,
                "sync_status": a.sync_status,
                "last_sync_at": a.last_sync_at.isoformat() if a.last_sync_at else None,
                "sync_error_message": a.sync_error_message,
            }
            for a in accounts
        ]
