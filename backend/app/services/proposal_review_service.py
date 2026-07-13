"""
Proposal review service — status transitions, editing, rollback,
comparison, and submission readiness validation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import BadRequestError, NotFoundError, ValidationAppError
from app.models.proposal import Proposal
from app.models.proposal_version import ProposalVersion
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.proposal_repository import ProposalRepository
from app.repositories.proposal_status_history_repository import (
    ProposalStatusHistoryRepository,
)
from app.repositories.proposal_version_repository import ProposalVersionRepository

VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"under_review", "archived", "ai_generated"},
    "ai_generated": {"awaiting_approval", "draft", "archived"},
    "awaiting_approval": {"approved", "rejected"},
    "approved": {"ready_to_submit", "queued", "draft"},
    "rejected": {"draft", "archived"},
    "queued": {"submitted", "draft"},
    "under_review": {"edited", "ready_to_submit"},
    "edited": {"under_review", "ready_to_submit"},
    "ready_to_submit": {"submitted", "under_review"},
    "submitted": {"won", "lost"},
    "won": set(),
    "lost": set(),
    "archived": {"draft"},
}

COMPARISON_SECTIONS = [
    "cover_letter",
    "executive_summary",
    "why_good_fit",
    "relevant_experience",
    "bid_amount",
    "estimated_duration",
    "milestones",
    "risk_notes",
    "confidence_explanation",
    "proposal_summary",
]


class ProposalReviewService:
    def __init__(
        self,
        proposal_repository: ProposalRepository,
        proposal_version_repository: ProposalVersionRepository,
        proposal_status_history_repository: ProposalStatusHistoryRepository,
        audit_log_repository: AuditLogRepository,
        opportunity_repository: OpportunityRepository,
    ):
        self._proposal_repo = proposal_repository
        self._version_repo = proposal_version_repository
        self._status_history_repo = proposal_status_history_repository
        self._audit_repo = audit_log_repository
        self._opp_repo = opportunity_repository

    # --- Status transitions ---

    async def transition_status(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID, to_status: str
    ) -> Proposal:
        proposal = await self._assert_ownership(proposal_id, user_id)
        from_status = proposal.status

        allowed = VALID_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise BadRequestError(
                f"Cannot transition from '{from_status}' to '{to_status}'. "
                f"Allowed transitions: {', '.join(sorted(allowed)) or 'none'}"
            )

        proposal = await self._proposal_repo.update(proposal, status=to_status)

        await self._status_history_repo.create(
            proposal_id=proposal_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=user_id,
        )

        await self._audit_repo.create(
            proposal_id=proposal_id,
            user_id=user_id,
            action="status_change",
            details=f"Status changed from '{from_status}' to '{to_status}'",
        )

        return proposal

    async def review(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Proposal:
        return await self.transition_status(proposal_id, user_id, "under_review")

    async def mark_ready(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        proposal = await self._assert_ownership(proposal_id, user_id)
        errors = await self.validate_readiness(proposal)
        if errors:
            raise ValidationAppError(
                "Proposal is not ready to submit: " + "; ".join(errors)
            )
        return await self.transition_status(proposal_id, user_id, "ready_to_submit")

    async def mark_submitted(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        proposal = await self.transition_status(proposal_id, user_id, "submitted")
        return await self._proposal_repo.update(
            proposal, submitted_at=datetime.now(timezone.utc)
        )

    async def archive(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        return await self.transition_status(proposal_id, user_id, "archived")

    async def request_approval(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        return await self.transition_status(proposal_id, user_id, "awaiting_approval")

    async def approve(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        proposal = await self.transition_status(proposal_id, user_id, "approved")
        return await self._proposal_repo.update(
            proposal,
            human_approved_at=datetime.now(timezone.utc),
            human_approved_by=user_id,
        )

    async def reject(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID, reason: str | None = None
    ) -> Proposal:
        proposal = await self.transition_status(proposal_id, user_id, "rejected")
        update = {"rejection_reason": reason} if reason else {}
        if update:
            proposal = await self._proposal_repo.update(proposal, **update)
        return proposal

    async def queue(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        return await self.transition_status(proposal_id, user_id, "queued")

    # --- Readiness validation ---

    async def validate_readiness(self, proposal: Proposal) -> list[str]:
        errors: list[str] = []

        if not proposal.cover_letter or not proposal.cover_letter.strip():
            errors.append("Cover letter is required.")

        if proposal.bid_amount is None:
            errors.append("Bid amount is required.")

        if not proposal.estimated_duration:
            errors.append("Delivery estimate is required.")

        if proposal.project_id:
            opp = await self._opp_repo.get_by_id(proposal.project_id)
            if opp and opp.status == "closed":
                errors.append("The associated opportunity is no longer open.")

        return errors

    # --- Editing ---

    async def edit_proposal(
        self,
        proposal_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        title: Optional[str] = None,
        cover_letter: Optional[str] = None,
        executive_summary: Optional[str] = None,
        why_good_fit: Optional[str] = None,
        relevant_experience: Optional[str] = None,
        bid_amount: Optional[float] = None,
        bid_type: Optional[str] = None,
        estimated_duration: Optional[str] = None,
        milestones: Optional[str] = None,
        risk_notes: Optional[str] = None,
        confidence_explanation: Optional[str] = None,
        proposal_summary: Optional[str] = None,
        change_summary: Optional[str] = None,
    ) -> tuple[Proposal, ProposalVersion]:
        proposal = await self._assert_ownership(proposal_id, user_id)

        update_fields: dict = {}
        if title is not None:
            update_fields["title"] = title
        if cover_letter is not None:
            update_fields["cover_letter"] = cover_letter
        if bid_amount is not None:
            update_fields["bid_amount"] = bid_amount
        if bid_type is not None:
            update_fields["bid_type"] = bid_type
        if estimated_duration is not None:
            update_fields["estimated_duration"] = estimated_duration

        if update_fields:
            proposal = await self._proposal_repo.update(proposal, **update_fields)

        last_version = await self._version_repo.get_latest_version_number(proposal_id)
        version_number = last_version + 1

        version = await self._version_repo.create(
            proposal_id=proposal_id,
            version_number=version_number,
            created_by="user",
            change_summary=change_summary or "User edit",
            cover_letter=cover_letter,
            executive_summary=executive_summary,
            why_good_fit=why_good_fit,
            relevant_experience=relevant_experience,
            bid_amount=bid_amount,
            bid_type=bid_type,
            estimated_duration=estimated_duration,
            milestones=milestones,
            risk_notes=risk_notes,
            confidence_explanation=confidence_explanation,
            proposal_summary=proposal_summary,
        )

        await self._audit_repo.create(
            proposal_id=proposal_id,
            user_id=user_id,
            action="user_edit",
            details=f"Created version {version_number}: {change_summary or 'User edit'}",
        )

        if proposal.status in ("draft", "under_review"):
            proposal = await self._proposal_repo.update(proposal, status="edited")
            await self._status_history_repo.create(
                proposal_id=proposal_id,
                from_status=proposal.status,
                to_status="edited",
                changed_by=user_id,
            )

        return proposal, version

    # --- Rollback ---

    async def rollback(
        self,
        proposal_id: uuid.UUID,
        user_id: uuid.UUID,
        version_id: uuid.UUID,
        change_summary: Optional[str] = None,
    ) -> tuple[Proposal, ProposalVersion]:
        target = await self._version_repo.get_by_id_and_proposal_id(
            version_id, proposal_id
        )
        if target is None:
            raise NotFoundError("Version not found for this proposal.")

        current = await self._assert_ownership(proposal_id, user_id)

        update_fields = {}
        for field in COMPARISON_SECTIONS:
            value = getattr(target, field, None)
            if field == "bid_amount":
                update_fields[field] = value
            elif value is not None:
                update_fields[field] = value

        proposal_update = {
            k: v
            for k, v in {
                "cover_letter": target.cover_letter,
                "bid_amount": target.bid_amount,
                "bid_type": target.bid_type,
                "estimated_duration": target.estimated_duration,
            }.items()
            if v is not None
        }
        if proposal_update:
            current = await self._proposal_repo.update(current, **proposal_update)

        last_version = await self._version_repo.get_latest_version_number(proposal_id)
        version_number = last_version + 1

        version = await self._version_repo.create(
            proposal_id=proposal_id,
            version_number=version_number,
            created_by="user",
            change_summary=change_summary or f"Rollback to version {target.version_number}",
            cover_letter=target.cover_letter,
            executive_summary=target.executive_summary,
            why_good_fit=target.why_good_fit,
            relevant_experience=target.relevant_experience,
            bid_amount=target.bid_amount,
            estimated_duration=target.estimated_duration,
            milestones=target.milestones,
            risk_notes=target.risk_notes,
            confidence_explanation=target.confidence_explanation,
            proposal_summary=target.proposal_summary,
        )

        await self._audit_repo.create(
            proposal_id=proposal_id,
            user_id=user_id,
            action="rollback",
            details=f"Rolled back to version {target.version_number} (new version {version_number})",
        )

        return current, version

    # --- Comparison ---

    async def compare_versions(
        self,
        proposal_id: uuid.UUID,
        user_id: uuid.UUID,
        version_id_a: uuid.UUID,
        version_id_b: uuid.UUID,
    ) -> dict:
        await self._assert_ownership(proposal_id, user_id)

        v_a = await self._version_repo.get_by_id_and_proposal_id(
            version_id_a, proposal_id
        )
        v_b = await self._version_repo.get_by_id_and_proposal_id(
            version_id_b, proposal_id
        )

        if v_a is None or v_b is None:
            raise NotFoundError("One or both versions not found.")

        section_diffs = []
        changed_count = 0
        added_count = 0
        removed_count = 0
        modified_count = 0
        total_added_words = 0
        total_removed_words = 0

        for section in COMPARISON_SECTIONS:
            old_val = self._get_section_value(v_a, section)
            new_val = self._get_section_value(v_b, section)

            old_str = str(old_val) if old_val is not None else ""
            new_str = str(new_val) if new_val is not None else ""

            if old_str == "" and new_str == "":
                change_type = "unchanged"
            elif old_str == "" and new_str != "":
                change_type = "added"
                added_count += 1
                total_added_words += len(new_str.split())
            elif old_str != "" and new_str == "":
                change_type = "removed"
                removed_count += 1
                total_removed_words += len(old_str.split())
            elif old_str != new_str:
                change_type = "modified"
                modified_count += 1
                changed_count += 1
                total_added_words += max(0, len(new_str.split()) - len(old_str.split()))
                total_removed_words += max(0, len(old_str.split()) - len(new_str.split()))
            else:
                change_type = "unchanged"

            if change_type != "unchanged":
                changed_count += 1 if change_type != "unchanged" else 0

            section_diffs.append(
                {
                    "section": section,
                    "old_value": old_str if old_str else None,
                    "new_value": new_str if new_str else None,
                    "change_type": change_type,
                }
            )

        return {
            "proposal_id": str(proposal_id),
            "version_old": v_a.version_number,
            "version_new": v_b.version_number,
            "section_diffs": section_diffs,
            "stats": {
                "total_sections": len(COMPARISON_SECTIONS),
                "changed_sections": changed_count,
                "added_sections": added_count,
                "removed_sections": removed_count,
                "modified_sections": modified_count,
                "words_added": total_added_words,
                "words_removed": total_removed_words,
            },
        }

    # --- Internal helpers ---

    async def _assert_ownership(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        from app.core.exceptions import AuthorizationError

        proposal = await self._proposal_repo.get_by_id(proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal not found.")
        if proposal.user_id != user_id:
            raise AuthorizationError(
                "You do not have permission to access this proposal."
            )
        return proposal

    @staticmethod
    def _get_section_value(version: ProposalVersion, section: str):
        return getattr(version, section, None)
