import uuid
from datetime import datetime, timezone

import pytest

from app.core.exceptions import BadRequestError, NotFoundError, ValidationAppError
from app.models.audit_log import AuditLog
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.models.proposal_note import ProposalNote
from app.models.proposal_status_history import ProposalStatusHistory
from app.models.proposal_version import ProposalVersion
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.proposal_note_service import ProposalNoteService
from app.services.proposal_review_service import (
    COMPARISON_SECTIONS,
    VALID_TRANSITIONS,
    ProposalReviewService,
)


# --- Fake Repositories ---


class FakeProposalRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, Proposal] = {}

    async def get_by_id(self, proposal_id):
        return self._store.get(proposal_id)

    async def create(self, user_id, project_id, **fields):
        allowed = [
            "status", "cover_letter", "bid_amount", "bid_type", "currency",
            "estimated_duration", "ai_generated", "ai_generation_version",
            "ai_confidence_score", "requires_human_approval", "template_id",
            "title",
        ]
        clean = {k: v for k, v in fields.items() if k in allowed}
        proposal = Proposal(id=uuid.uuid4(), user_id=user_id, project_id=project_id, **clean)
        self._store[proposal.id] = proposal
        return proposal

    async def update(self, proposal, **fields):
        for k, v in fields.items():
            setattr(proposal, k, v)
        return proposal


class FakeVersionRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, ProposalVersion] = {}

    async def get_by_id(self, version_id):
        return self._store.get(version_id)

    async def get_by_id_and_proposal_id(self, version_id, proposal_id):
        v = self._store.get(version_id)
        if v and v.proposal_id == proposal_id:
            return v
        return None

    async def get_by_proposal_id(self, proposal_id, skip=0, limit=20):
        items = [v for v in self._store.values() if v.proposal_id == proposal_id]
        items.sort(key=lambda v: v.version_number, reverse=True)
        return items[skip:skip + limit], len(items)

    async def get_latest_version_number(self, proposal_id):
        versions = [v for v in self._store.values() if v.proposal_id == proposal_id]
        if not versions:
            return 0
        return max(v.version_number for v in versions)

    async def create(self, **fields):
        fields.setdefault("created_by", "ai")
        version = ProposalVersion(id=uuid.uuid4(), **fields)
        self._store[version.id] = version
        return version


class FakeStatusHistoryRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, ProposalStatusHistory] = {}

    async def create(self, **fields):
        entry = ProposalStatusHistory(id=uuid.uuid4(), **fields)
        self._store[entry.id] = entry
        return entry

    async def get_by_proposal_id(self, proposal_id, skip=0, limit=50):
        items = [e for e in self._store.values() if e.proposal_id == proposal_id]
        items.sort(key=lambda e: e.created_at, reverse=True)
        return items[skip:skip + limit], len(items)


class FakeAuditLogRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, AuditLog] = {}

    async def create(self, **fields):
        fields.setdefault("created_at", datetime.now(timezone.utc))
        entry = AuditLog(id=uuid.uuid4(), **fields)
        self._store[entry.id] = entry
        return entry

    async def get_by_proposal_id(self, proposal_id, skip=0, limit=50):
        items = [e for e in self._store.values() if e.proposal_id == proposal_id]
        items.sort(key=lambda e: e.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return items[skip:skip + limit], len(items)


class FakeOpportunityRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, Opportunity] = {}

    async def get_by_id(self, opp_id):
        return self._store.get(opp_id)


class FakeNoteRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, ProposalNote] = {}

    async def create(self, **fields):
        note = ProposalNote(id=uuid.uuid4(), **fields)
        self._store[note.id] = note
        return note

    async def get_by_id(self, note_id):
        return self._store.get(note_id)

    async def get_by_proposal_id(self, proposal_id, skip=0, limit=20):
        items = [n for n in self._store.values() if n.proposal_id == proposal_id]
        items.sort(key=lambda n: n.created_at, reverse=True)
        return items[skip:skip + limit], len(items)

    async def update(self, note, **fields):
        for k, v in fields.items():
            setattr(note, k, v)
        return note

    async def delete(self, note):
        del self._store[note.id]


# --- Fixtures ---


@pytest.fixture
def user():
    return User(
        id=uuid.uuid4(),
        email="test@test.com",
        hashed_password="hash",
        full_name="Test User",
    )


