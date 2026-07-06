"""
Integration tests for the authentication and user-profile HTTP endpoints.

These tests go through the full stack — FastAPI routing, dependency
injection, services, repositories — against an isolated in-memory SQLite
database (see `tests/conftest.py`), verifying request/response contracts
and status codes end-to-end.
"""

import pytest  # noqa: F401 - required for pytest-asyncio test discovery
from httpx import AsyncClient


VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str = "jane@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Jane Doe", "password": VALID_PASSWORD},
    )
    return response


class TestRegisterEndpoint:
    async def test_register_returns_201_and_token_pair(self, client: AsyncClient):
        response = await _register(client)
        assert response.status_code == 201
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_register_rejects_duplicate_email(self, client: AsyncClient):
        await _register(client)
        response = await _register(client)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "conflict"

    async def test_register_rejects_weak_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "full_name": "Weak Pw", "password": "alllowercase1"},
        )
        assert response.status_code == 422

    async def test_register_rejects_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "full_name": "Bad Email", "password": VALID_PASSWORD},
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    async def test_login_succeeds_with_correct_credentials(self, client: AsyncClient):
        await _register(client)
        response = await client.post(
            "/api/v1/auth/login", json={"email": "jane@example.com", "password": VALID_PASSWORD}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_fails_with_wrong_password(self, client: AsyncClient):
        await _register(client)
        response = await client.post(
            "/api/v1/auth/login", json={"email": "jane@example.com", "password": "WrongPassword1"}
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "authentication_error"

    async def test_login_fails_for_unknown_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login", json={"email": "ghost@example.com", "password": VALID_PASSWORD}
        )
        assert response.status_code == 401


class TestRefreshEndpoint:
    async def test_refresh_returns_new_token_pair(self, client: AsyncClient):
        register_response = await _register(client)
        refresh_token = register_response.json()["refresh_token"]

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        assert response.json()["access_token"] != register_response.json()["access_token"]

    async def test_refresh_rotates_and_rejects_reused_refresh_token(self, client: AsyncClient):
        register_response = await _register(client)
        refresh_token = register_response.json()["refresh_token"]

        first_response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        second_response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert first_response.status_code == 200
        assert second_response.status_code == 401

    async def test_refresh_rejects_garbage_token(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage"})
        assert response.status_code == 401


class TestUserProfileEndpoints:
    async def test_get_me_requires_authentication(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_auth_me_returns_current_user(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "jane@example.com"

    async def test_get_me_returns_profile_with_valid_token(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "jane@example.com"
        assert "hashed_password" not in body

    async def test_update_me_changes_profile(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.put(
            "/api/v1/users/me",
            json={"first_name": "Jane", "last_name": "Updated", "years_of_experience": 5},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["first_name"] == "Jane"
        assert body["last_name"] == "Updated"
        assert body["years_of_experience"] == 5

    async def test_get_me_rejects_malformed_bearer_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401


class TestLogoutEndpoint:
    async def test_logout_revokes_access_token(self, client: AsyncClient):
        register_response = await _register(client)
        body = register_response.json()

        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": body["refresh_token"]},
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": body["refresh_token"]},
        )

        assert logout_response.status_code == 200
        assert me_response.status_code == 401
        assert refresh_response.status_code == 401

    async def test_logout_requires_authentication(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/logout", json={})
        assert response.status_code == 401


class TestPasswordChangeEndpoint:
    async def test_password_change_allows_login_with_new_password(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        change_response = await client.post(
            "/api/v1/auth/password",
            json={"current_password": VALID_PASSWORD, "new_password": "NewStrongPass2"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        old_login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "jane@example.com", "password": VALID_PASSWORD},
        )
        new_login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "jane@example.com", "password": "NewStrongPass2"},
        )

        assert change_response.status_code == 200
        assert old_login_response.status_code == 401
        assert new_login_response.status_code == 200

    async def test_password_change_rejects_wrong_current_password(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/password",
            json={"current_password": "WrongPassword1", "new_password": "NewStrongPass2"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 401


class TestHealthCheck:
    async def test_health_check_returns_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    async def test_ready_check_returns_ready(self, client: AsyncClient):
        response = await client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    async def test_version_returns_app_metadata(self, client: AsyncClient):
        response = await client.get("/version")
        assert response.status_code == 200
        assert response.json()["service"] == "Nexora AI"
        assert response.json()["version"]
