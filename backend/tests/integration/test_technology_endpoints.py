"""
Integration tests for technology endpoints.
"""

import uuid

from httpx import AsyncClient

_VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str = "tech-admin@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Admin User", "password": _VALID_PASSWORD},
    )
    return response


async def _auth_header(client: AsyncClient, email: str = "tech-admin@example.com") -> dict:
    reg = await _register(client, email)
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestCreateTechnology:
    async def test_create_technology_returns_201(self, client: AsyncClient):
        headers = await _auth_header(client)
        response = await client.post(
            "/api/v1/technologies",
            json={"name": "Python", "description": "A programming language.", "category": "Language"},
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Python"
        assert body["slug"] == "python"
        assert body["category"] == "Language"
        assert body["is_active"] is True
        assert "id" in body

    async def test_create_duplicate_name_returns_409(self, client: AsyncClient):
        headers = await _auth_header(client)
        await client.post(
            "/api/v1/technologies",
            json={"name": "Python", "category": "Language"},
            headers=headers,
        )
        response = await client.post(
            "/api/v1/technologies",
            json={"name": "Python", "category": "Language"},
            headers=headers,
        )
        assert response.status_code == 409

    async def test_create_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/technologies",
            json={"name": "Python", "category": "Language"},
        )
        assert response.status_code == 401


class TestListTechnologies:
    async def test_list_returns_paginated_results(self, client: AsyncClient):
        headers = await _auth_header(client)
        await client.post(
            "/api/v1/technologies",
            json={"name": "Python", "category": "Language"},
            headers=headers,
        )
        await client.post(
            "/api/v1/technologies",
            json={"name": "FastAPI", "category": "Framework"},
            headers=headers,
        )
        response = await client.get("/api/v1/technologies", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 2
        assert len(body["items"]) >= 2
        assert body["page"] == 1
        assert body["size"] == 20

    async def test_list_with_search_filter(self, client: AsyncClient):
        headers = await _auth_header(client)
        await client.post(
            "/api/v1/technologies",
            json={"name": "JavaScript", "category": "Language"},
            headers=headers,
        )
        response = await client.get(
            "/api/v1/technologies?search=java",
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        assert all("java" in item["name"].lower() for item in body["items"])

    async def test_list_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/technologies")
        assert response.status_code == 401


class TestGetTechnology:
    async def test_get_by_id(self, client: AsyncClient):
        headers = await _auth_header(client)
        create_resp = await client.post(
            "/api/v1/technologies",
            json={"name": "Go", "category": "Language"},
            headers=headers,
        )
        tech_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/technologies/{tech_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Go"

    async def test_get_by_id_not_found(self, client: AsyncClient):
        headers = await _auth_header(client)
        response = await client.get(
            f"/api/v1/technologies/{uuid.uuid4()}",
            headers=headers,
        )
        assert response.status_code == 404

    async def test_get_requires_auth(self, client: AsyncClient):
        response = await client.get(f"/api/v1/technologies/{uuid.uuid4()}")
        assert response.status_code == 401


class TestUpdateTechnology:
    async def test_update_technology(self, client: AsyncClient):
        headers = await _auth_header(client)
        create_resp = await client.post(
            "/api/v1/technologies",
            json={"name": "Rust", "category": "Language"},
            headers=headers,
        )
        tech_id = create_resp.json()["id"]
        response = await client.put(
            f"/api/v1/technologies/{tech_id}",
            json={"name": "Rust Lang"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Rust Lang"

    async def test_update_not_found(self, client: AsyncClient):
        headers = await _auth_header(client)
        response = await client.put(
            f"/api/v1/technologies/{uuid.uuid4()}",
            json={"name": "Ghost"},
            headers=headers,
        )
        assert response.status_code == 404

    async def test_update_requires_auth(self, client: AsyncClient):
        response = await client.put(
            f"/api/v1/technologies/{uuid.uuid4()}",
            json={"name": "Ghost"},
        )
        assert response.status_code == 401


class TestDeleteTechnology:
    async def test_delete_technology(self, client: AsyncClient):
        headers = await _auth_header(client)
        create_resp = await client.post(
            "/api/v1/technologies",
            json={"name": "Kotlin", "category": "Language"},
            headers=headers,
        )
        tech_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/technologies/{tech_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Technology deleted successfully."

    async def test_delete_not_found(self, client: AsyncClient):
        headers = await _auth_header(client)
        response = await client.delete(
            f"/api/v1/technologies/{uuid.uuid4()}",
            headers=headers,
        )
        assert response.status_code == 404

    async def test_delete_requires_auth(self, client: AsyncClient):
        response = await client.delete(f"/api/v1/technologies/{uuid.uuid4()}")
        assert response.status_code == 401
