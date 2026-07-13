import uuid

import pytest

from app.models.ai_preference import AIPreference
from app.models.opportunity import Opportunity
from app.models.proposal_template import ProposalTemplate
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.prompt_builder import PromptBuilder, PromptContext
from app.services.scoring_service import ScoreResult


@pytest.fixture
def builder():
    return PromptBuilder()


@pytest.fixture
def user():
    return User(
        id=uuid.uuid4(),
        email="freelancer@example.com",
        full_name="Alice Freelancer",
        primary_skills=["Python", "FastAPI", "PostgreSQL"],
        secondary_skills=["Docker", "AWS"],
        years_of_experience=5,
        biography="Full-stack developer with 5 years of experience.",
        country="US",
        portfolio_url="https://github.com/alice",
        hashed_password="",
    )


@pytest.fixture
def opportunity():
    return Opportunity(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        platform="upwork",
        external_id="ext-123",
        title="Build a REST API with FastAPI",
        description="We need an experienced developer to build a REST API for our SaaS platform.",
        category="Web Development",
        subcategory="API Development",
        skills=["Python", "FastAPI", "PostgreSQL"],
        budget_min=5000.0,
        budget_max=10000.0,
        budget_type="fixed",
        experience_level="intermediate",
        duration="1-3 months",
        project_type="ongoing",
        country="US",
    )


@pytest.fixture
def score_result():
    return ScoreResult(
        score=0.85,
        skills_score=0.9,
        budget_score=0.8,
        category_score=1.0,
        experience_score=0.7,
        client_quality_score=0.75,
        match_reason="Skills match (90%); Budget in range (80%); Category matches (100%)",
    )


@pytest.fixture
def ai_prefs():
    pref = AIPreference(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        proposal_tone="professional",
        proposal_length="medium",
        writing_style="concise",
        automatically_include_portfolio=True,
        bid_recommendation_style="balanced",
    )
    pref.ai_enabled = True
    pref.confidence_threshold = 0.7
    pref.ai_learning_enabled = True
    return pref


def test_build_prompt_with_all_fields(builder, user, opportunity, score_result, ai_prefs):
    template = ProposalTemplate(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Standard Template",
        description="A standard proposal template",
        cover_letter_template="Dear {client}, I am excited to apply...",
        is_default=True,
    )
    ctx = PromptContext(
        user=user,
        opportunity=opportunity,
        score_result=score_result,
        user_preferences=UserPreference(id=uuid.uuid4(), user_id=user.id),
        ai_preferences=ai_prefs,
        proposal_template=template,
        historical_win_rate=0.75,
    )
    prompt = builder.build(ctx)
    assert "Alice Freelancer" in prompt
    assert "Build a REST API with FastAPI" in prompt
    assert "Overall Score: 0.85" in prompt
    assert "Tone: professional" in prompt
    assert "Standard Template" in prompt
    assert "Estimated Win Rate: 75.0%" in prompt
    assert "coverLetter" in prompt


def test_build_prompt_partial_data(builder, user, opportunity):
    user.primary_skills = None
    user.secondary_skills = None
    user.years_of_experience = None
    user.biography = None
    user.country = None
    user.portfolio_url = None
    opportunity.description = None
    opportunity.skills = None
    opportunity.budget_min = None
    opportunity.budget_max = None
    ctx = PromptContext(user=user, opportunity=opportunity)
    prompt = builder.build(ctx)
    assert "Alice Freelancer" in prompt
    assert "Build a REST API with FastAPI" in prompt
    assert "Primary Skills:" not in prompt
    assert "Required Skills:" not in prompt


def test_build_prompt_without_opportunity(builder, user, opportunity):
    ctx = PromptContext(user=user, opportunity=opportunity)
    prompt = builder.build(ctx)
    assert "Freelancer Profile" in prompt
    assert "Opportunity Details" in prompt
    assert "Overall Score:" not in prompt


def test_build_prompt_without_preferences(builder, user, opportunity):
    ctx = PromptContext(user=user, opportunity=opportunity)
    prompt = builder.build(ctx)
    assert "Writing Preferences" not in prompt
    assert "Tone:" not in prompt


def test_build_prompt_without_score(builder, user, opportunity, ai_prefs):
    ctx = PromptContext(user=user, opportunity=opportunity, ai_preferences=ai_prefs)
    prompt = builder.build(ctx)
    assert "Writing Preferences" in prompt
    assert "Overall Score:" not in prompt
    assert "Instructions" in prompt


@pytest.fixture
def ai_prefs_short():
    pref = AIPreference(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        proposal_tone="casual",
        proposal_length="short",
        writing_style="storytelling",
        automatically_include_portfolio=False,
        bid_recommendation_style="aggressive",
    )
    return pref


def test_build_prompt_short_length_instruction(builder, user, opportunity, ai_prefs_short):
    ctx = PromptContext(
        user=user,
        opportunity=opportunity,
        ai_preferences=ai_prefs_short,
    )
    prompt = builder.build(ctx)
    assert "Keep the proposal brief (1-2 paragraphs)." in prompt


def test_build_prompt_medium_length_instruction(builder, user, opportunity, ai_prefs):
    ctx = PromptContext(
        user=user,
        opportunity=opportunity,
        ai_preferences=ai_prefs,
    )
    prompt = builder.build(ctx)
    assert "Write a moderate-length proposal (3-5 paragraphs)." in prompt


def test_build_prompt_long_length_instruction(builder, user, opportunity):
    prefs = AIPreference(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        proposal_tone="professional",
        proposal_length="long",
        writing_style="concise",
        automatically_include_portfolio=True,
        bid_recommendation_style="balanced",
    )
    ctx = PromptContext(user=user, opportunity=opportunity, ai_preferences=prefs)
    prompt = builder.build(ctx)
    assert "Write a detailed, comprehensive proposal." in prompt


def test_build_prompt_with_template_injection(builder, user, opportunity):
    template = ProposalTemplate(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Custom Template",
        cover_letter_template="I have been working with these technologies for years.",
    )
    ctx = PromptContext(
        user=user,
        opportunity=opportunity,
        proposal_template=template,
    )
    prompt = builder.build(ctx)
    assert "Custom Template" in prompt
    assert "I have been working with these technologies for years." in prompt


def test_build_prompt_edge_case_empty_skills(builder, user, opportunity):
    user.primary_skills = []
    user.secondary_skills = []
    opportunity.skills = []
    ctx = PromptContext(user=user, opportunity=opportunity)
    prompt = builder.build(ctx)
    assert "Primary Skills:" not in prompt
    assert "Required Skills:" not in prompt
