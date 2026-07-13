import uuid
from datetime import datetime, timezone

from app.core.exceptions import BadRequestError
from app.domain.events.opportunity_events import EventBus, ImportCompleted, OpportunityImported, OpportunitySkipped, OpportunityUpdated
from app.infrastructure.providers.base import NormalizedOpportunity
from app.infrastructure.providers.registry import ProviderRegistry
from app.models.import_history import ImportHistory
from app.repositories.import_history_repository import ImportHistoryRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.opportunity_service import OpportunityService


class ImportService:
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        opportunity_repository: OpportunityRepository,
        import_history_repository: ImportHistoryRepository,
        opportunity_service: OpportunityService,
        event_bus: EventBus,
    ):
        self._registry = provider_registry
        self._opportunity_repo = opportunity_repository
        self._import_history_repo = import_history_repository
        self._opportunity_service = opportunity_service
        self._event_bus = event_bus

    async def import_opportunities(
        self,
        user_id: uuid.UUID,
        platform: str,
        max_results: int | None = None,
    ) -> ImportHistory:
        provider = self._registry.get(platform)
        if provider is None:
            raise BadRequestError(f"Unsupported platform: {platform}")

        started_at = datetime.now(timezone.utc)
        import_record = await self._import_history_repo.create(
            user_id=user_id,
            platform=platform,
            started_at=started_at,
            status="in_progress",
        )

        try:
            raw_opportunities = await provider.fetch_opportunities(user_id)
            if max_results and len(raw_opportunities) > max_results:
                raw_opportunities = raw_opportunities[:max_results]

            imported_count = 0
            updated_count = 0
            skipped_count = 0
            failed_count = 0
            error_messages: list[str] = []

            for normalized in raw_opportunities:
                try:
                    result = await self._process_opportunity(user_id, normalized, import_record.id)
                    if result == "imported":
                        imported_count += 1
                    elif result == "updated":
                        updated_count += 1
                    else:
                        skipped_count += 1
                except Exception as exc:
                    failed_count += 1
                    error_messages.append(f"Failed to process opportunity '{normalized.title}': {exc}")

            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            import_record = await self._import_history_repo.update(
                import_record,
                completed_at=completed_at,
                duration_ms=duration_ms,
                opportunities_found=len(raw_opportunities),
                imported=imported_count,
                updated=updated_count,
                skipped=skipped_count,
                failed=failed_count,
                status="completed" if failed_count == 0 else "completed_with_errors",
                error_messages="\n".join(error_messages) if error_messages else None,
            )

            await self._event_bus.publish(
                ImportCompleted(
                    import_id=import_record.id,
                    user_id=user_id,
                    platform=platform,
                    imported=imported_count,
                    updated=updated_count,
                    skipped=skipped_count,
                    failed=failed_count,
                )
            )
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000
            import_record = await self._import_history_repo.update(
                import_record,
                completed_at=completed_at,
                duration_ms=duration_ms,
                status="failed",
                error_messages=str(exc),
            )

        return import_record

    async def _process_opportunity(
        self,
        user_id: uuid.UUID,
        normalized: NormalizedOpportunity,
        import_id: uuid.UUID,
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
                await self._event_bus.publish(
                    OpportunityUpdated(
                        opportunity_id=existing.id,
                        user_id=user_id,
                        platform=normalized.platform,
                        title=normalized.title,
                    )
                )
                return "updated"
            else:
                await self._event_bus.publish(
                    OpportunitySkipped(
                        platform=normalized.platform,
                        reason="duplicate",
                        external_id=normalized.external_id,
                    )
                )
                return "skipped"

        opportunity = await self._opportunity_service.create_opportunity(
            user_id=user_id,
            import_id=import_id,
            platform=normalized.platform,
            title=normalized.title,
            external_id=normalized.external_id,
            description=normalized.description,
            url=normalized.url,
            project_type=normalized.project_type,
            experience_level=normalized.experience_level,
            duration=normalized.duration,
            budget_min=normalized.budget_min,
            budget_max=normalized.budget_max,
            budget_type=normalized.budget_type,
            currency=normalized.currency,
            skills=normalized.skills,
            category=normalized.category,
            subcategory=normalized.subcategory,
            country=normalized.country,
            client_rating=normalized.client_rating,
            client_reviews_count=normalized.client_reviews_count,
            client_payment_verified=normalized.client_payment_verified,
            client_total_hired=normalized.client_total_hired,
            is_remote=normalized.is_remote,
            is_negotiable=normalized.is_negotiable,
            posted_at=normalized.posted_at,
            deadline=normalized.deadline,
        )
        await self._event_bus.publish(
            OpportunityImported(
                opportunity_id=opportunity.id,
                user_id=user_id,
                platform=normalized.platform,
                title=normalized.title,
            )
        )
        return "imported"
