import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser
from app.dependencies.opportunities import get_import_history_repository
from app.repositories.import_history_repository import ImportHistoryRepository
from app.schemas.opportunity import ImportHistoryResponse


router = APIRouter(prefix="/imports", tags=["Imports"])


@router.get("", response_model=dict, summary="List import history for the current user")
async def list_imports(
    current_user: CurrentUser,
    repo: Annotated[ImportHistoryRepository, Depends(get_import_history_repository)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: str | None = Query(None),
    status: str | None = Query(None),
) -> dict:
    items, total = await repo.get_all(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        platform=platform,
        status=status,
    )
    return {"items": [ImportHistoryResponse.model_validate(i) for i in items], "total": total, "skip": skip, "limit": limit}


@router.get("/{import_id}", response_model=ImportHistoryResponse, summary="Get an import record by ID")
async def get_import(
    import_id: uuid.UUID,
    current_user: CurrentUser,
    repo: Annotated[ImportHistoryRepository, Depends(get_import_history_repository)],
) -> ImportHistoryResponse:
    record = await repo.get_by_id(import_id)
    if record is None or record.user_id != current_user.id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Import record not found.")
    return ImportHistoryResponse.model_validate(record)
