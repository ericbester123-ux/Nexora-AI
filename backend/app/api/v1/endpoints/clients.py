"""
Client endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.dependencies.auth import CurrentUser, get_client_service
from app.schemas.auth import MessageResponse
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.services.client_service import ClientService


class Page(BaseModel):
    items: list[ClientResponse]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=Page, summary="List clients for the current user")
async def list_clients(
    current_user: CurrentUser,
    service: Annotated[ClientService, Depends(get_client_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> Page:
    items, total = await service.get_by_user_id(
        current_user.id, skip=skip, limit=limit, search=search, is_active=is_active
    )
    return Page(items=items, total=total, page=(skip // limit) + 1, size=limit)


@router.get("/{client_id}", response_model=ClientResponse, summary="Get a client by ID")
async def get_client(
    client_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ClientService, Depends(get_client_service)],
) -> ClientResponse:
    client = await service.get_by_id(client_id, user_id=current_user.id)
    return ClientResponse.model_validate(client)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED, summary="Create a new client")
async def create_client(
    payload: ClientCreate,
    current_user: CurrentUser,
    service: Annotated[ClientService, Depends(get_client_service)],
) -> ClientResponse:
    client = await service.create(current_user.id, payload)
    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse, summary="Update a client")
async def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdate,
    current_user: CurrentUser,
    service: Annotated[ClientService, Depends(get_client_service)],
) -> ClientResponse:
    client = await service.update(client_id, payload, user_id=current_user.id)
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", response_model=MessageResponse, summary="Delete a client")
async def delete_client(
    client_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ClientService, Depends(get_client_service)],
) -> MessageResponse:
    await service.delete(client_id, user_id=current_user.id)
    return MessageResponse(message="Client deleted successfully.")
