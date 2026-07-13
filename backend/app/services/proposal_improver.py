import json
import uuid
from decimal import Decimal

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, NotFoundError, ValidationAppError
from app.infrastructure.llm import LLMConfig, LLMProvider, get_llm_provider, make_llm_config
from app.models.ai_usage_log import AIUsageLog
from app.models.opportunity import Opportunity
from app.models.proposal import Proposal
from app.models.proposal_version import ProposalVersion
from app.models.user import User
from app.repositories.ai_usage_log_repository import AIUsageLogRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.proposal_repository import ProposalRepository
from app.repositories.proposal_version_repository import ProposalVersionRepository

IMPROVE_PROMPT_VERSION = "1.0"

STYLE_INSTRUCTIONS = {
    "shorter": "Rewrite the proposal to be significantly shorter and more concise. Remove unnecessary details while keeping the core message.",
    "longer": "Expand the proposal with more detail, examples, and elaboration while maintaining quality.",
    "more_technical": "Increase technical depth. Use industry terminology, mention specific technologies, and demonstrate technical expertise.",
    "less_technical": "Simplify technical language for a non-technical audience. Focus on outcomes rather than implementation details.",
    "more_persuasive": "Strengthen the persuasive elements. Emphasize value proposition, past results, and client benefits.",
    "formal": "Rewrite in a formal, professional business tone. Use proper business language and structure.",
    "casual": "Rewrite in a friendly, conversational tone. Be approachable while remaining professional.",
    "custom": "",
}


class ProposalImprover:
    def __init__(
        self,
        proposal_repository: ProposalRepository,
        proposal_version_repository: ProposalVersionRepository,
        ai_usage_log_repository: AIUsageLogRepository,
        opportunity_repository: OpportunityRepository,
        llm_provider: LLMProvider | None = None,
    ):
        self._proposal_repo = proposal_repository
        self._version_repo = proposal_version_repository
        self._usage_repo = ai_usage_log_repository
        self._opp_repo = opportunity_repository
        self._llm_provider = llm_provider or get_llm_provider()

    async def improve(
        self,
        user: User,
        proposal_id: uuid.UUID,
        style: str,
        custom_instruction: str | None = None,
        focus_section: str | None = None,
    ) -> tuple[Proposal, ProposalVersion, AIUsageLog]:
        proposal = await self._proposal_repo.get_by_id(proposal_id)
        if proposal is None or proposal.user_id != user.id:
            raise NotFoundError("Proposal not found.")

        last_version = await self._version_repo.get_latest_version_number(proposal_id)
        prev_version = None
        if last_version > 0:
            versions, _ = await self._version_repo.get_by_proposal_id(proposal_id, limit=1)
            prev_version = versions[0] if versions else None

        opportunity = None
        if proposal.project_id:
            opportunity = await self._opp_repo.get_by_id(proposal.project_id)

        style_instr = STYLE_INSTRUCTIONS.get(style, "")
        if style == "custom" and custom_instruction:
            style_instr = custom_instruction

        prompt = self._build_improve_prompt(
            proposal=proposal,
            prev_version=prev_version,
            opportunity=opportunity,
            style_instruction=style_instr,
            focus_section=focus_section,
        )

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

        version_number = last_version + 1
        version = await self._version_repo.create(
            proposal_id=proposal_id,
            version_number=version_number,
            created_by="ai",
            change_summary=f"AI improvement: {style}" + (f" ({focus_section})" if focus_section else ""),
            cover_letter=parsed.get("coverLetter"),
            executive_summary=parsed.get("executiveSummary"),
            why_good_fit=parsed.get("whyGoodFit"),
            relevant_experience=parsed.get("relevantExperience"),
            bid_amount=float(parsed["recommendedBid"]) if parsed.get("recommendedBid") else None,
            bid_type=proposal.bid_type,
            estimated_duration=parsed.get("estimatedDeliveryTime"),
            milestones=parsed.get("suggestedMilestones"),
            risk_notes=parsed.get("riskNotes"),
            confidence_explanation=parsed.get("confidenceExplanation"),
            proposal_summary=parsed.get("proposalSummary"),
            raw_ai_response=response.content,
            prompt_version=IMPROVE_PROMPT_VERSION,
            model=response.model,
            temperature=config.temperature,
            tokens_used=response.total_tokens,
        )

        if parsed.get("coverLetter"):
            update_fields = {"cover_letter": parsed["coverLetter"]}
            if parsed.get("recommendedBid"):
                update_fields["bid_amount"] = Decimal(str(parsed["recommendedBid"]))
            if parsed.get("estimatedDeliveryTime"):
                update_fields["estimated_duration"] = parsed["estimatedDeliveryTime"]
            proposal = await self._proposal_repo.update(proposal, **update_fields)

        usage_log = await self._usage_repo.create(
            user_id=user.id,
            provider=self._llm_provider.provider_name,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost_usd=self._estimate_cost(response),
            latency_ms=response.latency_ms,
            endpoint=f"improve_proposal_{style}",
        )

        return proposal, version, usage_log

    def _build_improve_prompt(
        self,
        proposal: Proposal,
        prev_version: ProposalVersion | None,
        opportunity: Opportunity | None,
        style_instruction: str,
        focus_section: str | None,
    ) -> str:
        sections = ["## Current Proposal Content"]
        sections.append(f"Cover Letter: {proposal.cover_letter or '(empty)'}")
        sections.append(f"Bid Amount: {proposal.bid_amount or '(not set)'}")
        sections.append(f"Estimated Duration: {proposal.estimated_duration or '(not set)'}")

        if prev_version:
            sections.append("\n## Previous Version Content")
            sections.append(f"Cover Letter: {prev_version.cover_letter or '(empty)'}")
            if prev_version.executive_summary:
                sections.append(f"Executive Summary: {prev_version.executive_summary}")
            if prev_version.why_good_fit:
                sections.append(f"Why Good Fit: {prev_version.why_good_fit}")
            if prev_version.relevant_experience:
                sections.append(f"Relevant Experience: {prev_version.relevant_experience}")

        if opportunity:
            sections.append("\n## Opportunity Context")
            sections.append(f"Title: {opportunity.title}")
            if opportunity.description:
                sections.append(f"Description: {opportunity.description}")
            if opportunity.skills:
                sections.append(f"Required Skills: {', '.join(opportunity.skills)}")

        sections.append("\n## Improvement Instruction")
        sections.append(style_instruction)

        focus = ""
        if focus_section:
            focus = f"\nFocus only on improving the '{focus_section}' section. Keep other sections as-is."
        sections.append(focus)

        sections.append("""
Respond in valid JSON format with the same keys as the original:
coverLetter, executiveSummary, whyGoodFit, relevantExperience, recommendedBid, estimatedDeliveryTime, suggestedMilestones, riskNotes, confidenceExplanation, proposalSummary

Do NOT include markdown formatting in the JSON values.""")

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
        except json.JSONDecodeError as exc:
            raise ValidationAppError(f"AI response is not valid JSON: {exc}")

        if not isinstance(parsed, dict):
            raise ValidationAppError("AI response must be a JSON object.")

        return parsed

    @staticmethod
    def _estimate_cost(response) -> float:
        prompt_cost = (response.prompt_tokens / 1_000_000) * 0.15
        completion_cost = (response.completion_tokens / 1_000_000) * 0.60
        return round(prompt_cost + completion_cost, 6)
