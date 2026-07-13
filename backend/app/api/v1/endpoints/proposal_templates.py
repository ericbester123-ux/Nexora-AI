"""
Proposal template endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies.auth import CurrentUser, get_proposal_template_service
from app.schemas.auth import MessageResponse
from app.schemas.proposal_template import (
    ProposalTemplateCreate,
    ProposalTemplateResponse,
    ProposalTemplateUpdate,
)
from app.services.proposal_template_service import ProposalTemplateService


class Page(BaseModel):
    items: list[ProposalTemplateResponse]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/proposal-templates", tags=["Proposal Templates"])


@router.get("", response_model=Page, summary="List proposal templates for the current user")
async def list_templates(
    current_user: CurrentUser,
    service: Annotated[ProposalTemplateService, Depends(get_proposal_template_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> Page:
    items, total = await service.get_by_user_id(
        current_user.id, skip=skip, limit=limit, search=search, category=category, is_active=is_active
    )
    return Page(items=items, total=total, page=(skip // limit) + 1, size=limit)


@router.get("/{template_id}", response_model=ProposalTemplateResponse, summary="Get a proposal template by id")
async def get_template(
    template_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ProposalTemplateService, Depends(get_proposal_template_service)],
) -> ProposalTemplateResponse:
    template = await service.get_by_id(template_id, user_id=current_user.id)
    return ProposalTemplateResponse.model_validate(template)


@router.post("", response_model=ProposalTemplateResponse, status_code=201, summary="Create a new proposal template")
async def create_template(
    payload: ProposalTemplateCreate,
    current_user: CurrentUser,
    service: Annotated[ProposalTemplateService, Depends(get_proposal_template_service)],
) -> ProposalTemplateResponse:
    template = await service.create(current_user.id, payload)
    return ProposalTemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=ProposalTemplateResponse, summary="Update a proposal template")
async def update_template(
    template_id: uuid.UUID,
    payload: ProposalTemplateUpdate,
    current_user: CurrentUser,
    service: Annotated[ProposalTemplateService, Depends(get_proposal_template_service)],
) -> ProposalTemplateResponse:
    template = await service.update(template_id, payload, user_id=current_user.id)
    return ProposalTemplateResponse.model_validate(template)


@router.delete("/{template_id}", response_model=MessageResponse, summary="Delete a proposal template")
async def delete_template(
    template_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ProposalTemplateService, Depends(get_proposal_template_service)],
) -> MessageResponse:
    await service.delete(template_id, user_id=current_user.id)
    return MessageResponse(message="Proposal template deleted successfully.")
