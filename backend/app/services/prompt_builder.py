from app.models.ai_preference import AIPreference
from app.models.opportunity import Opportunity
from app.models.proposal_template import ProposalTemplate
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.scoring_service import ScoreResult

PROMPT_VERSION = "1.0"


class PromptContext:
    def __init__(
        self,
        user: User,
        opportunity: Opportunity,
        score_result: ScoreResult | None = None,
        user_preferences: UserPreference | None = None,
        ai_preferences: AIPreference | None = None,
        proposal_template: ProposalTemplate | None = None,
        historical_win_rate: float | None = None,
    ):
        self.user = user
        self.opportunity = opportunity
        self.score_result = score_result
        self.user_preferences = user_preferences
        self.ai_preferences = ai_preferences
        self.proposal_template = proposal_template
        self.historical_win_rate = historical_win_rate


class PromptBuilder:
    def build(self, ctx: PromptContext) -> str:
        sections: list[str] = []

        sections.append(self._build_user_profile(ctx))
        sections.append(self._build_opportunity(ctx))
        if ctx.score_result:
            sections.append(self._build_scoring(ctx))
        sections.append(self._build_preferences(ctx))
        if ctx.proposal_template:
            sections.append(self._build_template(ctx))
        if ctx.historical_win_rate is not None:
            sections.append(self._build_history(ctx))
        sections.append(self._build_instructions(ctx))

        return "\n\n".join(sections)

    @staticmethod
    def _build_user_profile(ctx: PromptContext) -> str:
        u = ctx.user
        lines = ["## Freelancer Profile"]
        if u.full_name:
            lines.append(f"Name: {u.full_name}")
        if u.primary_skills:
            lines.append(f"Primary Skills: {', '.join(u.primary_skills)}")
        if u.secondary_skills:
            lines.append(f"Secondary Skills: {', '.join(u.secondary_skills)}")
        if u.years_of_experience is not None:
            lines.append(f"Years of Experience: {u.years_of_experience}")
        if u.portfolio_url:
            lines.append(f"Portfolio: {u.portfolio_url}")
        if u.biography:
            lines.append(f"Biography: {u.biography}")
        if u.country:
            lines.append(f"Country: {u.country}")
        return "\n".join(lines)

    @staticmethod
    def _build_opportunity(ctx: PromptContext) -> str:
        o = ctx.opportunity
        lines = ["## Opportunity Details"]
        lines.append(f"Title: {o.title}")
        if o.description:
            lines.append(f"Description: {o.description}")
        if o.category:
            lines.append(f"Category: {o.category}")
        if o.subcategory:
            lines.append(f"Subcategory: {o.subcategory}")
        if o.skills:
            lines.append(f"Required Skills: {', '.join(o.skills)}")
        if o.budget_min is not None and o.budget_max is not None:
            lines.append(f"Budget: ${o.budget_min:.2f} - ${o.budget_max:.2f}")
        elif o.budget_max is not None:
            lines.append(f"Budget: Up to ${o.budget_max:.2f}")
        if o.budget_type:
            lines.append(f"Budget Type: {o.budget_type}")
        if o.experience_level:
            lines.append(f"Experience Level: {o.experience_level}")
        if o.duration:
            lines.append(f"Duration: {o.duration}")
        if o.project_type:
            lines.append(f"Project Type: {o.project_type}")
        if o.country:
            lines.append(f"Client Country: {o.country}")
        return "\n".join(lines)

    @staticmethod
    def _build_scoring(ctx: PromptContext) -> str:
        s = ctx.score_result
        lines = ["## AI Match Score"]
        lines.append(f"Overall Score: {s.score:.2f}")
        lines.append(f"Skills Match: {s.skills_score:.2f}")
        lines.append(f"Budget Compatibility: {s.budget_score:.2f}")
        lines.append(f"Category Match: {s.category_score:.2f}")
        lines.append(f"Experience Alignment: {s.experience_score:.2f}")
        lines.append(f"Client Quality: {s.client_quality_score:.2f}")
        lines.append(f"Match Explanation: {s.match_reason}")
        return "\n".join(lines)

    @staticmethod
    def _build_preferences(ctx: PromptContext) -> str:
        ap = ctx.ai_preferences
        if ap is None:
            return ""
        lines = ["## Writing Preferences"]
        lines.append(f"Tone: {ap.proposal_tone}")
        lines.append(f"Length: {ap.proposal_length}")
        lines.append(f"Writing Style: {ap.writing_style}")
        lines.append(f"Include Portfolio: {'Yes' if ap.automatically_include_portfolio else 'No'}")
        lines.append(f"Bid Recommendation Style: {ap.bid_recommendation_style}")
        return "\n".join(lines)

    @staticmethod
    def _build_template(ctx: PromptContext) -> str:
        t = ctx.proposal_template
        lines = ["## Proposal Template"]
        lines.append(f"Template Name: {t.name}")
        if t.description:
            lines.append(f"Description: {t.description}")
        lines.append(f"Template Content:\n{t.cover_letter_template}")
        return "\n".join(lines)

    @staticmethod
    def _build_history(ctx: PromptContext) -> str:
        return f"## Historical Performance\nEstimated Win Rate: {ctx.historical_win_rate:.1%}"

    @staticmethod
    def _build_instructions(ctx: PromptContext) -> str:
        ap = ctx.ai_preferences
        length_guide = {
            "short": "Keep the proposal brief (1-2 paragraphs).",
            "medium": "Write a moderate-length proposal (3-5 paragraphs).",
            "long": "Write a detailed, comprehensive proposal.",
        }
        length_instr = length_guide.get(ap.proposal_length if ap else "medium", "Write a moderate-length proposal.")

        return f"""## Instructions

Generate a professional proposal for this freelance opportunity. {length_instr}

The proposal must be structured with the following sections:

1. **Cover Letter** — A personalized introduction addressing the client and demonstrating understanding of their project.
2. **Executive Summary** — Brief overview of your proposed approach.
3. **Why I'm a Good Fit** — Connect your skills and experience to the project requirements.
4. **Relevant Experience** — Specific examples of similar work completed.
5. **Recommended Bid** — Suggested bid amount and justification based on the opportunity budget.
6. **Estimated Delivery Time** — Realistic timeline for completion.
7. **Suggested Milestones** (optional) — Key deliverables and phases.
8. **Risk Notes** — Any potential challenges and mitigation strategies.
9. **Confidence Explanation** — Why you are confident in delivering quality results.
10. **Proposal Summary** — One-paragraph summary for quick review.

Respond in valid JSON format with keys matching these section names (camelCase):
coverLetter, executiveSummary, whyGoodFit, relevantExperience, recommendedBid, estimatedDeliveryTime, suggestedMilestones, riskNotes, confidenceExplanation, proposalSummary

Do NOT include markdown formatting in the JSON values."""