@pytest.fixture
def proposal_repo():
    return FakeProposalRepo()


@pytest.fixture
def version_repo():
    return FakeVersionRepo()


@pytest.fixture
def status_history_repo():
    return FakeStatusHistoryRepo()


@pytest.fixture
def audit_log_repo():
    return FakeAuditLogRepo()


@pytest.fixture
def opp_repo():
    return FakeOpportunityRepo()


@pytest.fixture
def note_repo():
    return FakeNoteRepo()


@pytest.fixture
def review_service(proposal_repo, version_repo, status_history_repo, audit_log_repo, opp_repo):
    return ProposalReviewService(
        proposal_repository=proposal_repo,
        proposal_version_repository=version_repo,
        proposal_status_history_repository=status_history_repo,
        audit_log_repository=audit_log_repo,
        opportunity_repository=opp_repo,
    )


@pytest.fixture
def audit_service(audit_log_repo):
    return AuditService(audit_log_repo)


@pytest.fixture
def note_service(note_repo):
    return ProposalNoteService(note_repo)


@pytest.fixture
def draft_proposal(proposal_repo, user):
    p = Proposal(
        id=uuid.uuid4(),
        user_id=user.id,
        project_id=uuid.uuid4(),
        status="draft",
        cover_letter="Initial cover letter",
        bid_amount=5000.0,
        estimated_duration="2 months",
    )
    proposal_repo._store[p.id] = p
    return p


# --- Status Transition Tests ---


class TestStatusTransitions:
    async def test_draft_to_under_review(self, review_service, draft_proposal, user):
        result = await review_service.review(draft_proposal.id, user.id)
        assert result.status == "under_review"

    async def test_draft_to_archived(self, review_service, draft_proposal, user):
        result = await review_service.archive(draft_proposal.id, user.id)
        assert result.status == "archived"

    async def test_invalid_transition(self, review_service, draft_proposal, user):
        with pytest.raises(BadRequestError, match="Cannot transition"):
            await review_service.transition_status(
                draft_proposal.id, user.id, "submitted"
            )

    async def test_terminal_state_won(self, review_service, draft_proposal, user, proposal_repo):
        p = proposal_repo._store[draft_proposal.id]
        p.status = "won"
        with pytest.raises(BadRequestError, match="Cannot transition"):
            await review_service.transition_status(draft_proposal.id, user.id, "lost")

    async def test_archived_to_draft(self, review_service, draft_proposal, user, proposal_repo):
        p = proposal_repo._store[draft_proposal.id]
        p.status = "archived"
        result = await review_service.transition_status(
            draft_proposal.id, user.id, "draft"
        )
        assert result.status == "draft"

    async def test_transition_status_history_created(
        self, review_service, draft_proposal, user, status_history_repo
    ):
        await review_service.review(draft_proposal.id, user.id)
        items, total = await status_history_repo.get_by_proposal_id(draft_proposal.id)
        assert total == 1
        assert items[0].from_status == "draft"
        assert items[0].to_status == "under_review"

    async def test_transition_audit_log_created(
        self, review_service, draft_proposal, user, audit_log_repo
    ):
        await review_service.review(draft_proposal.id, user.id)
        items, total = await audit_log_repo.get_by_proposal_id(draft_proposal.id)
        assert total == 1
        assert items[0].action == "status_change"

    async def test_transition_unauthorized(self, review_service, draft_proposal, user):
        other = User(id=uuid.uuid4(), email="o@t.com", hashed_password="h", full_name="O")
        with pytest.raises(Exception):
            await review_service.review(draft_proposal.id, other.id)

    async def test_transition_missing_proposal(self, review_service, user):
        with pytest.raises(NotFoundError):
            await review_service.review(uuid.uuid4(), user.id)


# --- Submission Readiness Tests ---


