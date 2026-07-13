"""
Development data seeding.

This module creates sample data for development and demo purposes.
Run via `python seed.py` or `python -m app.seed`.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.client import Client
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.proposal import Proposal
from app.models.technology import Technology
from app.models.user import User


ADMIN_EMAIL = "admin@nexora.ai"
ADMIN_PASSWORD = "XeroaAI!"
ADMIN_NAME = "Admin"


async def seed_development_data(session: AsyncSession) -> dict:
    """
    Seed the database with development data.

    Creates:
    - Admin user (idempotent)
    - Sample technologies
    - Sample clients
    - Sample projects
    - Sample proposals
    - Sample opportunities
    """
    result = {
        "admin_user": False,
        "sample_projects": 0,
        "sample_proposals": 0,
    }

    # --- 1. Admin User ---
    admin = await _get_or_create_admin(session)
    result["admin_user"] = True

    # --- 2. Sample Technologies ---
    technologies = await _seed_technologies(session)

    # --- 3. Sample Clients ---
    clients = await _seed_clients(session, admin.id)

    # --- 4. Sample Projects ---
    projects = await _seed_projects(session, admin.id, clients, technologies)
    result["sample_projects"] = len(projects)

    # --- 5. Sample Proposals ---
    proposals = await _seed_proposals(session, admin.id, projects)
    result["sample_proposals"] = len(proposals)

    # --- 6. Sample Opportunities ---
    await _seed_opportunities(session, admin.id, technologies)

    await session.commit()
    return result


async def _get_or_create_admin(session: AsyncSession) -> User:
    """Get existing admin user or create new one."""
    result = await session.execute(
        select(User).where(User.email == ADMIN_EMAIL)
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        admin = User(
            email=ADMIN_EMAIL,
            full_name=ADMIN_NAME,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            is_verified=True,
            subscription_status="active",
        )
        session.add(admin)
        await session.flush()
        await session.refresh(admin)

    return admin


async def _seed_technologies(session: AsyncSession) -> list[Technology]:
    """Seed sample technologies."""
    tech_data = [
        {"name": "Python", "slug": "python", "category": "Language"},
        {"name": "JavaScript", "slug": "javascript", "category": "Language"},
        {"name": "TypeScript", "slug": "typescript", "category": "Language"},
        {"name": "React", "slug": "react", "category": "Frontend"},
        {"name": "Vue.js", "slug": "vuejs", "category": "Frontend"},
        {"name": "Node.js", "slug": "nodejs", "category": "Backend"},
        {"name": "FastAPI", "slug": "fastapi", "category": "Backend"},
        {"name": "Django", "slug": "django", "category": "Backend"},
        {"name": "PostgreSQL", "slug": "postgresql", "category": "Database"},
        {"name": "MongoDB", "slug": "mongodb", "category": "Database"},
        {"name": "Docker", "slug": "docker", "category": "DevOps"},
        {"name": "Kubernetes", "slug": "kubernetes", "category": "DevOps"},
        {"name": "AWS", "slug": "aws", "category": "Cloud"},
        {"name": "GraphQL", "slug": "graphql", "category": "API"},
        {"name": "REST API", "slug": "rest-api", "category": "API"},
    ]

    technologies = []
    for data in tech_data:
        result = await session.execute(
            select(Technology).where(Technology.slug == data["slug"])
        )
        tech = result.scalar_one_or_none()
        if tech is None:
            tech = Technology(**data, is_active=True)
            session.add(tech)
            await session.flush()
        technologies.append(tech)

    return technologies


async def _seed_clients(session: AsyncSession, user_id: uuid.UUID) -> list[Client]:
    """Seed sample clients."""
    client_data = [
        {
            "name": "TechCorp Inc.",
            "website": "https://techcorp.example.com",
            "email": "hiring@techcorp.example.com",
            "company": "TechCorp Inc.",
            "country": "USA",
        },
        {
            "name": "StartupXYZ",
            "website": "https://startupxyz.example.com",
            "email": "jobs@startupxyz.example.com",
            "company": "StartupXYZ",
            "country": "USA",
        },
        {
            "name": "Enterprise Solutions Ltd.",
            "website": "https://enterprisesolutions.example.com",
            "email": "procurement@enterprise.example.com",
            "company": "Enterprise Solutions Ltd.",
            "country": "USA",
        },
    ]

    clients = []
    for data in client_data:
        result = await session.execute(
            select(Client).where(Client.email == data["email"])
        )
        client = result.scalar_one_or_none()
        if client is None:
            client = Client(**data, user_id=user_id)
            session.add(client)
            await session.flush()
        clients.append(client)

    return clients


async def _seed_projects(
    session: AsyncSession,
    user_id: uuid.UUID,
    clients: list[Client],
    technologies: list[Technology],
) -> list[Project]:
    """Seed sample projects."""
    project_data = [
        {
            "title": "E-commerce Platform Redesign",
            "description": "Complete redesign of legacy e-commerce platform using React and Node.js",
            "client_id": clients[0].id,
            "budget_min": 15000,
            "budget_max": 25000,
            "estimated_duration": "12 weeks",
            "technology_slugs": ["react", "nodejs", "postgresql", "aws"],
        },
        {
            "title": "Real-time Analytics Dashboard",
            "description": "Build a real-time analytics dashboard with WebSocket integration",
            "client_id": clients[1].id,
            "budget_min": 8000,
            "budget_max": 15000,
            "estimated_duration": "8 weeks",
            "technology_slugs": ["react", "typescript", "graphql", "docker"],
        },
        {
            "title": "API Integration Layer",
            "description": "Create a unified API layer for microservice architecture",
            "client_id": clients[2].id,
            "budget_min": 20000,
            "budget_max": 35000,
            "estimated_duration": "16 weeks",
            "technology_slugs": ["fastapi", "python", "postgresql", "kubernetes"],
        },
    ]

    # Create slug to technology mapping
    tech_by_slug = {t.slug: t for t in technologies}

    projects = []
    for data in project_data:
        tech_slugs = data.pop("technology_slugs")
        result = await session.execute(
            select(Project).where(Project.title == data["title"])
        )
        project = result.scalar_one_or_none()
        if project is None:
            project = Project(**data, user_id=user_id)
            # Add technologies
            for slug in tech_slugs:
                if slug in tech_by_slug:
                    project.technologies.append(tech_by_slug[slug])
            session.add(project)
            await session.flush()
        projects.append(project)

    return projects


async def _seed_proposals(
    session: AsyncSession,
    user_id: uuid.UUID,
    projects: list[Project],
) -> list[Proposal]:
    """Seed sample proposals."""
    proposal_data = [
        {
            "title": "E-commerce Platform Redesign - Proposal",
            "project_id": projects[0].id,
            "status": "submitted",
            "cover_letter": "Dear Hiring Team,\n\nI am excited to submit my proposal for the E-commerce Platform Redesign project...",
            "bid_amount": 22000,
            "estimated_duration": "12 weeks",
        },
        {
            "title": "Real-time Analytics Dashboard - Proposal",
            "project_id": projects[1].id,
            "status": "under_review",
            "cover_letter": "Hello,\n\nThank you for the opportunity to work on the Real-time Analytics Dashboard...",
            "bid_amount": 12000,
            "estimated_duration": "8 weeks",
        },
        {
            "title": "API Integration Layer - Proposal",
            "project_id": projects[2].id,
            "status": "draft",
            "cover_letter": "Dear Procurement Team,\n\nI am writing to propose my services for the API Integration Layer project...",
            "bid_amount": 28000,
            "estimated_duration": "16 weeks",
        },
    ]

    proposals = []
    for data in proposal_data:
        result = await session.execute(
            select(Proposal).where(Proposal.title == data["title"])
        )
        proposal = result.scalar_one_or_none()
        if proposal is None:
            proposal = Proposal(**data, user_id=user_id)
            session.add(proposal)
            await session.flush()
        proposals.append(proposal)

    return proposals


async def _seed_opportunities(
    session: AsyncSession,
    user_id: uuid.UUID,
    technologies: list[Technology],
) -> list[Opportunity]:
    """Seed sample opportunities."""
    opportunity_data = [
        {
            "title": "Senior Full Stack Developer",
            "description": "Looking for a senior developer to lead the development of a new SaaS product.",
            "platform": "direct",
            "budget_min": 8000,
            "budget_max": 12000,
            "duration": "12 weeks",
        },
        {
            "title": "API Developer - Microservices",
            "description": "Need experienced API developer to build and maintain microservice APIs.",
            "platform": "upwork",
            "budget_min": 15000,
            "budget_max": 25000,
            "duration": "16 weeks",
        },
        {
            "title": "React Frontend Specialist",
            "description": "Short-term contract for React frontend work on an existing project.",
            "platform": "freelancer",
            "budget_min": 5000,
            "budget_max": 8000,
            "duration": "4 weeks",
        },
    ]

    opportunities = []
    for data in opportunity_data:
        result = await session.execute(
            select(Opportunity).where(Opportunity.title == data["title"])
        )
        opportunity = result.scalar_one_or_none()
        if opportunity is None:
            opportunity = Opportunity(**data, user_id=user_id)
            session.add(opportunity)
            await session.flush()
        opportunities.append(opportunity)

    return opportunities