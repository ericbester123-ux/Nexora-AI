"""
Integration tests for client endpoints.
"""

from httpx import AsyncClient

VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str = "jane@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Jane Doe", "password": VALID_PASSWORD},
    )
    return response


class TestCreateClient:
    async def test_create_client_returns_201(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.post(
            "/api/v1/clients",
            json={"name": "Acme Corp", "company": "Acme Inc", "country": "US"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Acme Corp"
        assert body["company"] == "Acme Inc"
        assert body["country"] == "US"
        assert body["is_active"] is True
        assert "id" in body

    async def test_create_client_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/clients", json={"name": "Acme Corp"}
        )
        assert response.status_code == 401


class TestListClients:
    async def test_list_clients_returns_paginated_results(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        for i in range(3):
            await client.post(
                "/api/v1/clients",
                json={"name": f"Client {i}"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        response = await client.get(
            "/api/v1/clients?skip=0&limit=2",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        assert body["total"] == 3
        assert body["size"] == 2
        assert body["page"] == 1

    async def test_list_clients_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/clients")
        assert response.status_code == 401


class TestGetClient:
    async def test_get_client_by_id(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/clients",
            json={"name": "Specific Client"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        client_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/clients/{client_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Specific Client"

    async def test_get_client_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/clients/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 401


class TestUpdateClient:
    async def test_update_client(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/clients",
            json={"name": "Old Name"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        client_id = create_response.json()["id"]

        response = await client.put(
            f"/api/v1/clients/{client_id}",
            json={"name": "New Name", "company": "New Corp"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "New Name"
        assert body["company"] == "New Corp"

    async def test_update_client_requires_auth(self, client: AsyncClient):
        response = await client.put(
            "/api/v1/clients/00000000-0000-0000-0000-000000000000",
            json={"name": "Hack"},
        )
        assert response.status_code == 401


class TestDeleteClient:
    async def test_delete_client(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        create_response = await client.post(
            "/api/v1/clients",
            json={"name": "Delete Me"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        client_id = create_response.json()["id"]

        response = await client.delete(
            f"/api/v1/clients/{client_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Client deleted successfully."

        get_response = await client.get(
            f"/api/v1/clients/{client_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert get_response.status_code == 404

    async def test_delete_client_requires_auth(self, client: AsyncClient):
        response = await client.delete(
            "/api/v1/clients/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 401