class TestReadiness:
    async def test_ready_success(self, review_service, draft_proposal, user):
        await review_service.review(draft_proposal.id, user.id)
        result = await review_service.mark_ready(draft_proposal.id, user.id)
        assert result.status == "ready_to_submit"

    async def test_ready_missing_cover_letter(
        self, review_service, draft_proposal, user, proposal_repo
    ):
        p = proposal_repo._store[draft_proposal.id]
        p.cover_letter = None
        with pytest.raises(ValidationAppError, match="Cover letter"):
            await review_service.mark_ready(draft_proposal.id, user.id)

    async def test_ready_missing_bid(
        self, review_service, draft_proposal, user, proposal_repo
    ):
        p = proposal_repo._store[draft_proposal.id]
        p.bid_amount = None
        with pytest.raises(ValidationAppError, match="Bid amount"):
            await review_service.mark_ready(draft_proposal.id, user.id)

    async def test_ready_missing_duration(
        self, review_service, draft_proposal, user, proposal_repo
    ):
        p = proposal_repo._store[draft_proposal.id]
        p.estimated_duration = None
        with pytest.raises(ValidationAppError, match="Delivery estimate"):
            await review_service.mark_ready(draft_proposal.id, user.id)

    async def test_ready_opportunity_closed(
        self, review_service, draft_proposal, user, proposal_repo, opp_repo
    ):
        opp = Opportunity(
            id=draft_proposal.project_id,
            user_id=user.id,
            platform="upwork",
            title="Test",
            status="closed",
        )
        opp_repo._store[opp.id] = opp
        with pytest.raises(ValidationAppError, match="no longer open"):
            await review_service.mark_ready(draft_proposal.id, user.id)

    async def test_readiness_check_api(
        self, review_service, draft_proposal, user
    ):
        errors = await review_service.validate_readiness(draft_proposal)
        assert errors == []

    async def test_readiness_check_fails(
        self, review_service, draft_proposal, user, proposal_repo
    ):
        p = proposal_repo._store[draft_proposal.id]
        p.cover_letter = ""
        p.bid_amount = None
        errors = await review_service.validate_readiness(p)
        assert len(errors) >= 2


# --- Editing Tests ---


class TestEditing:
    async def test_edit_creates_new_version(
        self, review_service, draft_proposal, user, version_repo
    ):
        proposal, version = await review_service.edit_proposal(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            cover_letter="Updated cover letter",
            change_summary="Fixed typos",
        )
        assert version.version_number >= 1
        assert version.created_by == "user"
        assert version.change_summary == "Fixed typos"
        assert version.cover_letter == "Updated cover letter"

    async def test_edit_transitions_to_edited(
        self, review_service, draft_proposal, user
    ):
        proposal, version = await review_service.edit_proposal(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            cover_letter="Edited version",
        )
        assert proposal.status == "edited"

    async def test_edit_updates_proposal(
        self, review_service, draft_proposal, user, proposal_repo
    ):
        proposal, version = await review_service.edit_proposal(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            title="New Title",
            bid_amount=7500.0,
        )
        assert proposal.title == "New Title"
        assert proposal.bid_amount == 7500.0

    async def test_edit_audit_logged(
        self, review_service, draft_proposal, user, audit_log_repo
    ):
        await review_service.edit_proposal(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            cover_letter="Updated",
        )
        items, total = await audit_log_repo.get_by_proposal_id(draft_proposal.id)
        assert any(e.action == "user_edit" for e in items)


# --- Rollback Tests ---


class TestRollback:
    async def test_rollback_creates_new_version(
        self, review_service, draft_proposal, user, version_repo
    ):
        v1 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=1,
            created_by="ai",
            cover_letter="AI version",
        )
        v2 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=2,
            created_by="user",
            cover_letter="User edit",
        )
        proposal, version = await review_service.rollback(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            version_id=v1.id,
            change_summary="Revert to AI version",
        )
        assert version.version_number > v2.version_number
        assert version.cover_letter == "AI version"
        assert version.created_by == "user"
        assert "Revert" in version.change_summary

    async def test_rollback_missing_version(
        self, review_service, draft_proposal, user
    ):
        with pytest.raises(NotFoundError, match="Version not found"):
            await review_service.rollback(
                proposal_id=draft_proposal.id,
                user_id=user.id,
                version_id=uuid.uuid4(),
            )

    async def test_rollback_audit_logged(
        self, review_service, draft_proposal, user, version_repo, audit_log_repo
    ):
        v1 = await version_repo.create(
            proposal_id=draft_proposal.id, version_number=1, created_by="ai"
        )
        await review_service.rollback(
            proposal_id=draft_proposal.id, user_id=user.id, version_id=v1.id
        )
        items, total = await audit_log_repo.get_by_proposal_id(draft_proposal.id)
        assert any(e.action == "rollback" for e in items)


# --- Comparison Tests ---


