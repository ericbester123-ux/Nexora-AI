"""
Integration tests for category endpoints.
"""

import uuid

from httpx import AsyncClient


VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "full_name": "Test User", "password": VALID_PASSWORD},
    )
    return response


async def _auth_header(client: AsyncClient) -> dict:
    resp = await _register(client)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestCreateCategory:
    async def test_create_category_returns_201(self, client: AsyncClient):
        headers = await _auth_header(client)
        response = await client.post(
            "/api/v1/categories",
            json={"name": "Web Development", "description": "Build websites", "icon": "globe"},
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Web Development"
        assert body["description"] == "Build websites"
        assert body["icon"] == "globe"
        assert body["slug"] == "web-development"
        assert body["is_active"] is True
        assert "id" in body

    async def test_create_category_duplicate_name_returns_409(self, client: AsyncClient):
        headers = await _auth_header(client)
        await client.post(
            "/api/v1/categories",
            json={"name": "Web Development"},
            headers=headers,
        )
        response = await client.post(
            "/api/v1/categories",
            json={"name": "Web Development"},
            headers=headers,
        )
        assert response.status_code == 409

    async def test_create_category_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/categories",
            json={"name": "No Auth"},
        )
        assert response.status_code == 401


class TestListCategories:
    async def test_list_returns_paginated_results(self, client: AsyncClient):
        headers = await _auth_header(client)
        for i in range(3):
            await client.post(
                "/api/v1/categories",
                json={"name": f"Category {i}"},
                headers=headers,
            )
        response = await client.get(
            "/api/v1/categories?skip=0&limit=2",
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["size"] == 2


class TestGetCategory:
    async def test_get_category_by_id(self, client: AsyncClient):
        headers = await _auth_header(client)
        create_resp = await client.post(
            "/api/v1/categories",
            json={"name": "Data Science"},
            headers=headers,
        )
        cat_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/categories/{cat_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Data Science"

    async def test_get_category_not_found_returns_404(self, client: AsyncClient):
        headers = await _auth_header(client)
        response = await client.get(f"/api/v1/categories/{uuid.uuid4()}", headers=headers)
        assert response.status_code == 404


class TestUpdateCategory:
    async def test_update_category(self, client: AsyncClient):
        headers = await _auth_header(client)
        create_resp = await client.post(
            "/api/v1/categories",
            json={"name": "Mobile Dev", "description": "Build mobile apps"},
            headers=headers,
        )
        cat_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/categories/{cat_id}",
            json={"name": "Mobile Development", "description": "Build native and cross-platform apps"},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Mobile Development"
        assert body["description"] == "Build native and cross-platform apps"

    async def test_update_category_not_found_returns_404(self, client: AsyncClient):
        headers = await _auth_header(client)
        response = await client.put(
            f"/api/v1/categories/{uuid.uuid4()}",
            json={"name": "Ghost"},
            headers=headers,
        )
        assert response.status_code == 404


class TestDeleteCategory:
    async def test_delete_category(self, client: AsyncClient):
        headers = await _auth_header(client)
        create_resp = await client.post(
            "/api/v1/categories",
            json={"name": "DevOps"},
            headers=headers,
        )
        cat_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/categories/{cat_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Category deleted successfully."

        get_resp = await client.get(f"/api/v1/categories/{cat_id}", headers=headers)
        assert get_resp.status_code == 404

    async def test_delete_category_requires_auth(self, client: AsyncClient):
        response = await client.delete(f"/api/v1/categories/{uuid.uuid4()}")
        assert response.status_code == 401
