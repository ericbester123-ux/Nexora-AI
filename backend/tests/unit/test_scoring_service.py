import uuid

import pytest
from app.models.ai_preference import AIPreference
from app.models.opportunity import Opportunity
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.opportunity_service import OpportunityService
from app.services.scoring_service import ScoreResult, ScoringService


class FakeOpportunityRepo:
    def __init__(self):
        self._opportunities: dict[uuid.UUID, Opportunity] = {}

    async def get_by_id(self, id):
        return self._opportunities.get(id)

    async def create(self, **fields):
        fields.setdefault("status", "new")
        fields.setdefault("is_remote", True)
        fields.setdefault("is_negotiable", False)
        fields.setdefault("is_ai_scored", False)
        fields.setdefault("currency", "USD")
        opp = Opportunity(id=uuid.uuid4(), **fields)
        self._opportunities[opp.id] = opp
        return opp

    async def get_all(self, user_id, skip=0, limit=20, **filters):
        items = [o for o in self._opportunities.values() if o.user_id == user_id]
        return items[skip:skip + limit], len(items)

    async def update(self, opportunity, **fields):
        for k, v in fields.items():
            setattr(opportunity, k, v)
        return opportunity


@pytest.fixture
def user():
    return User(
        id=uuid.uuid4(),
        email="test@test.com",
        hashed_password="hash",
        full_name="Test User",
        primary_skills=["python", "react", "docker"],
        secondary_skills=["aws", "postgresql"],
        years_of_experience=5,
    )


@pytest.fixture
def opportunity():
    return Opportunity(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        platform="freelancer",
        title="Python Developer Needed",
        skills=["Python", "React", "Docker"],
        budget_min=3000.0,
        budget_max=8000.0,
        category="Web Development",
        experience_level="intermediate",
        client_rating=4.5,
        client_payment_verified=True,
        client_reviews_count=10,
    )


@pytest.fixture
def prefs():
    return UserPreference(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        min_budget=2000,
        max_budget=10000,
        preferred_categories=["Web Development", "AI & Machine Learning"],
        preferred_technologies=["Python", "React"],
        min_client_rating=3.5,
        require_payment_verified=False,
    )


@pytest.fixture
def ai_prefs():
    return AIPreference(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        confidence_threshold=0.5,
    )


@pytest.fixture
def scoring_service():
    return ScoringService(OpportunityService(repository=FakeOpportunityRepo()))


class TestScoringService:
    async def test_score_high_match(self, scoring_service, user, opportunity, prefs, ai_prefs):
        result = await scoring_service.score_opportunity(opportunity, user, prefs, ai_prefs)
        assert result.score >= 0.6
        assert result.skills_score >= 0.5
        assert result.budget_score >= 0.5
        assert result.category_score >= 0.5
        assert result.match_reason != "Low match across all criteria"

    async def test_score_no_skills_match(self, scoring_service, prefs, ai_prefs):
        user = User(
            id=uuid.uuid4(),
            email="test@test.com",
            hashed_password="hash",
            full_name="Test",
            primary_skills=["java", "c++"],
            secondary_skills=None,
            years_of_experience=3,
        )
        opp = Opportunity(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            platform="freelancer",
            title="Rust Developer",
            skills=["Rust", "Assembly"],
            category="Systems",
            experience_level="expert",
        )
        result = await scoring_service.score_opportunity(opp, user, prefs, ai_prefs)
        assert result.skills_score == 0.0
        assert result.score < 0.6

    async def test_score_no_preferences(self, scoring_service, user, opportunity, ai_prefs):
        result = await scoring_service.score_opportunity(opportunity, user, None, ai_prefs)
        assert result.score >= 0.0
        assert result.score <= 1.0

    async def test_score_and_persist_updates_opportunity(self, scoring_service, user, opportunity, prefs, ai_prefs):
        service = scoring_service._opportunity_service
        repo = service._repo
        created = await repo.create(
            user_id=user.id,
            platform="freelancer",
            title="Test",
            skills=["Python"],
            category="Web Development",
            experience_level="intermediate",
        )
        result = await scoring_service.score_and_persist(created, user, prefs, ai_prefs)
        updated = await service.get_by_id(created.id, user_id=user.id)
        assert updated.is_ai_scored is True
        assert updated.ai_score == result.score
        assert updated.ai_match_reason == result.match_reason

    async def test_score_batch(self, scoring_service, user, prefs, ai_prefs):
        repo = scoring_service._opportunity_service._repo
        for i in range(5):
            await repo.create(
                user_id=user.id,
                platform="freelancer",
                title=f"Opp {i}",
                skills=["Python"],
                category="Web Development",
            )
        result = await scoring_service.score_batch(user, prefs, ai_prefs)
        assert result["scored"] == 5
        assert result["total"] == 5


