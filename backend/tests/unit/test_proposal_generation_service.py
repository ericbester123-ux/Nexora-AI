import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ExternalServiceError, NotFoundError, ValidationAppError
from app.infrastructure.llm import LLMConfig, LLMProvider, LLMResponse
from app.models.ai_preference import AIPreference
from app.models.ai_usage_log import AIUsageLog
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.models.proposal_template import ProposalTemplate
from app.models.proposal_version import ProposalVersion
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.proposal_generation_service import ProposalGenerationService
from app.services.prompt_builder import PromptBuilder


class FakeProposalRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, Proposal] = {}

    async def get_by_id(self, proposal_id):
        return self._store.get(proposal_id)

    async def create(self, user_id, project_id, **fields):
        allowed = ["status", "cover_letter", "bid_amount", "bid_type", "currency",
                    "estimated_duration", "ai_generated", "ai_generation_version",
                    "ai_confidence_score", "requires_human_approval", "template_id"]
        clean = {k: v for k, v in fields.items() if k in allowed}
        proposal = Proposal(
            id=uuid.uuid4(),
            user_id=user_id,
            project_id=project_id,
            **clean,
        )
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

    async def create(self, **fields):
        opp = Opportunity(id=uuid.uuid4(), **fields)
        self._store[opp.id] = opp
        return opp

    async def update(self, opp, **fields):
        for k, v in fields.items():
            setattr(opp, k, v)
        return opp


class FakeTemplateRepo:
    def __init__(self):
        self._store: dict[uuid.UUID, ProposalTemplate] = {}

    async def get_by_id(self, template_id):
        return self._store.get(template_id)

    async def get_by_user_id(self, user_id, skip=0, limit=20, search=None, category=None, is_active=None):
        items = [t for t in self._store.values() if t.user_id == user_id]
        if is_active is not None:
            items = [t for t in items if t.is_active == is_active]
        return items, len(items)


class FakeScoringService:
    async def score_opportunity(self, opportunity, user, user_preferences, ai_preferences):
        from app.services.scoring_service import ScoreResult
        return ScoreResult(
            score=0.85,
            skills_score=0.9,
            budget_score=0.8,
            category_score=1.0,
            experience_score=0.7,
            client_quality_score=0.75,
            match_reason="Skills match (90%)",
        )


class MockLLMProvider(LLMProvider):
    def __init__(self, response_content: str = '{"coverLetter": "Dear client...", "executiveSummary": "Summary...", "whyGoodFit": "I am a good fit because...", "relevantExperience": "I have done similar work...", "recommendedBid": 7500, "estimatedDeliveryTime": "4 weeks", "suggestedMilestones": "Phase 1: Setup", "riskNotes": "No significant risks.", "confidenceExplanation": "I am confident.", "proposalSummary": "In summary..."}'):
        self._content = response_content
        self._name = "mock-provider"

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        return LLMResponse(
            content=self._content,
            model="mock-model",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            latency_ms=500,
        )

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def user():
    return User(
        id=uuid.uuid4(),
        email="test@test.com",
        hashed_password="hash",
        full_name="Test User",
        primary_skills=["Python", "FastAPI"],
    )


@pytest.fixture
def opp(user):
    opp = Opportunity(
        id=uuid.uuid4(),
        user_id=user.id,
        platform="upwork",
        external_id="ext-1",
        title="Build API",
        description="Need an API",
        skills=["Python", "FastAPI"],
        budget_min=5000,
        budget_max=10000,
        is_ai_scored=True,
        ai_score=0.85,
        ai_match_reason="Good match",
    )
    return opp


@pytest.fixture
def proposal(user, opp):
    return Proposal(
        id=uuid.uuid4(),
        user_id=user.id,
        project_id=opp.id,
        status="draft",
        cover_letter=None,
    )


@pytest.fixture
def service(user, opp):
    proposal_repo = FakeProposalRepo()
    version_repo = FakeVersionRepo()
    usage_repo = FakeUsageRepo()
    opp_repo = FakeOpportunityRepo()
    template_repo = FakeTemplateRepo()
    scoring_service = FakeScoringService()
    llm_provider = MockLLMProvider()

    opp_repo._store[opp.id] = opp

    svc = ProposalGenerationService(
        proposal_repository=proposal_repo,
        proposal_version_repository=version_repo,
        ai_usage_log_repository=usage_repo,
        opportunity_repository=opp_repo,
        proposal_template_repository=template_repo,
        scoring_service=scoring_service,
        llm_provider=llm_provider,
    )
    return svc


