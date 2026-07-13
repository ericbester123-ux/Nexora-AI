"""
Aggregates all v1 endpoint routers under a single APIRouter.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import ai_settings, auth, categories, clients, imports, integrations, notification_preferences, opportunities, preferences, projects, proposal_templates, proposals, statistics, technologies, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(preferences.router)
api_router.include_router(ai_settings.router)
api_router.include_router(notification_preferences.router)
api_router.include_router(categories.router)
api_router.include_router(clients.router)
api_router.include_router(proposal_templates.router)
api_router.include_router(proposals.router)
api_router.include_router(technologies.router)
api_router.include_router(projects.router)
api_router.include_router(opportunities.router)
api_router.include_router(integrations.router)
api_router.include_router(imports.router)
api_router.include_router(statistics.router)