class TestComparison:
    async def test_compare_identical_versions(
        self, review_service, draft_proposal, user, version_repo
    ):
        v1 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=1,
            created_by="ai",
            cover_letter="Hello",
        )
        result = await review_service.compare_versions(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            version_id_a=v1.id,
            version_id_b=v1.id,
        )
        assert result["stats"]["changed_sections"] == 0

    async def test_compare_different_versions(
        self, review_service, draft_proposal, user, version_repo
    ):
        v1 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=1,
            created_by="ai",
            cover_letter="Old version",
            bid_amount=5000.0,
        )
        v2 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=2,
            created_by="user",
            cover_letter="New version",
            bid_amount=7500.0,
        )
        result = await review_service.compare_versions(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            version_id_a=v1.id,
            version_id_b=v2.id,
        )
        assert result["stats"]["changed_sections"] >= 2
        assert result["proposal_id"] == str(draft_proposal.id)
        assert result["version_old"] == 1
        assert result["version_new"] == 2

    async def test_compare_section_diffs(
        self, review_service, draft_proposal, user, version_repo
    ):
        v1 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=1,
            cover_letter="Old cover",
            executive_summary="Old summary",
        )
        v2 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=2,
            cover_letter="New cover",
            executive_summary="",
        )
        result = await review_service.compare_versions(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            version_id_a=v1.id,
            version_id_b=v2.id,
        )
        diffs = {d["section"]: d for d in result["section_diffs"]}
        assert diffs["cover_letter"]["change_type"] == "modified"
        assert diffs["executive_summary"]["change_type"] == "removed"
        assert diffs["bid_amount"]["change_type"] == "unchanged"

    async def test_compare_missing_version(
        self, review_service, draft_proposal, user
    ):
        with pytest.raises(NotFoundError):
            await review_service.compare_versions(
                proposal_id=draft_proposal.id,
                user_id=user.id,
                version_id_a=uuid.uuid4(),
                version_id_b=uuid.uuid4(),
            )

    async def test_compare_stats(
        self, review_service, draft_proposal, user, version_repo
    ):
        v1 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=1,
            cover_letter="A B C D E",
            executive_summary="X Y Z",
        )
        v2 = await version_repo.create(
            proposal_id=draft_proposal.id,
            version_number=2,
            cover_letter="A B C D E F G",
            executive_summary="",
            bid_amount=100.0,
        )
        result = await review_service.compare_versions(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            version_id_a=v1.id,
            version_id_b=v2.id,
        )
        stats = result["stats"]
        assert stats["total_sections"] == len(COMPARISON_SECTIONS)
        assert stats["words_added"] >= 2


# --- Audit Service Tests ---


class TestAuditService:
    async def test_log_creates_entry(self, audit_service, user):
        entry = await audit_service.log(
            user_id=user.id,
            action="test_action",
            proposal_id=uuid.uuid4(),
            details="Test details",
        )
        assert entry.action == "test_action"
        assert entry.details == "Test details"

    async def test_get_proposal_log(self, audit_service, audit_log_repo, user):
        pid = uuid.uuid4()
        await audit_service.log(user_id=user.id, action="a1", proposal_id=pid)
        await audit_service.log(user_id=user.id, action="a2", proposal_id=pid)
        items, total = await audit_service.get_proposal_log(pid)
        assert total == 2


# --- Proposal Note Tests ---


class TestNotes:
    async def test_create_note(self, note_service, draft_proposal, user):
        note = await note_service.create(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            content="This is a private note.",
        )
        assert note.content == "This is a private note."
        assert note.proposal_id == draft_proposal.id

    async def test_update_note(self, note_service, draft_proposal, user):
        note = await note_service.create(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            content="Original",
        )
        updated = await note_service.update(
            note_id=note.id,
            user_id=user.id,
            content="Updated",
        )
        assert updated.content == "Updated"

    async def test_delete_note(self, note_service, draft_proposal, user):
        note = await note_service.create(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            content="To delete",
        )
        await note_service.delete(note_id=note.id, user_id=user.id)
        with pytest.raises(NotFoundError):
            await note_service.get_by_id(note.id, user_id=user.id)

    async def test_note_ownership(self, note_service, draft_proposal, user):
        other = User(id=uuid.uuid4(), email="o@t.com", hashed_password="h", full_name="O")
        note = await note_service.create(
            proposal_id=draft_proposal.id,
            user_id=user.id,
            content="Private",
        )
        with pytest.raises(Exception):
            await note_service.update(note_id=note.id, user_id=other.id, content="Hacked")


