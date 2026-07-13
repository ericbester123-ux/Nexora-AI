import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, NotFoundError, ValidationAppError
from app.infrastructure.llm import LLMConfig, LLMProvider, OpenAIProvider, make_llm_config
from app.models.ai_preference import AIPreference
from app.models.ai_usage_log import AIUsageLog
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.models.proposal_template import ProposalTemplate
from app.models.proposal_version import ProposalVersion
from app.models.user import User
from app.models.user_preference import UserPreference
from app.repositories.ai_usage_log_repository import AIUsageLogRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.proposal_repository import ProposalRepository
from app.repositories.proposal_template_repository import ProposalTemplateRepository
from app.repositories.proposal_version_repository import ProposalVersionRepository
from app.services.prompt_builder import PromptBuilder, PromptContext
from app.services.scoring_service import ScoreResult, ScoringService

PROMPT_VERSION = "1.0"


class ProposalGenerationService:
    def __init__(
        self,
        proposal_repository: ProposalRepository,
        proposal_version_repository: ProposalVersionRepository,
        ai_usage_log_repository: AIUsageLogRepository,
        opportunity_repository: OpportunityRepository,
        proposal_template_repository: ProposalTemplateRepository,
        scoring_service: ScoringService,
        llm_provider: LLMProvider | None = None,
    ):
        self._proposal_repo = proposal_repository
        self._version_repo = proposal_version_repository
        self._usage_repo = ai_usage_log_repository
        self._opportunity_repo = opportunity_repository
        self._template_repo = proposal_template_repository
        self._scoring_service = scoring_service
        self._llm_provider = llm_provider or OpenAIProvider()
        self._prompt_builder = PromptBuilder()

    async def generate_proposal(
        self,
        user: User,
        opportunity_id: uuid.UUID,
        user_preferences: UserPreference | None = None,
        ai_preferences: AIPreference | None = None,
    ) -> tuple[Proposal, ProposalVersion, AIUsageLog]:
        settings = get_settings()

        opportunity = await self._opportunity_repo.get_by_id(opportunity_id)
        if opportunity is None or opportunity.user_id != user.id:
            raise NotFoundError("Opportunity not found.")

        score_result = None
        if opportunity.is_ai_scored and opportunity.ai_score is not None:
            score_result = ScoreResult(
                score=opportunity.ai_score,
                skills_score=0,
                budget_score=0,
                category_score=0,
                experience_score=0,
                client_quality_score=0,
                match_reason=opportunity.ai_match_reason or "",
            )

        template = None
        templates, _ = await self._template_repo.get_by_user_id(user.id, is_active=True)
        if templates:
            default = next((t for t in templates if t.is_default), templates[0])
            template = default

        ctx = PromptContext(
            user=user,
            opportunity=opportunity,
            score_result=score_result,
            user_preferences=user_preferences,
            ai_preferences=ai_preferences,
            proposal_template=template,
        )

        prompt = self._prompt_builder.build(ctx)

        config = make_llm_config(settings)

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

        proposal = await self._proposal_repo.create(
            user_id=user.id,
            project_id=uuid.uuid4(),
            status="ai_generated",
            cover_letter=parsed.get("coverLetter", ""),
            bid_amount=Decimal(str(parsed["recommendedBid"])) if parsed.get("recommendedBid") else None,
            bid_type="fixed",
            currency="USD",
            estimated_duration=parsed.get("estimatedDeliveryTime"),
            ai_generated=True,
            ai_generation_version=PROMPT_VERSION,
            ai_confidence_score=score_result.score if score_result else None,
            requires_human_approval=True,
        )

        version_number = 1
        version = await self._version_repo.create(
            proposal_id=proposal.id,
            version_number=version_number,
            created_by="ai",
            change_summary="AI-generated proposal",
            cover_letter=parsed.get("coverLetter"),
            executive_summary=parsed.get("executiveSummary"),
            why_good_fit=parsed.get("whyGoodFit"),
            relevant_experience=parsed.get("relevantExperience"),
            bid_amount=float(parsed["recommendedBid"]) if parsed.get("recommendedBid") else None,
            bid_type="fixed",
            estimated_duration=parsed.get("estimatedDeliveryTime"),
            milestones=parsed.get("suggestedMilestones"),
            risk_notes=parsed.get("riskNotes"),
            confidence_explanation=parsed.get("confidenceExplanation"),
            proposal_summary=parsed.get("proposalSummary"),
            raw_ai_response=response.content,
            prompt_version=PROMPT_VERSION,
            model=response.model,
            temperature=config.temperature,
            tokens_used=response.total_tokens,
        )

        usage_log = await self._usage_repo.create(
            user_id=user.id,
            provider=self._llm_provider.provider_name,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost_usd=self._estimate_cost(response),
            latency_ms=response.latency_ms,
            endpoint="generate_proposal",
        )

        return proposal, version, usage_log

    async def regenerate(
        self,
        user: User,
        proposal_id: uuid.UUID,
        user_preferences: UserPreference | None = None,
        ai_preferences: AIPreference | None = None,
    ) -> tuple[Proposal, ProposalVersion, AIUsageLog]:
        existing = await self._proposal_repo.get_by_id(proposal_id)
        if existing is None or existing.user_id != user.id:
            raise NotFoundError("Proposal not found.")

        opportunity = None
        if existing.project_id:
            opportunity = await self._opportunity_repo.get_by_id(existing.project_id)

        score_result = None
        if opportunity and opportunity.is_ai_scored and opportunity.ai_score is not None:
            score_result = ScoreResult(
                score=opportunity.ai_score,
                skills_score=0,
                budget_score=0,
                category_score=0,
                experience_score=0,
                client_quality_score=0,
                match_reason=opportunity.ai_match_reason or "",
            )

        template = await self._template_repo.get_by_id(existing.template_id) if existing.template_id else None
        if template is None:
            templates, _ = await self._template_repo.get_by_user_id(user.id, is_active=True)
            if templates:
                template = next((t for t in templates if t.is_default), templates[0])

        ctx = PromptContext(
            user=user,
            opportunity=opportunity or Opportunity(id=uuid.uuid4(), user_id=user.id, platform="", title=""),
            score_result=score_result,
            user_preferences=user_preferences,
            ai_preferences=ai_preferences,
            proposal_template=template,
        )

        prompt = self._prompt_builder.build(ctx)

        settings = get_settings()
        config = make_llm_config(settings)

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

        prev_version = await self._version_repo.get_latest_version_number(proposal_id)
        version_number = prev_version + 1

        version = await self._version_repo.create(
            proposal_id=proposal_id,
            version_number=version_number,
            created_by="ai",
            change_summary="AI regeneration",
            cover_letter=parsed.get("coverLetter"),
            executive_summary=parsed.get("executiveSummary"),
            why_good_fit=parsed.get("whyGoodFit"),
            relevant_experience=parsed.get("relevantExperience"),
            bid_amount=float(parsed["recommendedBid"]) if parsed.get("recommendedBid") else None,
            bid_type="fixed",
            estimated_duration=parsed.get("estimatedDeliveryTime"),
            milestones=parsed.get("suggestedMilestones"),
            risk_notes=parsed.get("riskNotes"),
            confidence_explanation=parsed.get("confidenceExplanation"),
            proposal_summary=parsed.get("proposalSummary"),
            raw_ai_response=response.content,
            prompt_version=PROMPT_VERSION,
            model=response.model,
            temperature=config.temperature,
            tokens_used=response.total_tokens,
        )

        usage_log = await self._usage_repo.create(
            user_id=user.id,
            provider=self._llm_provider.provider_name,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost_usd=self._estimate_cost(response),
            latency_ms=response.latency_ms,
            endpoint="regenerate_proposal",
        )

        return existing, version, usage_log

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
        except json.JSONDecodeError as exc:
            raise ValidationAppError(f"AI response is not valid JSON: {exc}")

        if not isinstance(parsed, dict):
            raise ValidationAppError("AI response must be a JSON object.")

        required = ["coverLetter", "executiveSummary", "whyGoodFit", "relevantExperience", "proposalSummary"]
        missing = [k for k in required if k not in parsed]
        if missing:
            raise ValidationAppError(f"AI response missing required sections: {', '.join(missing)}")

        if not parsed.get("coverLetter"):
            raise ValidationAppError("Cover letter must not be empty.")

        return parsed

    @staticmethod
    def _estimate_cost(response) -> float:
        prompt_cost = (response.prompt_tokens / 1_000_000) * 0.15
        completion_cost = (response.completion_tokens / 1_000_000) * 0.60
        return round(prompt_cost + completion_cost, 6)
