import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.dependencies.auth import CurrentUser, get_project_service
from app.schemas.auth import MessageResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService


class Page(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=Page, summary="List projects for the current user")
async def list_projects(
    current_user: CurrentUser,
    service: Annotated[ProjectService, Depends(get_project_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    technology_id: uuid.UUID | None = Query(None),
    is_archived: bool = Query(False),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
) -> Page:
    items, total = await service.get_all(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        category_id=category_id,
        technology_id=technology_id,
        is_archived=is_archived,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return Page(items=items, total=total, page=(skip // limit) + 1, size=limit)


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get a project by ID")
async def get_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = await service.get_by_id(project_id, user_id=current_user.id)
    return ProjectResponse.model_validate(project)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectCreate,
    current_user: CurrentUser,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = await service.create(current_user.id, payload)
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update a project")
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: CurrentUser,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = await service.update(project_id, payload, user_id=current_user.id)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", response_model=MessageResponse, summary="Delete a project")
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> MessageResponse:
    await service.delete(project_id, user_id=current_user.id)
    return MessageResponse(message="Project deleted successfully.")
