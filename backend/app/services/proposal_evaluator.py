import json
import uuid

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.infrastructure.llm import LLMConfig, LLMProvider, get_llm_provider, make_llm_config
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.models.proposal_version import ProposalVersion
from app.models.user import User
from app.repositories.ai_usage_log_repository import AIUsageLogRepository
from app.repositories.opportunity_repository import OpportunityRepository

EVALUATE_PROMPT_VERSION = "1.0"


class EvaluationResult:
    def __init__(
        self,
        overall_score: float,
        completeness_score: float,
        persuasiveness_score: float,
        relevance_score: float,
        clarity_score: float,
        formatting_score: float,
        strengths: list[str],
        weaknesses: list[str],
        suggestions: list[str],
        raw_response: str,
    ):
        self.overall_score = round(overall_score, 2)
        self.completeness_score = round(completeness_score, 2)
        self.persuasiveness_score = round(persuasiveness_score, 2)
        self.relevance_score = round(relevance_score, 2)
        self.clarity_score = round(clarity_score, 2)
        self.formatting_score = round(formatting_score, 2)
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.suggestions = suggestions
        self.raw_response = raw_response

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "completeness_score": self.completeness_score,
            "persuasiveness_score": self.persuasiveness_score,
            "relevance_score": self.relevance_score,
            "clarity_score": self.clarity_score,
            "formatting_score": self.formatting_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
        }


class ProposalEvaluator:
    def __init__(
        self,
        ai_usage_log_repository: AIUsageLogRepository,
        opportunity_repository: OpportunityRepository,
        llm_provider: LLMProvider | None = None,
    ):
        self._usage_repo = ai_usage_log_repository
        self._opp_repo = opportunity_repository
        self._llm_provider = llm_provider or get_llm_provider()

    async def evaluate(
        self,
        user: User,
        proposal: Proposal,
        version: ProposalVersion | None = None,
        opportunity: Opportunity | None = None,
    ) -> EvaluationResult:
        if opportunity is None and proposal.project_id:
            opportunity = await self._opp_repo.get_by_id(proposal.project_id)

        prompt = self._build_evaluation_prompt(proposal, version, opportunity)

        settings = get_settings()
        config = make_llm_config(settings)
        config.temperature = 0.3
        config.max_tokens = 1024
        config.system_prompt = "You are an expert proposal evaluator. Score proposals objectively."

        last_error = None
        for attempt in range(config.retry_count + 1):
            try:
                response = await self._llm_provider.generate(prompt, config)
                break
            except Exception as exc:
                last_error = exc
                if attempt < config.retry_count:
                    continue
                raise ExternalServiceError(f"AI provider failed after {config.retry_count + 1} attempts: {last_error}")

        parsed = self._parse_response(response.content)

        result = EvaluationResult(
            overall_score=parsed.get("overallScore", 0),
            completeness_score=parsed.get("completenessScore", 0),
            persuasiveness_score=parsed.get("persuasivenessScore", 0),
            relevance_score=parsed.get("relevanceScore", 0),
            clarity_score=parsed.get("clarityScore", 0),
            formatting_score=parsed.get("formattingScore", 0),
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            suggestions=parsed.get("suggestions", []),
            raw_response=response.content,
        )

        await self._usage_repo.create(
            user_id=user.id,
            provider=self._llm_provider.provider_name,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost_usd=self._estimate_cost(response),
            latency_ms=response.latency_ms,
            endpoint="evaluate_proposal",
        )

        return result

    def _build_evaluation_prompt(
        self,
        proposal: Proposal,
        version: ProposalVersion | None,
        opportunity: Opportunity | None,
    ) -> str:
        sections = ["## Proposal to Evaluate"]

        content = version.cover_letter if version and version.cover_letter else proposal.cover_letter or ""
        sections.append(f"Cover Letter: {content}")

        if version:
            if version.executive_summary:
                sections.append(f"Executive Summary: {version.executive_summary}")
            if version.why_good_fit:
                sections.append(f"Why Good Fit: {version.why_good_fit}")
            if version.relevant_experience:
                sections.append(f"Relevant Experience: {version.relevant_experience}")
            if version.proposal_summary:
                sections.append(f"Proposal Summary: {version.proposal_summary}")

        sections.append(f"Bid Amount: {proposal.bid_amount or '(not set)'}")
        sections.append(f"Estimated Duration: {proposal.estimated_duration or '(not set)'}")

        if opportunity:
            sections.append("\n## Opportunity Context")
            sections.append(f"Title: {opportunity.title}")
            if opportunity.description:
                sections.append(f"Description: {opportunity.description}")
            if opportunity.skills:
                sections.append(f"Required Skills: {', '.join(opportunity.skills)}")
            if opportunity.budget_min is not None and opportunity.budget_max is not None:
                sections.append(f"Budget Range: ${opportunity.budget_min} - ${opportunity.budget_max}")

        sections.append("""
## Evaluation Criteria

Score each category from 0.0 to 1.0 and provide specific feedback:

1. **completenessScore** - Does the proposal cover all necessary sections? Is the bid amount present?
2. **persuasivenessScore** - How compelling is the proposal? Does it convince the client?
3. **relevanceScore** - How well does the proposal address the opportunity requirements?
4. **clarityScore** - Is the writing clear, well-structured, and error-free?
5. **formattingScore** - Is the proposal well-formatted and professional?

Also provide:
- **overallScore** - Weighted average of all scores
- **strengths** - List of 2-4 specific strengths
- **weaknesses** - List of 2-4 specific areas for improvement
- **suggestions** - List of 2-4 actionable suggestions

Respond in valid JSON format only with keys: overallScore, completenessScore, persuasivenessScore, relevanceScore, clarityScore, formattingScore, strengths, weaknesses, suggestions""")

        return "\n\n".join(sections)

    @staticmethod
    def _parse_response(content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "overallScore": 0,
                "completenessScore": 0,
                "persuasivenessScore": 0,
                "relevanceScore": 0,
                "clarityScore": 0,
                "formattingScore": 0,
                "strengths": [],
                "weaknesses": ["Unable to parse evaluation response"],
                "suggestions": ["Try evaluating again"],
            }

        if not isinstance(parsed, dict):
            return {
                "overallScore": 0,
                "completenessScore": 0,
                "persuasivenessScore": 0,
                "relevanceScore": 0,
                "clarityScore": 0,
                "formattingScore": 0,
                "strengths": [],
                "weaknesses": ["Invalid evaluation response format"],
                "suggestions": ["Try evaluating again"],
            }

        return parsed

    @staticmethod
    def _estimate_cost(response) -> float:
        prompt_cost = (response.prompt_tokens / 1_000_000) * 0.15
        completion_cost = (response.completion_tokens / 1_000_000) * 0.60
        return round(prompt_cost + completion_cost, 6)