class TestGenerateProposal:
    async def test_generate_proposal_success(self, service, user, opp):
        proposal, version, usage_log = await service.generate_proposal(user=user, opportunity_id=opp.id)
        assert proposal.status == "ai_generated"
        assert proposal.ai_generated is True
        assert version.version_number == 1
        assert version.cover_letter == "Dear client..."
        assert usage_log.provider == "mock-provider"
        assert usage_log.total_tokens == 300
        assert usage_log.estimated_cost_usd > 0

    async def test_generate_proposal_invalid_json(self, service, user, opp):
        bad_provider = MockLLMProvider(response_content="not json at all")
        service._llm_provider = bad_provider
        with pytest.raises(ValidationAppError, match="not valid JSON"):
            await service.generate_proposal(user=user, opportunity_id=opp.id)

    async def test_generate_proposal_missing_required_section(self, service, user, opp):
        bad_provider = MockLLMProvider(response_content='{"coverLetter": "Hello", "executiveSummary": "Sum"}')
        service._llm_provider = bad_provider
        with pytest.raises(ValidationAppError, match="missing required sections"):
            await service.generate_proposal(user=user, opportunity_id=opp.id)

    async def test_generate_proposal_empty_cover_letter(self, service, user, opp):
        bad_content = '{"coverLetter": "", "executiveSummary": "Sum", "whyGoodFit": "Fit", "relevantExperience": "Exp", "proposalSummary": "Summary"}'
        bad_provider = MockLLMProvider(response_content=bad_content)
        service._llm_provider = bad_provider
        with pytest.raises(ValidationAppError, match="Cover letter must not be empty"):
            await service.generate_proposal(user=user, opportunity_id=opp.id)

    async def test_generate_proposal_llm_failure(self, service, user, opp):
        failing_provider = MockLLMProvider(response_content="")
        original_generate = failing_provider.generate

        call_count = 0

        async def failing_generate(prompt, config):
            nonlocal call_count
            call_count += 1
            raise TimeoutError("LLM timeout")

        failing_provider.generate = failing_generate
        service._llm_provider = failing_provider
        with pytest.raises(ExternalServiceError, match="AI provider failed"):
            await service.generate_proposal(user=user, opportunity_id=opp.id)

    async def test_generate_proposal_missing_opportunity(self, service, user):
        with pytest.raises(NotFoundError, match="Opportunity not found"):
            await service.generate_proposal(user=user, opportunity_id=uuid.uuid4())

    async def test_generate_proposal_unauthorized_opportunity(self, service, user, opp):
        other_user = User(
            id=uuid.uuid4(),
            email="other@test.com",
            hashed_password="hash",
            full_name="Other",
        )
        with pytest.raises(NotFoundError, match="Opportunity not found"):
            await service.generate_proposal(user=other_user, opportunity_id=opp.id)

    async def test_generate_proposal_with_preferences(self, service, user, opp):
        ai_prefs = AIPreference(
            id=uuid.uuid4(),
            user_id=user.id,
            proposal_tone="casual",
            proposal_length="short",
            writing_style="storytelling",
            automatically_include_portfolio=False,
            bid_recommendation_style="aggressive",
        )
        user_prefs = UserPreference(
            id=uuid.uuid4(),
            user_id=user.id,
        )
        proposal, version, usage_log = await service.generate_proposal(
            user=user,
            opportunity_id=opp.id,
            user_preferences=user_prefs,
            ai_preferences=ai_prefs,
        )
        assert proposal.status == "ai_generated"
        assert version.version_number == 1


class TestRegenerate:
    async def test_regenerate_creates_new_version(self, service, user, opp, proposal):
        svc = service
        proposal_repo = svc._proposal_repo
        proposal_repo._store[proposal.id] = proposal
        existing, version, usage_log = await svc.regenerate(user=user, proposal_id=proposal.id)
        assert version.version_number >= 1

    async def test_regenerate_missing_proposal(self, service, user):
        with pytest.raises(NotFoundError, match="Proposal not found"):
            await service.regenerate(user=user, proposal_id=uuid.uuid4())

    async def test_regenerate_unauthorized(self, service, user, opp, proposal):
        other_user = User(id=uuid.uuid4(), email="o@t.com", hashed_password="h", full_name="O")
        proposal_repo = service._proposal_repo
        proposal.user_id = other_user.id
        proposal_repo._store[proposal.id] = proposal
        with pytest.raises(NotFoundError, match="Proposal not found"):
            await service.regenerate(user=user, proposal_id=proposal.id)


