"""
Real Freelancer.com provider using the official Freelancer SDK.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from freelancersdk.session import Session
from freelancersdk.resources.projects.projects import search_projects, get_project_by_id
from freelancersdk.resources.projects.exceptions import ProjectsNotFoundException

from app.infrastructure.providers.base import BaseOpportunityProvider, NormalizedOpportunity


class FreelancerProvider(BaseOpportunityProvider):
    """Real Freelancer.com provider using official SDK."""

    def __init__(self, oauth_token: str, sandbox: bool = False):
        """
        Initialize Freelancer provider.

        Args:
            oauth_token: OAuth2 token from Freelancer.com developer portal
            sandbox: If True, use sandbox environment (freelancer-sandbox.com)
        """
        url = "https://www.freelancer-sandbox.com" if sandbox else "https://www.freelancer.com"
        self._session = Session(oauth_token=oauth_token, url=url)
        self._platform = "freelancer"

    async def fetch_opportunities(
        self,
        user_id: uuid.UUID,
        query: str = "",
        limit: int = 20,
        offset: int = 0,
        **kwargs
    ) -> list[NormalizedOpportunity]:
        """
        Fetch opportunities from Freelancer.com.

        Args:
            user_id: Internal user ID (for tracking)
            query: Search query string
            limit: Maximum number of results
            offset: Pagination offset
            **kwargs: Additional filters (skills, budget, etc.)
        """
        try:
            search_filter = {}
            if kwargs.get("budget_min"):
                search_filter["budget_min"] = kwargs["budget_min"]
            if kwargs.get("budget_max"):
                search_filter["budget_max"] = kwargs["budget_max"]
            if kwargs.get("job_type"):
                search_filter["job_type"] = kwargs["job_type"]

            project_details = {"full_description": True, "seo_url": True}
            user_details = {"avatar": True, "reputation": True, "status": True}

            result = search_projects(
                session=self._session,
                query=query,
                search_filter=search_filter if search_filter else None,
                project_details=project_details,
                user_details=user_details,
                limit=limit,
                offset=offset,
                active_only=True,
            )

            opportunities = []
            for project in result.get("projects", []):
                opp = self._normalize_project(project)
                if opp:
                    opportunities.append(opp)

            return opportunities

        except ProjectsNotFoundException as e:
            raise RuntimeError(f"Failed to fetch projects: {e.message}") from e

    async def fetch_opportunity_details(self, external_id: str) -> NormalizedOpportunity | None:
        """Fetch detailed information for a specific project."""
        try:
            project_details = {"full_description": True, "seo_url": True}
            user_details = {"avatar": True, "reputation": True, "status": True}

            project = get_project_by_id(
                session=self._session,
                project_id=int(external_id),
                project_details=project_details,
                user_details=user_details,
            )

            return self._normalize_project(project)

        except ProjectsNotFoundException:
            return None

    async def validate_payload(self, payload: dict) -> bool:
        """Validate if we can bid on this project."""
        return bool(payload.get("project_id") and payload.get("description"))

    async def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            # Try a simple search to verify connectivity
            search_projects(self._session, query="test", limit=1)
            return True
        except Exception:
            return False

    def _normalize_project(self, project: dict) -> NormalizedOpportunity:
        """Convert Freelancer project to NormalizedOpportunity."""
        # Extract skills from jobs
        skills = []
        for job in project.get("jobs", []):
            if job.get("name"):
                skills.append(job["name"])

        # Determine currency
        budget_min = project.get("budget", {}).get("minimum")
        budget_max = project.get("budget", {}).get("maximum")
        budget_type = project.get("type", "fixed").lower()

        # Determine currency
        currency = project.get("currency", {}).get("code", "USD")

        # Parse dates
        posted_at = None
        if project.get("time_submitted"):
            posted_at = datetime.fromtimestamp(project["time_submitted"], tz=timezone.utc)

        deadline = None
        if project.get("time_remaining"):
            deadline = datetime.now(timezone.utc) + timedelta(seconds=project["time_remaining"])

        # Owner info
        owner = project.get("owner", {})
        client_rating = owner.get("reputation", {}).get("reputation_rating")
        client_reviews = owner.get("reputation", {}).get("review_count")
        client_payment_verified = owner.get("payment_verified", False)
        client_total_hired = owner.get("jobs_filled", 0)

        return NormalizedOpportunity(
            external_id=str(project.get("id")),
            platform=self._platform,
            title=project.get("title", ""),
            description=project.get("description", ""),
            url=project.get("seo_url"),
            project_type=budget_type,
            experience_level=project.get("status"),  # could be "open", "in_progress", etc.
            duration=str(project.get("days_left", 0)) + " days" if project.get("days_left") else None,
            budget_min=float(budget_min) if budget_min else None,
            budget_max=float(budget_max) if budget_max else None,
            budget_type=budget_type,
            currency=currency,
            skills=skills if skills else None,
            category=project.get("category", {}).get("name"),
            subcategory=project.get("subcategory", {}).get("name"),
            country=owner.get("location", {}).get("country", {}).get("name") if owner.get("location") else None,
            client_rating=float(client_rating) if client_rating else None,
            client_reviews_count=int(client_reviews) if client_reviews else None,
            client_payment_verified=bool(client_payment_verified),
            client_total_hired=int(client_total_hired) if client_total_hired else None,
            is_remote=True,  # Freelancer is remote by default
            is_negotiable=budget_type == "hourly",
            posted_at=posted_at,
            deadline=deadline,
            raw_data=project,
        )