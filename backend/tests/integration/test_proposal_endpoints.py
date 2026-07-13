"""
Integration tests for the Proposal CRUD HTTP endpoints.

These tests go through the full stack — FastAPI routing, dependency
injection, services, repositories — against an isolated in-memory SQLite
database, verifying request/response contracts and status codes end-to-end.
"""

import pytest
from httpx import AsyncClient


VALID_PASSWORD = "StrongPass1"
PROJECT_PAYLOAD = {
    "title": "Build a website",
    "description": "Need a full-stack developer.",
    "budget_min": 1000,
    "budget_max": 5000,
    "currency": "USD",
    "status": "open",
}


async def _register(client: AsyncClient, email: str = "proposal_tester@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Proposal Tester", "password": VALID_PASSWORD},
    )
    return response.json()


async def _create_project(client: AsyncClient, access_token: str) -> dict:
    response = await client.post(
        "/api/v1/projects",
        json=PROJECT_PAYLOAD,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()


class TestCreateProposalEndpoint:
    async def test_create_proposal_returns_201(self, client: AsyncClient):
        auth = await _register(client)
        project = await _create_project(client, auth["access_token"])

        response = await client.post(
            "/api/v1/proposals",
            json={
                "project_id": project["id"],
                "cover_letter": "I can build this website.",
                "bid_amount": 2500.00,
                "bid_type": "fixed",
            },
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["project_id"] == project["id"]
        assert body["cover_letter"] == "I can build this website."
        assert body["status"] == "draft"
        assert body["user_id"] is not None

    async def test_create_proposal_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/proposals",
            json={"project_id": "00000000-0000-0000-0000-000000000000", "cover_letter": "test"},
        )
        assert response.status_code == 401


class TestListProposalsEndpoint:
    async def test_list_proposals_returns_paginated_results(self, client: AsyncClient):
        auth = await _register(client)
        project = await _create_project(client, auth["access_token"])

        await client.post(
            "/api/v1/proposals",
            json={"project_id": project["id"], "cover_letter": "First proposal."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        await client.post(
            "/api/v1/proposals",
            json={"project_id": project["id"], "cover_letter": "Second proposal."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )

        response = await client.get(
            "/api/v1/proposals",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 2
        assert len(body["items"]) >= 2

    async def test_list_proposals_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/proposals")
        assert response.status_code == 401


class TestGetProposalEndpoint:
    async def test_get_proposal_by_id(self, client: AsyncClient):
        auth = await _register(client)
        project = await _create_project(client, auth["access_token"])

        create_resp = await client.post(
            "/api/v1/proposals",
            json={"project_id": project["id"], "cover_letter": "Get this proposal."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        proposal_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == proposal_id
        assert response.json()["cover_letter"] == "Get this proposal."

    async def test_get_proposal_requires_auth(self, client: AsyncClient):
        response = await client.get(
            f"/api/v1/proposals/{'00000000-0000-0000-0000-000000000000'}"
        )
        assert response.status_code == 401


class TestUpdateProposalEndpoint:
    async def test_update_proposal(self, client: AsyncClient):
        auth = await _register(client)
        project = await _create_project(client, auth["access_token"])

        create_resp = await client.post(
            "/api/v1/proposals",
            json={"project_id": project["id"], "cover_letter": "Original text."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        proposal_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/proposals/{proposal_id}",
            json={"cover_letter": "Updated text.", "status": "submitted"},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert response.status_code == 200
        assert response.json()["cover_letter"] == "Updated text."
        assert response.json()["status"] == "submitted"

    async def test_update_proposal_requires_auth(self, client: AsyncClient):
        response = await client.put(
            f"/api/v1/proposals/{'00000000-0000-0000-0000-000000000000'}",
            json={"cover_letter": "test"},
        )
        assert response.status_code == 401


class TestDeleteProposalEndpoint:
    async def test_delete_proposal(self, client: AsyncClient):
        auth = await _register(client)
        project = await _create_project(client, auth["access_token"])

        create_resp = await client.post(
            "/api/v1/proposals",
            json={"project_id": project["id"], "cover_letter": "To be deleted."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        proposal_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Proposal deleted successfully."

        get_response = await client.get(
            f"/api/v1/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert get_response.status_code == 404

    async def test_delete_proposal_requires_auth(self, client: AsyncClient):
        response = await client.delete(
            f"/api/v1/proposals/{'00000000-0000-0000-0000-000000000000'}"
        )
        assert response.status_code == 401
