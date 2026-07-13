"""
Real Freelancer.com provider implementing MarketplaceProvider interface.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode

import requests

from app.infrastructure.providers.base import BaseOpportunityProvider, NormalizedOpportunity
from app.infrastructure.providers.marketplace_base import MarketplaceProvider, MarketplaceUserProfile


class FreelancerProvider(BaseOpportunityProvider, MarketplaceProvider):
    """Freelancer.com provider implementing both opportunity fetching and account management."""

    def __init__(self, oauth_token: str | None = None, sandbox: bool = False):
        self._sandbox = sandbox
        self._base_url = "https://www.freelancer-sandbox.com" if sandbox else "https://www.freelancer.com"
        self._api_url = f"{self._base_url}/api"
        self._oauth_token = oauth_token
        self._session = None
        if oauth_token:
            self._init_session(oauth_token)

    def _init_session(self, oauth_token: str):
        from freelancersdk.session import Session
        self._session = Session(oauth_token=oauth_token, url=self._base_url)

    # --- MarketplaceProvider interface ---

    def get_platform_name(self) -> str:
        return "freelancer"

    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "response_type": "code",
            "client_id": "{client_id}",
            "redirect_uri": redirect_uri,
            "scope": "basic profile projects",
            "state": state,
            "prompt": "consent",
        }
        return f"{self._base_url}/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
        token_url = f"{self._api_url}/users/0.1/oauth/token"
        response = requests.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to exchange code: {response.text}")
        return response.json()

    async def refresh_access_token(self, refresh_token: str, client_id: str, client_secret: str) -> dict:
        token_url = f"{self._api_url}/users/0.1/self/access_token"
        response = requests.post(
            token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to refresh token: {response.text}")
        return response.json()

    async def get_user_profile(self, access_token: str) -> MarketplaceUserProfile:
        from freelancersdk.session import Session
        from freelancersdk.resources.users.users import get_self_user_id, get_user

        session = Session(oauth_token=access_token, url=self._base_url)
        user_id = get_self_user_id(session)
        user_info = get_user(session, user_id)

        reputation = user_info.get("reputation", {}) or {}
        location = user_info.get("location", {}) or {}
        avatar = user_info.get("avatar", "") or ""
        if isinstance(avatar, dict):
            avatar = avatar.get("url", "") or avatar.get("large", "") or avatar.get("small", "") or ""

        return MarketplaceUserProfile(
            external_user_id=str(user_id),
            username=user_info.get("username"),
            display_name=user_info.get("display_name") or user_info.get("username"),
            email=user_info.get("email"),
            avatar_url=avatar if avatar else None,
            profile_url=f"{self._base_url}/users/{user_id}",
            rating=float(reputation.get("reputation_rating", 0)) if reputation.get("reputation_rating") else None,
            reviews_count=int(reputation.get("review_count", 0)) if reputation.get("review_count") else None,
            projects_completed=int(user_info.get("jobs_filled", 0)) or None,
            verification_status="verified" if user_info.get("payment_verified") else "unverified",
            member_since=datetime.fromtimestamp(user_info.get("registration_date", 0), tz=timezone.utc) if user_info.get("registration_date") else None,
            raw_data=user_info,
        )

    async def get_self_user_id(self, access_token: str) -> str:
        from freelancersdk.session import Session
        from freelancersdk.resources.users.users import get_self_user_id

        session = Session(oauth_token=access_token, url=self._base_url)
        return str(get_self_user_id(session))

    async def validate_token(self, access_token: str) -> bool:
        try:
            await self.get_self_user_id(access_token)
            return True
        except Exception:
            return False

    # --- BaseOpportunityProvider interface ---

    async def fetch_opportunities(
        self,
        user_id: uuid.UUID,
        query: str = "",
        limit: int = 20,
        offset: int = 0,
        **kwargs
    ) -> list[NormalizedOpportunity]:
        if not self._session:
            raise RuntimeError("Freelancer provider not authenticated. Set OAuth token first.")
        from freelancersdk.resources.projects.projects import search_projects
        from freelancersdk.resources.projects.exceptions import ProjectsNotFoundException

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

        except ProjectsNotFoundException:
            return []

    async def fetch_opportunity_details(self, external_id: str) -> NormalizedOpportunity | None:
        if not self._session:
            raise RuntimeError("Freelancer provider not authenticated.")
        from freelancersdk.resources.projects.projects import get_project_by_id
        from freelancersdk.resources.projects.exceptions import ProjectsNotFoundException

        try:
            project = get_project_by_id(
                session=self._session,
                project_id=int(external_id),
                project_details={"full_description": True, "seo_url": True},
                user_details={"avatar": True, "reputation": True, "status": True},
            )
            return self._normalize_project(project)
        except ProjectsNotFoundException:
            return None

    async def validate_payload(self, payload: dict) -> bool:
        return bool(payload.get("project_id") and payload.get("description"))

    async def health_check(self) -> bool:
        try:
            if not self._session:
                return False
            from freelancersdk.resources.projects.projects import search_projects
            search_projects(self._session, query="test", limit=1)
            return True
        except Exception:
            return False

    def _normalize_project(self, project: dict) -> NormalizedOpportunity:
        skills = []
        for job in project.get("jobs", []):
            if job.get("name"):
                skills.append(job["name"])

        budget_min = project.get("budget", {}).get("minimum")
        budget_max = project.get("budget", {}).get("maximum")
        budget_type = project.get("type", "fixed").lower()
        currency = project.get("currency", {}).get("code", "USD")

        posted_at = None
        if project.get("time_submitted"):
            posted_at = datetime.fromtimestamp(project["time_submitted"], tz=timezone.utc)

        deadline = None
        if project.get("time_remaining"):
            deadline = datetime.now(timezone.utc) + timedelta(seconds=project["time_remaining"])

        owner = project.get("owner", {})
        client_rating = owner.get("reputation", {}).get("reputation_rating")
        client_reviews = owner.get("reputation", {}).get("review_count")
        client_payment_verified = owner.get("payment_verified", False)
        client_total_hired = owner.get("jobs_filled", 0)

        return NormalizedOpportunity(
            external_id=str(project.get("id")),
            platform="freelancer",
            title=project.get("title", ""),
            description=project.get("description", ""),
            url=project.get("seo_url"),
            project_type=budget_type,
            experience_level=project.get("status"),
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
            is_remote=True,
            is_negotiable=budget_type == "hourly",
            posted_at=posted_at,
            deadline=deadline,
            raw_data=project,
        )
