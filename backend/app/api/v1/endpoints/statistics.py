from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser
from app.dependencies.opportunities import get_opportunity_service
from app.schemas.opportunity import OpportunityStatistics
from app.services.opportunity_service import OpportunityService


router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/opportunities", response_model=OpportunityStatistics, summary="Get opportunity statistics")
async def get_opportunity_statistics(
    current_user: CurrentUser,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
) -> OpportunityStatistics:
    stats = await service.get_statistics(user_id=current_user.id)
    return OpportunityStatistics(**stats)
