import uuid

import pytest

from app.infrastructure.llm import LLMConfig, LLMProvider, LLMResponse
from app.models.ai_usage_log import AIUsageLog
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.models.proposal_version import ProposalVersion
from app.models.user import User
from app.services.proposal_evaluator import ProposalEvaluator


class MockLLMProvider(LLMProvider):
    def __init__(self, response_content: str | None = None):
        self._content = response_content or '{"overallScore": 0.85, "completenessScore": 0.9, "persuasivenessScore": 0.8, "relevanceScore": 0.85, "clarityScore": 0.9, "formattingScore": 0.75, "strengths": ["Clear structure", "Relevant experience highlighted"], "weaknesses": ["Bid amount not justified", "Could be more concise"], "suggestions": ["Add budget justification", "Shorten executive summary"]}'
        self._name = "mock-evaluator"

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        return LLMResponse(
            content=self._content,
            model="mock-evaluator-model",
            prompt_tokens=120,
            completion_tokens=100,
            total_tokens=220,
            latency_ms=350,
        )

    async def health_check(self) -> bool:
        return True


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
        cover_letter="We are confident we can deliver this project.",
        bid_amount=5000,
        estimated_duration="4 weeks",
    )


@pytest.fixture
def version(proposal):
    return ProposalVersion(
        id=uuid.uuid4(),
        proposal_id=proposal.id,
        version_number=1,
        created_by="ai",
        cover_letter="We are confident we can deliver this project.",
        executive_summary="Summary of approach",
        why_good_fit="We have relevant experience",
        relevant_experience="Similar projects completed",
        proposal_summary="In summary, we are a good fit",
    )


@pytest.fixture
def opp(user):
    return Opportunity(
        id=uuid.uuid4(),
        user_id=user.id,
        platform="upwork",
        title="Build API",
        description="Need REST API",
        skills=["Python", "FastAPI"],
    )


@pytest.fixture
def evaluator(user):
    usage_repo = FakeUsageRepo()
    opp_repo = FakeOpportunityRepo()
    llm_provider = MockLLMProvider()

    svc = ProposalEvaluator(
        ai_usage_log_repository=usage_repo,
        opportunity_repository=opp_repo,
        llm_provider=llm_provider,
    )
    return svc


class TestProposalEvaluator:
    async def test_evaluate_returns_scores(self, evaluator, user, proposal, version):
        result = await evaluator.evaluate(user=user, proposal=proposal, version=version)
        assert result.overall_score == 0.85
        assert result.completeness_score == 0.9
        assert result.persuasiveness_score == 0.8
        assert result.relevance_score == 0.85
        assert result.clarity_score == 0.9
        assert result.formatting_score == 0.75

    async def test_evaluate_returns_feedback(self, evaluator, user, proposal, version):
        result = await evaluator.evaluate(user=user, proposal=proposal, version=version)
        assert len(result.strengths) >= 1
        assert len(result.weaknesses) >= 1
        assert len(result.suggestions) >= 1
        assert "Clear structure" in result.strengths

    async def test_evaluate_with_opportunity(self, evaluator, user, proposal, version, opp):
        result = await evaluator.evaluate(user=user, proposal=proposal, version=version, opportunity=opp)
        assert result.overall_score > 0

    async def test_evaluate_no_version(self, evaluator, user, proposal):
        result = await evaluator.evaluate(user=user, proposal=proposal)
        assert result.overall_score is not None

    async def test_evaluate_usage_logged(self, evaluator, user, proposal, version):
        result = await evaluator.evaluate(user=user, proposal=proposal, version=version)
        logs = list(evaluator._usage_repo._store.values())
        assert len(logs) == 1
        assert logs[0].endpoint == "evaluate_proposal"
        assert logs[0].provider == "mock-evaluator"
        assert logs[0].total_tokens == 220

    async def test_evaluate_handles_invalid_json(self, evaluator, user, proposal, version):
        bad_provider = MockLLMProvider(response_content="not valid json at all")
        evaluator._llm_provider = bad_provider
        result = await evaluator.evaluate(user=user, proposal=proposal, version=version)
        assert result.overall_score == 0
        assert len(result.weaknesses) >= 1

    async def test_evaluate_handles_non_dict_response(self, evaluator, user, proposal, version):
        bad_provider = MockLLMProvider(response_content='"just a string"')
        evaluator._llm_provider = bad_provider
        result = await evaluator.evaluate(user=user, proposal=proposal, version=version)
        assert result.overall_score == 0

    async def test_evaluate_to_dict(self, evaluator, user, proposal, version):
        result = await evaluator.evaluate(user=user, proposal=proposal, version=version)
        d = result.to_dict()
        assert d["overall_score"] == 0.85
        assert "strengths" in d
        assert "weaknesses" in d
        assert "suggestions" in d
