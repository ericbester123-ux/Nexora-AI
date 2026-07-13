from decimal import Decimal
from typing import Any

from app.models.ai_preference import AIPreference
from app.models.opportunity import Opportunity
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.opportunity_service import OpportunityService

SKILL_WEIGHT = 0.40
BUDGET_WEIGHT = 0.20
CATEGORY_WEIGHT = 0.20
EXPERIENCE_WEIGHT = 0.10
CLIENT_QUALITY_WEIGHT = 0.10


class ScoreResult:
    def __init__(
        self,
        score: float,
        skills_score: float,
        budget_score: float,
        category_score: float,
        experience_score: float,
        client_quality_score: float,
        match_reason: str,
    ):
        self.score = round(score, 4)
        self.skills_score = round(skills_score, 4)
        self.budget_score = round(budget_score, 4)
        self.category_score = round(category_score, 4)
        self.experience_score = round(experience_score, 4)
        self.client_quality_score = round(client_quality_score, 4)
        self.match_reason = match_reason


class ScoringService:
    def __init__(self, opportunity_service: OpportunityService):
        self._opportunity_service = opportunity_service

    async def score_opportunity(
        self,
        opportunity: Opportunity,
        user: User,
        user_preferences: UserPreference | None,
        ai_preferences: AIPreference | None,
    ) -> ScoreResult:
        skills_score = self._score_skills(user, opportunity)
        budget_score = self._score_budget(user_preferences, opportunity)
        category_score = self._score_category(user_preferences, opportunity)
        experience_score = self._score_experience(user, opportunity)
        client_quality_score = self._score_client_quality(user_preferences, opportunity)

        total = (
            skills_score * SKILL_WEIGHT
            + budget_score * BUDGET_WEIGHT
            + category_score * CATEGORY_WEIGHT
            + experience_score * EXPERIENCE_WEIGHT
            + client_quality_score * CLIENT_QUALITY_WEIGHT
        )

        reasons: list[str] = []
        if skills_score >= 0.5:
            reasons.append(f"Skills match ({self._format_pct(skills_score)})")
        if budget_score >= 0.5:
            reasons.append(f"Budget in range ({self._format_pct(budget_score)})")
        if category_score >= 0.5:
            reasons.append(f"Category matches ({self._format_pct(category_score)})")
        if client_quality_score >= 0.5:
            reasons.append("Client quality meets criteria")

        match_reason = "; ".join(reasons) if reasons else "Low match across all criteria"

        return ScoreResult(
            score=total,
            skills_score=skills_score,
            budget_score=budget_score,
            category_score=category_score,
            experience_score=experience_score,
            client_quality_score=client_quality_score,
            match_reason=match_reason,
        )

    async def score_and_persist(
        self,
        opportunity: Opportunity,
        user: User,
        user_preferences: UserPreference | None,
        ai_preferences: AIPreference | None,
    ) -> ScoreResult:
        result = await self.score_opportunity(opportunity, user, user_preferences, ai_preferences)
        threshold = (ai_preferences.confidence_threshold if ai_preferences else 0.7)
        await self._opportunity_service.update(
            id=opportunity.id,
            user_id=user.id,
            is_ai_scored=True,
            ai_score=result.score,
            ai_match_reason=result.match_reason,
        )
        return result

    async def score_batch(self, user: User, user_preferences: UserPreference | None, ai_preferences: AIPreference | None) -> dict[str, Any]:
        all_opps, _ = await self._opportunity_service.get_all(user_id=user.id)
        unscored = [o for o in all_opps if not o.is_ai_scored]
        scored_count = 0
        for opp in unscored:
            result = await self.score_opportunity(opp, user, user_preferences, ai_preferences)
            threshold = (ai_preferences.confidence_threshold if ai_preferences else 0.7)
            await self._opportunity_service.update(
                id=opp.id,
                user_id=user.id,
                is_ai_scored=True,
                ai_score=result.score,
                ai_match_reason=result.match_reason,
            )
            scored_count += 1
        return {"scored": scored_count, "total": len(all_opps), "unscored": len(unscored) - scored_count}

    @staticmethod
    def _score_skills(user: User, opportunity: Opportunity) -> float:
        all_skills: set[str] = set()
        if user.primary_skills:
            all_skills.update(s.lower().strip() for s in user.primary_skills)
        if user.secondary_skills:
            all_skills.update(s.lower().strip() for s in user.secondary_skills)
        if not all_skills or not opportunity.skills:
            return 0.5
        opp_skills = set(s.lower().strip() for s in opportunity.skills)
        if not opp_skills:
            return 0.5
        matches = all_skills & opp_skills
        return len(matches) / len(opp_skills)

    @staticmethod
    def _score_budget(prefs: UserPreference | None, opportunity: Opportunity) -> float:
        if prefs is None:
            return 0.5
        min_budget = float(prefs.min_budget) if prefs.min_budget is not None else None
        max_budget = float(prefs.max_budget) if prefs.max_budget is not None else None
        if min_budget is None and max_budget is None:
            return 0.5
        opp_min = opportunity.budget_min or 0
        opp_max = opportunity.budget_max or float("inf")
        if opp_max == float("inf") and opp_min == 0:
            return 0.3
        if min_budget is not None and max_budget is not None:
            if opp_min <= max_budget and opp_max >= min_budget:
                overlap_min = max(min_budget, opp_min)
                overlap_max = min(max_budget, opp_max)
                overlap = max(0, overlap_max - overlap_min)
                user_range = max_budget - min_budget
                if user_range > 0:
                    return min(1.0, overlap / user_range)
                return 0.5 if min_budget <= opp_max <= max_budget else 0.0
            return 0.0
        if min_budget is not None:
            return 1.0 if opp_max >= min_budget else 0.0
        if max_budget is not None:
            return 1.0 if opp_min <= max_budget else 0.0
        return 0.5

    @staticmethod
    def _score_category(prefs: UserPreference | None, opportunity: Opportunity) -> float:
        if prefs is None or not prefs.preferred_categories or not opportunity.category:
            return 0.5
        opp_cat = opportunity.category.lower().strip()
        preferred = [c.lower().strip() for c in prefs.preferred_categories]
        return 1.0 if any(p in opp_cat or opp_cat in p for p in preferred) else 0.0

    @staticmethod
    def _score_experience(user: User, opportunity: Opportunity) -> float:
        if user.years_of_experience is None or not opportunity.experience_level:
            return 0.5
        exp = user.years_of_experience
        level_map = {
            "beginner": (0, 2),
            "intermediate": (2, 5),
            "expert": (5, 100),
        }
        level_range = level_map.get(opportunity.experience_level.lower(), None)
        if level_range is None:
            return 0.5
        if level_range[0] <= exp <= level_range[1]:
            return 1.0
        if exp < level_range[0]:
            return max(0.0, 1.0 - (level_range[0] - exp) / level_range[0])
        return max(0.0, 1.0 - (exp - level_range[1]) / exp)

    @staticmethod
    def _score_client_quality(prefs: UserPreference | None, opportunity: Opportunity) -> float:
        score = 0.5
        if prefs is not None and prefs.require_payment_verified:
            if opportunity.client_payment_verified is not None:
                return 1.0 if opportunity.client_payment_verified else 0.0
            return 0.0
        if prefs is not None and prefs.min_client_rating is not None:
            if opportunity.client_rating is not None:
                if opportunity.client_rating >= prefs.min_client_rating:
                    score = min(1.0, score + 0.25)
                else:
                    score = max(0.0, score - 0.25)
        if opportunity.client_payment_verified:
            score = min(1.0, score + 0.25)
        if opportunity.client_rating is not None and opportunity.client_rating >= 4.0:
            score = min(1.0, score + 0.25)
        return score

    @staticmethod
    def _format_pct(value: float) -> str:
        return f"{int(value * 100)}%"
