"""
Category endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies.auth import CurrentUser, get_category_service
from app.schemas.auth import MessageResponse
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService


class Page(BaseModel):
    items: list[CategoryResponse]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=Page, summary="List project categories")
async def list_categories(
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> Page:
    items, total = await service.get_all(skip=skip, limit=limit, search=search, is_active=is_active)
    return Page(items=items, total=total, page=(skip // limit) + 1, size=limit)


@router.get("/{category_id}", response_model=CategoryResponse, summary="Get a category by ID")
async def get_category(
    category_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.get_by_id(category_id)
    return CategoryResponse.model_validate(category)


@router.post("", response_model=CategoryResponse, status_code=201, summary="Create a new category")
async def create_category(
    payload: CategoryCreate,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.create(payload)
    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse, summary="Update a category")
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.update(category_id, payload)
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", response_model=MessageResponse, summary="Delete a category")
async def delete_category(
    category_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> MessageResponse:
    await service.delete(category_id)
    return MessageResponse(message="Category deleted successfully.")
