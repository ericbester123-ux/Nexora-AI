"""
Integration tests for the Proposal Review workflow HTTP endpoints.

Tests readiness checks, status transitions, editing, rollback,
comparison, notes, and audit-log through the full stack.
"""

import pytest
from httpx import AsyncClient

VALID_PASSWORD = "StrongPass1"
PROJECT_PAYLOAD = {
    "title": "Review Test Project",
    "description": "For Sprint 7 integration tests.",
    "budget_min": 1000,
    "budget_max": 5000,
    "currency": "USD",
    "status": "open",
}


async def _register(client: AsyncClient, email: str = "review_tester@example.com") -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Review Tester", "password": VALID_PASSWORD},
    )
    return resp.json()


async def _create_project(client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/api/v1/projects",
        json=PROJECT_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()


async def _create_proposal(client: AsyncClient, token: str, project_id: str) -> dict:
    resp = await client.post(
        "/api/v1/proposals",
        json={
            "project_id": project_id,
            "cover_letter": "Integration test proposal.",
            "bid_amount": 1500.00,
            "bid_type": "fixed",
            "estimated_duration": "2 weeks",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()


class TestReadinessEndpoint:
    async def test_readiness_check_pass(self, client: AsyncClient):
        auth = await _register(client, "readiness_pass@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        resp = await client.get(
            f"/api/v1/proposals/{proposal['id']}/readiness",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "ready" in body
        assert "checks" in body

    async def test_readiness_check_fail(self, client: AsyncClient):
        auth = await _register(client, "readiness_fail@test.com")
        project = await _create_project(client, auth["access_token"])
        resp = await client.post(
            "/api/v1/proposals",
            json={"project_id": project["id"], "cover_letter": ""},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        proposal = resp.json()

        resp2 = await client.get(
            f"/api/v1/proposals/{proposal['id']}/readiness",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["ready"] is False

    async def test_readiness_requires_auth(self, client: AsyncClient):
        resp = await client.get(
            f"/api/v1/proposals/00000000-0000-0000-0000-000000000000/readiness"
        )
        assert resp.status_code == 401


class TestReviewTransitionEndpoint:
    async def test_review_transition(self, client: AsyncClient):
        auth = await _register(client, "review_trans@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        resp = await client.post(
            f"/api/v1/proposals/{proposal['id']}/review",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "under_review"

    async def test_review_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            f"/api/v1/proposals/00000000-0000-0000-0000-000000000000/review"
        )
        assert resp.status_code == 401


class TestReadyEndpoint:
    async def test_mark_ready(self, client: AsyncClient):
        auth = await _register(client, "ready_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        await client.post(
            f"/api/v1/proposals/{proposal['id']}/review",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        resp = await client.post(
            f"/api/v1/proposals/{proposal['id']}/ready",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready_to_submit"

    async def test_mark_ready_fails_in_draft(self, client: AsyncClient):
        auth = await _register(client, "ready_fail@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        resp = await client.post(
            f"/api/v1/proposals/{proposal['id']}/ready",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 400


class TestSubmittedEndpoint:
    async def test_mark_submitted(self, client: AsyncClient):
        auth = await _register(client, "sub_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        await client.post(
            f"/api/v1/proposals/{proposal['id']}/review",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        await client.post(
            f"/api/v1/proposals/{proposal['id']}/ready",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        resp = await client.post(
            f"/api/v1/proposals/{proposal['id']}/submitted",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "submitted"


class TestArchiveEndpoint:
    async def test_archive(self, client: AsyncClient):
        auth = await _register(client, "arch_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        resp = await client.post(
            f"/api/v1/proposals/{proposal['id']}/archive",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"


class TestEditEndpoint:
    async def test_edit_creates_version(self, client: AsyncClient):
        auth = await _register(client, "edit_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        resp = await client.post(
            f"/api/v1/proposals/{proposal['id']}/edit",
            json={"cover_letter": "Updated via integration test."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["version_number"] == 1
        assert body["proposal_id"] == proposal["id"]

    async def test_edit_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            f"/api/v1/proposals/00000000-0000-0000-0000-000000000000/edit",
            json={"cover_letter": "test"},
        )
        assert resp.status_code == 401


class TestVersionHistoryEndpoint:
    async def test_list_versions(self, client: AsyncClient):
        auth = await _register(client, "vers_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        await client.post(
            f"/api/v1/proposals/{proposal['id']}/edit",
            json={"cover_letter": "v2"},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )

        resp = await client.get(
            f"/api/v1/proposals/{proposal['id']}/versions",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1


class TestRollbackEndpoint:
    async def test_rollback(self, client: AsyncClient):
        auth = await _register(client, "rb_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        edit = await client.post(
            f"/api/v1/proposals/{proposal['id']}/edit",
            json={"cover_letter": "v2"},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        v1_id = edit.json()["version_id"]

        await client.post(
            f"/api/v1/proposals/{proposal['id']}/edit",
            json={"cover_letter": "v3"},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )

        resp = await client.post(
            f"/api/v1/proposals/{proposal['id']}/rollback",
            json={"version_id": v1_id, "change_summary": "Go back to v2"},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        assert "version_id" in resp.json()


class TestCompareEndpoint:
    async def test_compare(self, client: AsyncClient):
        auth = await _register(client, "cmp_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        edit1 = await client.post(
            f"/api/v1/proposals/{proposal['id']}/edit",
            json={"cover_letter": "Version Two"},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        v1 = edit1.json()["version_id"]

        edit2 = await client.post(
            f"/api/v1/proposals/{proposal['id']}/edit",
            json={"cover_letter": "Version Three"},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        v2 = edit2.json()["version_id"]

        resp = await client.get(
            f"/api/v1/proposals/{proposal['id']}/compare?v1={v1}&v2={v2}",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "section_diffs" in body


class TestNotesEndpoints:
    async def test_notes_crud(self, client: AsyncClient):
        auth = await _register(client, "notes_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        create = await client.post(
            f"/api/v1/proposals/{proposal['id']}/notes",
            json={"content": "A private note."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert create.status_code == 201
        note_id = create.json()["id"]
        assert create.json()["content"] == "A private note."

        list_resp = await client.get(
            f"/api/v1/proposals/{proposal['id']}/notes",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        update = await client.put(
            f"/api/v1/proposals/notes/{note_id}",
            json={"content": "Updated note."},
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert update.status_code == 200
        assert update.json()["content"] == "Updated note."

        delete = await client.delete(
            f"/api/v1/proposals/notes/{note_id}",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert delete.status_code == 200

    async def test_notes_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            f"/api/v1/proposals/00000000-0000-0000-0000-000000000000/notes",
            json={"content": "test"},
        )
        assert resp.status_code == 401


class TestAuditLogEndpoint:
    async def test_audit_log(self, client: AsyncClient):
        auth = await _register(client, "audit_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])

        await client.post(
            f"/api/v1/proposals/{proposal['id']}/review",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )

        resp = await client.get(
            f"/api/v1/proposals/{proposal['id']}/audit-log",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1


class TestFullReviewFlow:
    async def test_complete_review_workflow(self, client: AsyncClient):
        auth = await _register(client, "flow_test@test.com")
        project = await _create_project(client, auth["access_token"])
        proposal = await _create_proposal(client, auth["access_token"], project["id"])
        pid = proposal["id"]

        assert proposal["status"] == "draft"

        r1 = await client.post(
            f"/api/v1/proposals/{pid}/review",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert r1.json()["status"] == "under_review"

        r2 = await client.post(
            f"/api/v1/proposals/{pid}/ready",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert r2.json()["status"] == "ready_to_submit"

        r3 = await client.post(
            f"/api/v1/proposals/{pid}/submitted",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert r3.json()["status"] == "submitted"

        log = await client.get(
            f"/api/v1/proposals/{pid}/audit-log",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        )
        assert log.json()["total"] >= 3