class TestScoringComponents:
    @staticmethod
    def test_skills_score_match():
        user = User(id=uuid.uuid4(), email="a@b.com", hashed_password="h", full_name="T",
                     primary_skills=["python", "react"], secondary_skills=["docker"])
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", skills=["Python", "React"])
        score = ScoringService._score_skills(user, opp)
        assert score == 1.0

    @staticmethod
    def test_skills_score_partial():
        user = User(id=uuid.uuid4(), email="a@b.com", hashed_password="h", full_name="T",
                     primary_skills=["python", "java"], secondary_skills=None)
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T",
                           skills=["Python", "React", "Docker"])
        score = ScoringService._score_skills(user, opp)
        assert score == pytest.approx(1.0 / 3.0)

    @staticmethod
    def test_skills_score_no_user_skills():
        user = User(id=uuid.uuid4(), email="a@b.com", hashed_password="h", full_name="T",
                     primary_skills=None, secondary_skills=None)
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", skills=["Python"])
        score = ScoringService._score_skills(user, opp)
        assert score == 0.5

    @staticmethod
    def test_budget_score_in_range():
        prefs = UserPreference(id=uuid.uuid4(), user_id=uuid.uuid4(), min_budget=1000, max_budget=5000)
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", budget_min=2000, budget_max=4000)
        score = ScoringService._score_budget(prefs, opp)
        assert score >= 0.5

    @staticmethod
    def test_budget_score_out_of_range():
        prefs = UserPreference(id=uuid.uuid4(), user_id=uuid.uuid4(), min_budget=1000, max_budget=2000)
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", budget_min=5000, budget_max=10000)
        score = ScoringService._score_budget(prefs, opp)
        assert score == 0.0

    @staticmethod
    def test_category_score_match():
        prefs = UserPreference(id=uuid.uuid4(), user_id=uuid.uuid4(), preferred_categories=["Web Development", "Mobile"])
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", category="Web Development")
        assert ScoringService._score_category(prefs, opp) == 1.0

    @staticmethod
    def test_category_score_no_match():
        prefs = UserPreference(id=uuid.uuid4(), user_id=uuid.uuid4(), preferred_categories=["Mobile"])
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", category="DevOps")
        assert ScoringService._score_category(prefs, opp) == 0.0

    @staticmethod
    def test_experience_score_match():
        user = User(id=uuid.uuid4(), email="a@b.com", hashed_password="h", full_name="T", years_of_experience=3)
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", experience_level="intermediate")
        assert ScoringService._score_experience(user, opp) == 1.0

    @staticmethod
    def test_experience_score_no_match():
        user = User(id=uuid.uuid4(), email="a@b.com", hashed_password="h", full_name="T", years_of_experience=0)
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T", experience_level="expert")
        assert ScoringService._score_experience(user, opp) < 1.0

    @staticmethod
    def test_client_quality_verified():
        opp = Opportunity(id=uuid.uuid4(), user_id=uuid.uuid4(), platform="f", title="T",
                          client_payment_verified=True, client_rating=4.5)
        score = ScoringService._score_client_quality(None, opp)
        assert score >= 0.75
