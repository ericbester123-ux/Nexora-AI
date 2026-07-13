import uuid

import pytest

from app.core.exceptions import ExternalServiceError, NotFoundError
from app.infrastructure.llm import LLMConfig, LLMProvider, LLMResponse
from app.models.ai_usage_log import AIUsageLog
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.models.proposal_version import ProposalVersion
from app.models.user import User
from app.services.proposal_improver import ProposalImprover


class MockLLMProvider(LLMProvider):
    def __init__(self, response_content: str | None = None):
        self._content = response_content or '{"coverLetter": "Improved letter", "executiveSummary": "Better summary", "whyGoodFit": "Strong fit", "relevantExperience": "Relevant exp", "recommendedBid": 5000, "estimatedDeliveryTime": "3 weeks", "suggestedMilestones": "Phase 1", "riskNotes": "Low risk", "confidenceExplanation": "Confident", "proposalSummary": "In summary..."}'
        self._name = "mock-improver"

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        return LLMResponse(
            content=self._content,
            model="mock-improver-model",
            prompt_tokens=80,
            completion_tokens=150,
            total_tokens=230,
            latency_ms=400,
        )

    async def health_check(self) -> bool:
        return True


class FakeProposalRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, Proposal] = {}

    async def get_by_id(self, proposal_id):
        return self._store.get(proposal_id)

    async def update(self, proposal, **fields):
        for k, v in fields.items():
            setattr(proposal, k, v)
        return proposal


class FakeVersionRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, ProposalVersion] = {}

    async def get_latest_version_number(self, proposal_id):
        versions = [v for v in self._store.values() if v.proposal_id == proposal_id]
        return max(v.version_number for v in versions) if versions else 0

    async def get_by_proposal_id(self, proposal_id, skip=0, limit=20):
        items = [v for v in self._store.values() if v.proposal_id == proposal_id]
        items.sort(key=lambda v: v.version_number, reverse=True)
        return items[skip:skip + limit], len(items)

    async def create(self, **fields):
        version = ProposalVersion(id=uuid.uuid4(), **fields)
        self._store[version.id] = version
        return version


class FakeUsageRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, AIUsageLog] = {}

    async def create(self, **fields):
        log = AIUsageLog(id=uuid.uuid4(), **fields)
        self._store[log.id] = log
        return log


class FakeOpportunityRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, Opportunity] = {}

    async def get_by_id(self, opp_id):
        return self._store.get(opp_id)


@pytest.fixture
def user():
    return User(id=uuid.uuid4(), email="t@t.com", hashed_password="h", full_name="Test")


@pytest.fixture
def proposal(user):
    return Proposal(
        id=uuid.uuid4(),
        user_id=user.id,
        project_id=uuid.uuid4(),
        status="ai_generated",
        cover_letter="Original cover letter for the proposal.",
        bid_amount=5000,
        estimated_duration="4 weeks",
    )


@pytest.fixture
def opp(user):
    return Opportunity(
        id=uuid.uuid4(),
        user_id=user.id,
        platform="upwork",
        title="Build a web app",
        description="Need a skilled developer",
        skills=["Python", "React"],
    )


@pytest.fixture
def improver(user, proposal, opp):
    proposal_repo = FakeProposalRepo()
    version_repo = FakeVersionRepo()
    usage_repo = FakeUsageRepo()
    opp_repo = FakeOpportunityRepo()
    llm_provider = MockLLMProvider()

    proposal_repo._store[proposal.id] = proposal
    opp_repo._store[opp.id] = opp

    svc = ProposalImprover(
        proposal_repository=proposal_repo,
        proposal_version_repository=version_repo,
        ai_usage_log_repository=usage_repo,
        opportunity_repository=opp_repo,
        llm_provider=llm_provider,
    )
    return svc


class TestProposalImprover:
    async def test_improve_shorter(self, improver, user, proposal):
        result_proposal, version, usage = await improver.improve(
            user=user, proposal_id=proposal.id, style="shorter"
        )
        assert version.version_number >= 1
        assert version.cover_letter == "Improved letter"
        assert usage.provider == "mock-improver"
        assert usage.endpoint == "improve_proposal_shorter"

    async def test_improve_longer(self, improver, user, proposal):
        result_proposal, version, usage = await improver.improve(
            user=user, proposal_id=proposal.id, style="longer"
        )
        assert version.cover_letter == "Improved letter"
        assert usage.endpoint == "improve_proposal_longer"

    async def test_improve_custom_instruction(self, improver, user, proposal):
        result_proposal, version, usage = await improver.improve(
            user=user,
            proposal_id=proposal.id,
            style="custom",
            custom_instruction="Make it more concise and focus on React experience",
        )
        assert version.cover_letter is not None

    async def test_improve_focus_section(self, improver, user, proposal):
        result_proposal, version, usage = await improver.improve(
            user=user,
            proposal_id=proposal.id,
            style="more_technical",
            focus_section="coverLetter",
        )
        assert version.cover_letter == "Improved letter"

    async def test_improve_creates_version_with_history(self, improver, user, proposal):
        v1_repo = improver._version_repo
        await v1_repo.create(proposal_id=proposal.id, version_number=1, created_by="ai")
        result_proposal, version, usage = await improver.improve(
            user=user, proposal_id=proposal.id, style="formal"
        )
        assert version.version_number == 2

    async def test_improve_missing_proposal(self, improver, user):
        with pytest.raises(NotFoundError, match="Proposal not found"):
            await improver.improve(user=user, proposal_id=uuid.uuid4(), style="shorter")

    async def test_improve_unauthorized(self, improver, proposal):
        other = User(id=uuid.uuid4(), email="o@t.com", hashed_password="h", full_name="O")
        with pytest.raises(NotFoundError, match="Proposal not found"):
            await improver.improve(user=other, proposal_id=proposal.id, style="shorter")

    async def test_improve_updates_proposal(self, improver, user, proposal):
        result_proposal, version, usage = await improver.improve(
            user=user, proposal_id=proposal.id, style="shorter"
        )
        assert result_proposal.cover_letter is not None

    async def test_improve_usage_logged(self, improver, user, proposal):
        result_proposal, version, usage = await improver.improve(
            user=user, proposal_id=proposal.id, style="more_persuasive"
        )
        assert usage.user_id == user.id
        assert usage.total_tokens == 230
        assert usage.estimated_cost_usd > 0

    async def test_improve_all_styles(self, improver, user, proposal):
        styles = ["shorter", "longer", "more_technical", "less_technical", "more_persuasive", "formal", "casual"]
        for style in styles:
            result, version, usage = await improver.improve(
                user=user, proposal_id=proposal.id, style=style
            )
            assert version.id is not None

    async def test_improve_invalid_json_response(self, improver, user, proposal):
        from app.core.exceptions import ValidationAppError
        bad_provider = MockLLMProvider(response_content="not json")
        improver._llm_provider = bad_provider
        with pytest.raises(ValidationAppError, match="not valid JSON"):
            await improver.improve(
                user=user, proposal_id=proposal.id, style="shorter"
            )
