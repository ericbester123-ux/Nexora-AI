import uuid
from datetime import datetime, timedelta, timezone

from app.infrastructure.providers.base import BaseOpportunityProvider, NormalizedOpportunity


MOCK_OPPORTUNITIES = [
    NormalizedOpportunity(
        external_id="fl-1001",
        platform="freelancer",
        title="Full-Stack Web Developer for SaaS Platform",
        description="We are building a next-gen SaaS platform for inventory management. Need an experienced full-stack developer proficient in Python and React.",
        url="https://www.freelancer.com/projects/fl-1001",
        project_type="fixed",
        experience_level="intermediate",
        duration="1-3 months",
        budget_min=2000.0,
        budget_max=5000.0,
        budget_type="fixed",
        currency="USD",
        skills=["Python", "React", "PostgreSQL", "Docker", "AWS"],
        category="Web Development",
        subcategory="Full-Stack Development",
        country="US",
        client_rating=4.8,
        client_reviews_count=23,
        client_payment_verified=True,
        client_total_hired=15,
        is_remote=True,
        is_negotiable=False,
        posted_at=datetime.now(timezone.utc) - timedelta(hours=2),
        deadline=datetime.now(timezone.utc) + timedelta(days=14),
    ),
    NormalizedOpportunity(
        external_id="fl-1002",
        platform="freelancer",
        title="Machine Learning Engineer for NLP Project",
        description="Looking for an ML engineer to build a custom NLP pipeline for text classification and sentiment analysis.",
        url="https://www.freelancer.com/projects/fl-1002",
        project_type="fixed",
        experience_level="expert",
        duration="3-6 months",
        budget_min=8000.0,
        budget_max=15000.0,
        budget_type="fixed",
        currency="USD",
        skills=["Python", "PyTorch", "Transformers", "NLP", "Docker"],
        category="AI & Machine Learning",
        subcategory="Natural Language Processing",
        country="GB",
        client_rating=4.5,
        client_reviews_count=8,
        client_payment_verified=True,
        client_total_hired=5,
        is_remote=True,
        is_negotiable=True,
        posted_at=datetime.now(timezone.utc) - timedelta(hours=5),
    ),
    NormalizedOpportunity(
        external_id="fl-1003",
        platform="freelancer",
        title="Mobile App Developer (React Native)",
        description="Need a React Native developer to build a cross-platform mobile app for a food delivery startup.",
        url="https://www.freelancer.com/projects/fl-1003",
        project_type="fixed",
        experience_level="intermediate",
        duration="1-3 months",
        budget_min=3000.0,
        budget_max=7000.0,
        budget_type="fixed",
        currency="USD",
        skills=["React Native", "TypeScript", "Firebase", "Redux"],
        category="Mobile Development",
        subcategory="Cross-Platform Development",
        country="CA",
        client_rating=4.2,
        client_reviews_count=12,
        client_payment_verified=False,
        client_total_hired=8,
        is_remote=True,
        is_negotiable=False,
        posted_at=datetime.now(timezone.utc) - timedelta(hours=1),
    ),
    NormalizedOpportunity(
        external_id="fl-1004",
        platform="freelancer",
        title="DevOps Engineer for AWS Infrastructure",
        description="Seeking a DevOps engineer to design and implement AWS infrastructure with Terraform and Kubernetes.",
        url="https://www.freelancer.com/projects/fl-1004",
        project_type="hourly",
        experience_level="expert",
        duration="3-6 months",
        budget_min=50.0,
        budget_max=90.0,
        budget_type="hourly",
        currency="USD",
        skills=["AWS", "Terraform", "Kubernetes", "CI/CD", "Docker", "Linux"],
        category="DevOps & Cloud",
        subcategory="Cloud Infrastructure",
        country="DE",
        client_rating=4.9,
        client_reviews_count=31,
        client_payment_verified=True,
        client_total_hired=20,
        is_remote=True,
        is_negotiable=False,
        posted_at=datetime.now(timezone.utc) - timedelta(hours=12),
    ),
    NormalizedOpportunity(
        external_id="fl-1005",
        platform="freelancer",
        title="WordPress Website Redesign",
        description="Need a WordPress expert to redesign our company website with a modern look and better performance.",
        url="https://www.freelancer.com/projects/fl-1005",
        project_type="fixed",
        experience_level="beginner",
        duration="Less than 1 month",
        budget_min=500.0,
        budget_max=1500.0,
        budget_type="fixed",
        currency="USD",
        skills=["WordPress", "PHP", "CSS", "JavaScript", "Elementor"],
        category="Web Development",
        subcategory="CMS Development",
        country="US",
        client_rating=4.0,
        client_reviews_count=5,
        client_payment_verified=True,
        client_total_hired=3,
        is_remote=True,
        is_negotiable=True,
        posted_at=datetime.now(timezone.utc) - timedelta(days=1),
    ),
]


class MockFreelancerProvider(BaseOpportunityProvider):
    async def fetch_opportunities(self, user_id: uuid.UUID, **kwargs) -> list[NormalizedOpportunity]:
        return list(MOCK_OPPORTUNITIES)

    async def fetch_opportunity_details(self, external_id: str) -> NormalizedOpportunity | None:
        for opp in MOCK_OPPORTUNITIES:
            if opp.external_id == external_id:
                return opp
        return None

    async def validate_payload(self, payload: dict) -> bool:
        return bool(payload.get("title"))

    async def health_check(self) -> bool:
        return True
