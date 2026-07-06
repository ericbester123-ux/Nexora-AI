"""
Integration tests for user profile endpoints.
"""

from httpx import AsyncClient

VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str = "jane@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Jane Doe", "password": VALID_PASSWORD},
    )
    return response


class TestGetProfile:
    async def test_get_me_returns_profile_with_all_fields(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "jane@example.com"
        assert "hashed_password" not in body
        # New profile fields should be present (nullable)
        assert body["first_name"] is None
        assert body["last_name"] is None
        assert body["years_of_experience"] is None
        assert body["primary_skills"] is None


class TestUpdateProfile:
    async def test_put_me_updates_all_profile_fields(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.put(
            "/api/v1/users/me",
            json={
                "first_name": "Jane",
                "last_name": "Doe",
                "display_name": "Jane D",
                "timezone": "America/New_York",
                "country": "US",
                "preferred_currency": "USD",
                "profile_photo_url": "https://example.com/photo.jpg",
                "biography": "Full-stack developer",
                "portfolio_url": "https://example.com/portfolio",
                "years_of_experience": 8,
                "primary_skills": ["Python", "FastAPI", "React"],
                "secondary_skills": ["Docker", "AWS"],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["first_name"] == "Jane"
        assert body["last_name"] == "Doe"
        assert body["display_name"] == "Jane D"
        assert body["timezone"] == "America/New_York"
        assert body["country"] == "US"
        assert body["preferred_currency"] == "USD"
        assert body["profile_photo_url"] == "https://example.com/photo.jpg"
        assert body["biography"] == "Full-stack developer"
        assert body["portfolio_url"] == "https://example.com/portfolio"
        assert body["years_of_experience"] == 8
        assert body["primary_skills"] == ["Python", "FastAPI", "React"]
        assert body["secondary_skills"] == ["Docker", "AWS"]

    async def test_put_me_partial_update(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.put(
            "/api/v1/users/me",
            json={"years_of_experience": 5},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["years_of_experience"] == 5

    async def test_put_me_rejects_invalid_currency(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.put(
            "/api/v1/users/me",
            json={"preferred_currency": "INVALID"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    async def test_put_me_rejects_invalid_country_code(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.put(
            "/api/v1/users/me",
            json={"country": "USA"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    async def test_put_me_requires_auth(self, client: AsyncClient):
        response = await client.put("/api/v1/users/me", json={"first_name": "Jane"})
        assert response.status_code == 401


class TestChangePassword:
    async def test_change_password_allows_login_with_new_password(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.put(
            "/api/v1/users/change-password",
            json={"current_password": VALID_PASSWORD, "new_password": "NewStrongPass2"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

        old_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "jane@example.com", "password": VALID_PASSWORD},
        )
        new_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "jane@example.com", "password": "NewStrongPass2"},
        )
        assert old_login.status_code == 401
        assert new_login.status_code == 200

    async def test_change_password_requires_auth(self, client: AsyncClient):
        response = await client.put(
            "/api/v1/users/change-password",
            json={"current_password": "old", "new_password": "NewStrongPass2"},
        )
        assert response.status_code == 401

    async def test_change_password_rejects_wrong_current_password(self, client: AsyncClient):
        register_response = await _register(client)
        access_token = register_response.json()["access_token"]

        response = await client.put(
            "/api/v1/users/change-password",
            json={"current_password": "WrongPassword1", "new_password": "NewStrongPass2"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 401
