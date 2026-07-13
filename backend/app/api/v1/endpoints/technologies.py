"""
Technology CRUD endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies.auth import CurrentUser, get_technology_service
from app.schemas.auth import MessageResponse
from app.schemas.technology import TechnologyCreate, TechnologyResponse, TechnologyUpdate
from app.services.technology_service import TechnologyService


class Page(BaseModel):
    items: list[TechnologyResponse]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/technologies", tags=["Technologies"])


@router.get("", response_model=Page, summary="List all technologies")
async def list_technologies(
    current_user: CurrentUser,
    technology_service: Annotated[TechnologyService, Depends(get_technology_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> Page:
    items, total = await technology_service.get_all(
        skip=skip, limit=limit, search=search, category=category, is_active=is_active,
    )
    return Page(items=items, total=total, page=(skip // limit) + 1, size=limit)


@router.get("/{technology_id}", response_model=TechnologyResponse, summary="Get a technology by ID")
async def get_technology(
    technology_id: uuid.UUID,
    current_user: CurrentUser,
    technology_service: Annotated[TechnologyService, Depends(get_technology_service)],
) -> TechnologyResponse:
    technology = await technology_service.get_by_id(technology_id)
    return TechnologyResponse.model_validate(technology)


@router.post("", response_model=TechnologyResponse, status_code=201, summary="Create a new technology")
async def create_technology(
    payload: TechnologyCreate,
    current_user: CurrentUser,
    technology_service: Annotated[TechnologyService, Depends(get_technology_service)],
) -> TechnologyResponse:
    technology = await technology_service.create(payload)
    return TechnologyResponse.model_validate(technology)


@router.put("/{technology_id}", response_model=TechnologyResponse, summary="Update a technology")
async def update_technology(
    technology_id: uuid.UUID,
    payload: TechnologyUpdate,
    current_user: CurrentUser,
    technology_service: Annotated[TechnologyService, Depends(get_technology_service)],
) -> TechnologyResponse:
    technology = await technology_service.update(technology_id, payload)
    return TechnologyResponse.model_validate(technology)


@router.delete("/{technology_id}", response_model=MessageResponse, summary="Delete a technology")
async def delete_technology(
    technology_id: uuid.UUID,
    current_user: CurrentUser,
    technology_service: Annotated[TechnologyService, Depends(get_technology_service)],
) -> MessageResponse:
    await technology_service.delete(technology_id)
    return MessageResponse(message="Technology deleted successfully.")
