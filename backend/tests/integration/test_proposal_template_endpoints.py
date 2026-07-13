"""
Integration tests for proposal template endpoints.
"""

from httpx import AsyncClient

VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str = "template@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Template User", "password": VALID_PASSWORD},
    )
    return response


class TestCreateTemplate:
    async def test_create_returns_201(self, client: AsyncClient):
        reg = await _register(client)
        token = reg.json()["access_token"]

        response = await client.post(
            "/api/v1/proposal-templates",
            json={
                "name": "Standard Proposal",
                "cover_letter_template": "Dear {{client_name}}, ...",
                "description": "A standard template",
                "category": "web-dev",
                "tags": ["web", "react"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Standard Proposal"
        assert body["cover_letter_template"] == "Dear {{client_name}}, ..."
        assert body["description"] == "A standard template"
        assert body["category"] == "web-dev"
        assert body["tags"] == ["web", "react"]
        assert body["is_default"] is False
        assert body["is_active"] is True
        assert "id" in body
        assert "created_at" in body

    async def test_create_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/proposal-templates",
            json={"name": "X", "cover_letter_template": "Y"},
        )
        assert response.status_code == 401


class TestListTemplates:
    async def test_list_returns_paginated_results(self, client: AsyncClient):
        reg = await _register(client, email="list@example.com")
        token = reg.json()["access_token"]

        for i in range(3):
            await client.post(
                "/api/v1/proposal-templates",
                json={"name": f"Template {i}", "cover_letter_template": f"Body {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            "/api/v1/proposal-templates",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3

    async def test_list_supports_search(self, client: AsyncClient):
        reg = await _register(client, email="search@example.com")
        token = reg.json()["access_token"]

        await client.post(
            "/api/v1/proposal-templates",
            json={"name": "Python Dev", "cover_letter_template": "X"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/proposal-templates",
            json={"name": "React Dev", "cover_letter_template": "Y"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            "/api/v1/proposal-templates?search=python",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

    async def test_list_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/proposal-templates")
        assert response.status_code == 401


class TestGetTemplate:
    async def test_get_by_id_returns_template(self, client: AsyncClient):
        reg = await _register(client, email="get@example.com")
        token = reg.json()["access_token"]

        create_resp = await client.post(
            "/api/v1/proposal-templates",
            json={"name": "My Template", "cover_letter_template": "Body"},
            headers={"Authorization": f"Bearer {token}"},
        )
        template_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/proposal-templates/{template_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "My Template"

    async def test_get_by_id_requires_auth(self, client: AsyncClient):
        response = await client.get(
            f"/api/v1/proposal-templates/{'00000000-0000-0000-0000-000000000000'}"
        )
        assert response.status_code == 401


class TestUpdateTemplate:
    async def test_update_modifies_fields(self, client: AsyncClient):
        reg = await _register(client, email="update@example.com")
        token = reg.json()["access_token"]

        create_resp = await client.post(
            "/api/v1/proposal-templates",
            json={"name": "Original", "cover_letter_template": "Original body"},
            headers={"Authorization": f"Bearer {token}"},
        )
        template_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/proposal-templates/{template_id}",
            json={"name": "Updated", "cover_letter_template": "Updated body"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"
        assert response.json()["cover_letter_template"] == "Updated body"

    async def test_update_requires_auth(self, client: AsyncClient):
        response = await client.put(
            f"/api/v1/proposal-templates/{'00000000-0000-0000-0000-000000000000'}",
            json={"name": "X"},
        )
        assert response.status_code == 401


class TestDeleteTemplate:
    async def test_delete_removes_template(self, client: AsyncClient):
        reg = await _register(client, email="delete@example.com")
        token = reg.json()["access_token"]

        create_resp = await client.post(
            "/api/v1/proposal-templates",
            json={"name": "To Delete", "cover_letter_template": "Body"},
            headers={"Authorization": f"Bearer {token}"},
        )
        template_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/proposal-templates/{template_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Proposal template deleted successfully."

        get_resp = await client.get(
            f"/api/v1/proposal-templates/{template_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404

    async def test_delete_requires_auth(self, client: AsyncClient):
        response = await client.delete(
            f"/api/v1/proposal-templates/{'00000000-0000-0000-0000-000000000000'}"
        )
        assert response.status_code == 401