# --- Proposal Note via Review Service Integration ---


class TestFullReviewFlow:
    async def test_full_review_flow(
        self, review_service, draft_proposal, user, proposal_repo, version_repo
    ):
        p = draft_proposal
        assert p.status == "draft"

        p = await review_service.review(p.id, user.id)
        assert p.status == "under_review"

        p, v1 = await review_service.edit_proposal(
            proposal_id=p.id, user_id=user.id, cover_letter="Edited",
        )

        p = await review_service.mark_ready(p.id, user.id)
        assert p.status == "ready_to_submit"

        p = await review_service.mark_submitted(p.id, user.id)
        assert p.status == "submitted"
        assert p.submitted_at is not None

        p = await review_service.transition_status(p.id, user.id, "won")
        assert p.status == "won"


# --- Human Approval Flow Tests ---


class TestHumanApprovalFlow:
    @pytest.fixture
    def ai_proposal(self, user, proposal_repo):
        p = Proposal(
            id=uuid.uuid4(),
            user_id=user.id,
            project_id=uuid.uuid4(),
            status="ai_generated",
            cover_letter="AI generated proposal",
            bid_amount=5000.0,
            estimated_duration="3 weeks",
        )
        proposal_repo._store[p.id] = p
        return p

    async def test_request_approval(self, review_service, user, ai_proposal):
        result = await review_service.request_approval(ai_proposal.id, user.id)
        assert result.status == "awaiting_approval"

    async def test_approve(self, review_service, user, ai_proposal, proposal_repo):
        p = proposal_repo._store[ai_proposal.id]
        p.status = "awaiting_approval"
        result = await review_service.approve(ai_proposal.id, user.id)
        assert result.status == "approved"
        assert result.human_approved_at is not None
        assert result.human_approved_by == user.id

    async def test_reject(self, review_service, user, ai_proposal, proposal_repo):
        p = proposal_repo._store[ai_proposal.id]
        p.status = "awaiting_approval"
        result = await review_service.reject(ai_proposal.id, user.id, reason="Needs more detail")
        assert result.status == "rejected"
        assert result.rejection_reason == "Needs more detail"

    async def test_reject_no_reason(self, review_service, user, ai_proposal, proposal_repo):
        p = proposal_repo._store[ai_proposal.id]
        p.status = "awaiting_approval"
        result = await review_service.reject(ai_proposal.id, user.id)
        assert result.status == "rejected"

    async def test_queue(self, review_service, user, ai_proposal, proposal_repo):
        p = proposal_repo._store[ai_proposal.id]
        p.status = "approved"
        result = await review_service.queue(ai_proposal.id, user.id)
        assert result.status == "queued"

    async def test_ai_generated_to_draft(self, review_service, user, ai_proposal):
        result = await review_service.transition_status(ai_proposal.id, user.id, "draft")
        assert result.status == "draft"

    async def test_approve_updates_human_approved_at(self, review_service, user, ai_proposal, proposal_repo):
        p = proposal_repo._store[ai_proposal.id]
        p.status = "awaiting_approval"
        from datetime import datetime, timezone
        before = datetime.now(timezone.utc)
        result = await review_service.approve(ai_proposal.id, user.id)
        assert result.human_approved_at is not None
        assert result.human_approved_at >= before

    async def test_rejected_to_draft(self, review_service, user, ai_proposal, proposal_repo):
        p = proposal_repo._store[ai_proposal.id]
        p.status = "rejected"
        result = await review_service.transition_status(ai_proposal.id, user.id, "draft")
        assert result.status == "draft"

    async def test_approved_to_ready(self, review_service, user, ai_proposal, proposal_repo):
        p = proposal_repo._store[ai_proposal.id]
        p.status = "approved"
        result = await review_service.transition_status(ai_proposal.id, user.id, "ready_to_submit")
        assert result.status == "ready_to_submit"

    async def test_invalid_approval_transition(self, review_service, user, ai_proposal):
        with pytest.raises(BadRequestError, match="Cannot transition"):
            await review_service.approve(ai_proposal.id, user.id)

    async def test_invalid_ai_generated_transition(self, review_service, user, ai_proposal):
        with pytest.raises(BadRequestError, match="Cannot transition"):
            await review_service.transition_status(ai_proposal.id, user.id, "submitted")
