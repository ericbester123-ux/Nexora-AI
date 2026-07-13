import uuid

from httpx import AsyncClient

VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str = "jane@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Jane Doe", "password": VALID_PASSWORD},
    )
    return response.json()


class TestCreateProject:
    async def test_create_project_returns_201(self, client: AsyncClient):
        tokens = await _register(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = await client.post(
            "/api/v1/projects",
            json={"title": "Build a website", "description": "A great project"},
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Build a website"
        assert body["user_id"] is not None
        assert body["id"] is not None
        assert body["is_remote"] is True
        assert body["status"] == "open"

    async def test_create_project_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/projects",
            json={"title": "No auth project"},
        )
        assert response.status_code == 401


class TestListProjects:
    async def test_list_projects_returns_paginated_results(self, client: AsyncClient):
        tokens = await _register(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        await client.post(
            "/api/v1/projects",
            json={"title": "Project One"},
            headers=headers,
        )
        await client.post(
            "/api/v1/projects",
            json={"title": "Project Two"},
            headers=headers,
        )

        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    async def test_list_projects_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401


class TestGetProject:
    async def test_get_project_by_id(self, client: AsyncClient):
        tokens = await _register(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = await client.post(
            "/api/v1/projects",
            json={"title": "Specific project"},
            headers=headers,
        )
        project_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Specific project"

    async def test_get_project_requires_auth(self, client: AsyncClient):
        response = await client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 401


class TestUpdateProject:
    async def test_update_project(self, client: AsyncClient):
        tokens = await _register(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = await client.post(
            "/api/v1/projects",
            json={"title": "Original title"},
            headers=headers,
        )
        project_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/projects/{project_id}",
            json={"title": "Updated title"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated title"

    async def test_update_project_requires_auth(self, client: AsyncClient):
        response = await client.put(
            f"/api/v1/projects/{uuid.uuid4()}",
            json={"title": "Hack"},
        )
        assert response.status_code == 401


class TestDeleteProject:
    async def test_delete_project(self, client: AsyncClient):
        tokens = await _register(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = await client.post(
            "/api/v1/projects",
            json={"title": "To be deleted"},
            headers=headers,
        )
        project_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Project deleted successfully."

        get_resp = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert get_resp.status_code == 404

    async def test_delete_project_requires_auth(self, client: AsyncClient):
        response = await client.delete(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 401
