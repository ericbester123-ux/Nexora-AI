"""
Unit tests for ClientService.
"""

import uuid
from decimal import Decimal

import pytest
from app.core.exceptions import NotFoundError
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from app.services.client_service import ClientService


class FakeClientRepository:
    def __init__(self):
        self._clients: dict[uuid.UUID, Client] = {}

    async def create(self, *, user_id, name, **fields):
        fields.setdefault("is_payment_verified", False)
        fields.setdefault("is_active", True)
        client = Client(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            **fields,
        )
        self._clients[client.id] = client
        return client

    async def get_by_id(self, client_id):
        return self._clients.get(client_id)

    async def get_by_user_id(self, user_id, skip=0, limit=20, search=None, is_active=None):
        items = [c for c in self._clients.values() if c.user_id == user_id]
        if search:
            items = [c for c in items if search.lower() in c.name.lower()]
        if is_active is not None:
            items = [c for c in items if c.is_active == is_active]
        return sorted(items, key=lambda c: c.created_at or c.id, reverse=True)[skip : skip + limit], len(items)

    async def update(self, client, **fields):
        for k, v in fields.items():
            setattr(client, k, v)
        return client

    async def delete(self, client):
        self._clients.pop(client.id, None)


@pytest.fixture
def client_service() -> ClientService:
    return ClientService(repo=FakeClientRepository())


@pytest.fixture
async def existing_client(client_service: ClientService) -> Client:
    user_id = uuid.uuid4()
    payload = ClientCreate(name="Test Client", company="Test Corp")
    response = await client_service.create(user_id, payload)
    return response


class TestCreate:
    async def test_create_client(self, client_service: ClientService):
        user_id = uuid.uuid4()
        payload = ClientCreate(
            name="Acme Corp",
            company="Acme Inc",
            email="contact@acme.com",
            country="US",
        )
        result = await client_service.create(user_id, payload)
        assert result.name == "Acme Corp"
        assert result.company == "Acme Inc"
        assert result.email == "contact@acme.com"
        assert result.country == "US"
        assert result.user_id == user_id
        assert result.is_active is True
        assert result.is_payment_verified is False


class TestGetById:
    async def test_get_by_id_returns_client(self, client_service: ClientService, existing_client):
        result = await client_service.get_by_id(existing_client.id)
        assert result.id == existing_client.id
        assert result.name == existing_client.name

    async def test_get_by_id_raises_not_found(self, client_service: ClientService):
        with pytest.raises(NotFoundError):
            await client_service.get_by_id(uuid.uuid4())


class TestGetByUserId:
    async def test_get_by_user_id_returns_paginated_results(self, client_service: ClientService):
        user_id = uuid.uuid4()
        for i in range(5):
            payload = ClientCreate(name=f"Client {i}")
            await client_service.create(user_id, payload)

        items, total = await client_service.get_by_user_id(user_id, skip=0, limit=2)
        assert len(items) == 2
        assert total == 5

    async def test_get_by_user_id_filters_by_search(self, client_service: ClientService):
        user_id = uuid.uuid4()
        await client_service.create(user_id, ClientCreate(name="Alpha Corp"))
        await client_service.create(user_id, ClientCreate(name="Beta Inc"))

        items, total = await client_service.get_by_user_id(user_id, search="Alpha")
        assert total == 1
        assert items[0].name == "Alpha Corp"

    async def test_get_by_user_id_filters_by_is_active(self, client_service: ClientService):
        user_id = uuid.uuid4()
        c1 = await client_service.create(user_id, ClientCreate(name="Active Client"))
        c2 = await client_service.create(user_id, ClientCreate(name="Inactive Client"))
        client_service._repo._clients[c2.id].is_active = False

        items, total = await client_service.get_by_user_id(user_id, is_active=True)
        assert total == 1
        assert items[0].name == "Active Client"


class TestUpdate:
    async def test_update_client(self, client_service: ClientService, existing_client):
        payload = ClientUpdate(name="Updated Corp", company="Updated Inc")
        result = await client_service.update(existing_client.id, payload)
        assert result.name == "Updated Corp"
        assert result.company == "Updated Inc"

    async def test_update_partial(self, client_service: ClientService, existing_client):
        payload = ClientUpdate(company="New Company Only")
        result = await client_service.update(existing_client.id, payload)
        assert result.company == "New Company Only"
        assert result.name == existing_client.name

    async def test_update_raises_not_found(self, client_service: ClientService):
        payload = ClientUpdate(name="Ghost")
        with pytest.raises(NotFoundError):
            await client_service.update(uuid.uuid4(), payload)


class TestDelete:
    async def test_delete_client(self, client_service: ClientService, existing_client):
        await client_service.delete(existing_client.id)
        with pytest.raises(NotFoundError):
            await client_service.get_by_id(existing_client.id)

    async def test_delete_raises_not_found(self, client_service: ClientService):
        with pytest.raises(NotFoundError):
            await client_service.delete(uuid.uuid4())