class TestVersionHistory:
    async def test_get_version_history(self, service, user, opp):
        proposal, version, _ = await service.generate_proposal(user=user, opportunity_id=opp.id)
        version_repo = service._version_repo
        versions, total = await version_repo.get_by_proposal_id(proposal.id)
        assert total == 1
        assert versions[0].id == version.id

    async def test_get_version_detail(self, service, user, opp):
        proposal, version, _ = await service.generate_proposal(user=user, opportunity_id=opp.id)
        version_repo = service._version_repo
        found = await version_repo.get_by_id(version.id)
        assert found is not None
        assert found.id == version.id


class TestUsageLogging:
    async def test_usage_log_created(self, service, user, opp):
        proposal, version, usage_log = await service.generate_proposal(user=user, opportunity_id=opp.id)
        assert usage_log.user_id == user.id
        assert usage_log.provider == "mock-provider"
        assert usage_log.model == "mock-model"
        assert usage_log.prompt_tokens == 100
        assert usage_log.completion_tokens == 200
        assert usage_log.total_tokens == 300
        assert usage_log.latency_ms == 500
        assert usage_log.endpoint == "generate_proposal"

    async def test_cost_tracking(self, service, user, opp):
        proposal, version, usage_log = await service.generate_proposal(user=user, opportunity_id=opp.id)
        assert usage_log.estimated_cost_usd > 0
        expected_prompt_cost = (100 / 1_000_000) * 0.15
        expected_completion_cost = (200 / 1_000_000) * 0.60
        expected_total = round(expected_prompt_cost + expected_completion_cost, 6)
        assert usage_log.estimated_cost_usd == expected_total


class TestValidation:
    async def test_validate_malformed_json(self, service, user, opp):
        bad_provider = MockLLMProvider(response_content='{"coverLetter": "Hello"')
        service._llm_provider = bad_provider
        with pytest.raises(ValidationAppError, match="not valid JSON"):
            await service.generate_proposal(user=user, opportunity_id=opp.id)

    async def test_validate_non_dict_response(self, service, user, opp):
        bad_provider = MockLLMProvider(response_content='"just a string"')
        service._llm_provider = bad_provider
        with pytest.raises(ValidationAppError, match="must be a JSON object"):
            await service.generate_proposal(user=user, opportunity_id=opp.id)

    async def test_validate_markdown_code_block_no_lang(self, service, user, opp):
        md_content = """```
{"coverLetter": "Dear client...", "executiveSummary": "Summary...", "whyGoodFit": "I am a good fit because...", "relevantExperience": "I have done similar work...", "recommendedBid": 7500, "estimatedDeliveryTime": "4 weeks", "suggestedMilestones": "Phase 1", "riskNotes": "None", "confidenceExplanation": "Confident.", "proposalSummary": "In summary..."}
```"""
        md_provider = MockLLMProvider(response_content=md_content)
        service._llm_provider = md_provider
        proposal, version, usage_log = await service.generate_proposal(user=user, opportunity_id=opp.id)
        assert version.cover_letter == "Dear client..."

    async def test_parse_response_extra_whitespace(self, service, user, opp):
        content = """


{"coverLetter": "Hello", "executiveSummary": "Sum", "whyGoodFit": "Fit", "relevantExperience": "Exp", "proposalSummary": "Summary"}


"""
        bad_provider = MockLLMProvider(response_content=content)
        service._llm_provider = bad_provider
        proposal, version, usage_log = await service.generate_proposal(user=user, opportunity_id=opp.id)
        assert version.cover_letter == "Hello"

    async def test_validate_markdown_code_block(self, service, user, opp):
        md_content = """```json
{"coverLetter": "Dear client...", "executiveSummary": "Summary...", "whyGoodFit": "I am a good fit because...", "relevantExperience": "I have done similar work...", "recommendedBid": 7500, "estimatedDeliveryTime": "4 weeks", "suggestedMilestones": "Phase 1", "riskNotes": "None", "confidenceExplanation": "Confident.", "proposalSummary": "In summary..."}
```"""
        md_provider = MockLLMProvider(response_content=md_content)
        service._llm_provider = md_provider
        proposal, version, usage_log = await service.generate_proposal(user=user, opportunity_id=opp.id)
        assert version.cover_letter == "Dear client..."
