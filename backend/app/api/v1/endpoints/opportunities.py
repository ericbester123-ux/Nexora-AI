import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser, get_ai_preference_service, get_user_preference_service
from app.dependencies.opportunities import get_import_service, get_opportunity_service, get_scoring_service
from app.schemas.opportunity import (
    ImportHistoryResponse,
    ImportRequest,
    OpportunityResponse,
    ScoreResponse,
    SearchParams,
    SearchRequest,
)
from app.schemas.auth import MessageResponse
from app.services.import_service import ImportService
from app.services.opportunity_service import OpportunityService
from app.services.preference_service import AIPreferenceService, UserPreferenceService
from app.services.scoring_service import ScoringService


router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


@router.post("/import", response_model=ImportHistoryResponse, summary="Import opportunities from a platform")
async def import_opportunities(
    payload: ImportRequest,
    current_user: CurrentUser,
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> ImportHistoryResponse:
    result = await import_service.import_opportunities(
        user_id=current_user.id,
        platform=payload.platform,
        max_results=payload.max_results,
    )
    return ImportHistoryResponse.model_validate(result)


@router.get("", response_model=dict, summary="List opportunities for the current user")
async def list_opportunities(
    current_user: CurrentUser,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: str | None = Query(None),
    status: str | None = Query(None),
) -> dict:
    items, total = await service.get_all(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        platform=platform,
        status=status,
    )
    return {"items": [OpportunityResponse.model_validate(o) for o in items], "total": total, "skip": skip, "limit": limit}


@router.get("/search", response_model=dict, summary="Search opportunities with filters")
async def search_opportunities(
    current_user: CurrentUser,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
    keyword: str | None = Query(None),
    technology: str | None = Query(None),
    category: str | None = Query(None),
    budget_min: float | None = Query(None),
    budget_max: float | None = Query(None),
    country: str | None = Query(None),
    platform: str | None = Query(None),
    payment_verified: bool | None = Query(None),
    project_status: str | None = Query(None),
    date_posted: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("posted_at"),
    sort_desc: bool = Query(True),
) -> dict:
    params = SearchParams(
        keyword=keyword,
        technology=technology,
        category=category,
        budget_min=budget_min,
        budget_max=budget_max,
        country=country,
        platform=platform,
        payment_verified=payment_verified,
        project_status=project_status,
        date_posted=date_posted,
    )
    items, total = await service.search(
        user_id=current_user.id,
        params=params,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return {"items": [OpportunityResponse.model_validate(o) for o in items], "total": total, "skip": skip, "limit": limit}


@router.get("/recommendations", response_model=dict, summary="Get top AI-recommended opportunities")
async def get_recommendations(
    current_user: CurrentUser,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
    user_preference_service: Annotated[UserPreferenceService, Depends(get_user_preference_service)],
    ai_preference_service: Annotated[AIPreferenceService, Depends(get_ai_preference_service)],
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    min_score: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    prefs = await user_preference_service.get(current_user.id)
    ai_prefs = await ai_preference_service.get(current_user.id)
    threshold = ai_prefs.confidence_threshold if ai_prefs else 0.7
    user_threshold = max(min_score, threshold)
    items, _ = await service.get_all(user_id=current_user.id, limit=1000)

    scored: list[tuple] = []
    for opp in items:
        if opp.is_ai_scored and opp.ai_score is not None and opp.ai_score >= user_threshold:
            scored.append((opp.ai_score, opp))
    scored.sort(key=lambda x: x[0], reverse=True)

    results = [OpportunityResponse.model_validate(opp) for _, opp in scored[:limit]]
    return {"items": results, "total": len(scored), "threshold": user_threshold, "limit": limit}


@router.post("/{opportunity_id}/score", response_model=ScoreResponse, summary="Score a single opportunity")
async def score_opportunity(
    opportunity_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
    user_preference_service: Annotated[UserPreferenceService, Depends(get_user_preference_service)],
    ai_preference_service: Annotated[AIPreferenceService, Depends(get_ai_preference_service)],
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
) -> ScoreResponse:
    opportunity = await service.get_by_id(opportunity_id, user_id=current_user.id)
    prefs = await user_preference_service.get(current_user.id)
    ai_prefs = await ai_preference_service.get(current_user.id)
    result = await scoring_service.score_and_persist(opportunity, current_user, prefs, ai_prefs)
    return ScoreResponse(
        opportunity_id=opportunity.id,
        score=result.score,
        skills_score=result.skills_score,
        budget_score=result.budget_score,
        category_score=result.category_score,
        experience_score=result.experience_score,
        client_quality_score=result.client_quality_score,
        match_reason=result.match_reason,
    )


@router.post("/score/batch", response_model=dict, summary="Score all unscored opportunities")
async def score_all_opportunities(
    current_user: CurrentUser,
    user_preference_service: Annotated[UserPreferenceService, Depends(get_user_preference_service)],
    ai_preference_service: Annotated[AIPreferenceService, Depends(get_ai_preference_service)],
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
) -> dict:
    prefs = await user_preference_service.get(current_user.id)
    ai_prefs = await ai_preference_service.get(current_user.id)
    result = await scoring_service.score_batch(current_user, prefs, ai_prefs)
    return result


@router.get("/{opportunity_id}", response_model=OpportunityResponse, summary="Get an opportunity by ID")
async def get_opportunity(
    opportunity_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
) -> OpportunityResponse:
    opportunity = await service.get_by_id(opportunity_id, user_id=current_user.id)
    return OpportunityResponse.model_validate(opportunity)


@router.delete("/{opportunity_id}", response_model=MessageResponse, summary="Delete an opportunity")
async def delete_opportunity(
    opportunity_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
) -> MessageResponse:
    await service.update(opportunity_id, user_id=current_user.id, status="dismissed")
    return MessageResponse(message="Opportunity dismissed.")


@router.post("/search/live", response_model=dict, summary="Search live opportunities from Freelancer.com")
async def search_live_opportunities(
    search_request: SearchRequest,
    current_user: CurrentUser,
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> dict:
    """
    Search for live opportunities from Freelancer.com in real-time.
    
    This does NOT import the opportunities - it just returns them for display.
    """
    provider = import_service._registry.get("freelancer")
    if provider is None:
        return {"items": [], "total": 0, "message": "Freelancer provider not configured"}
    
    try:
        opportunities = await provider.fetch_opportunities(
            user_id=current_user.id,
            query=search_request.query,
            limit=search_request.limit,
            offset=search_request.offset,
            **search_request.filters,
        )
        
        # Convert to response format
        items = []
        for opp in opportunities:
            items.append({
                "external_id": opp.external_id,
                "platform": opp.platform,
                "title": opp.title,
                "description": opp.description,
                "url": opp.url,
                "project_type": opp.project_type,
                "experience_level": opp.experience_level,
                "duration": opp.duration,
                "budget_min": opp.budget_min,
                "budget_max": opp.budget_max,
                "budget_type": opp.budget_type,
                "currency": opp.currency,
                "skills": opp.skills,
                "category": opp.category,
                "subcategory": opp.subcategory,
                "country": opp.country,
                "client_rating": opp.client_rating,
                "client_reviews_count": opp.client_reviews_count,
                "client_payment_verified": opp.client_payment_verified,
                "client_total_hired": opp.client_total_hired,
                "is_remote": opp.is_remote,
                "is_negotiable": opp.is_negotiable,
                "posted_at": opp.posted_at,
                "deadline": opp.deadline,
            })
        
        return {"items": items, "total": len(items)}
    except Exception as e:
        return {"items": [], "total": 0, "error": str(e)}
