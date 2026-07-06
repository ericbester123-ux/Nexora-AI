"""
Integration tests for preference endpoints (user, AI, notification).
"""

from httpx import AsyncClient

VALID_PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str = "pref@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Pref User", "password": VALID_PASSWORD},
    )
    return response


class TestUserPreferences:
    async def test_get_preferences_returns_defaults(self, client: AsyncClient):
        reg = await _register(client)
        token = reg.json()["access_token"]

        response = await client.get(
            "/api/v1/preferences", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["max_daily_recommendations"] == 10
        assert body["require_payment_verified"] is False

    async def test_put_preferences_saves_all_fields(self, client: AsyncClient):
        reg = await _register(client)
        token = reg.json()["access_token"]

        response = await client.put(
            "/api/v1/preferences",
            json={
                "min_budget": 100.00,
                "max_budget": 5000.00,
                "preferred_categories": ["Web Development", "Mobile"],
                "preferred_technologies": ["Python", "React"],
                "preferred_countries": ["US", "GB"],
                "preferred_languages": ["en"],
                "min_client_rating": 4.0,
                "require_payment_verified": True,
                "max_competition_level": 30,
                "max_daily_recommendations": 15,
                "preferred_project_age": "recent",
                "preferred_delivery_time": "flexible",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert float(body["min_budget"]) == 100.00
        assert float(body["max_budget"]) == 5000.00
        assert body["preferred_categories"] == ["Web Development", "Mobile"]
        assert body["require_payment_verified"] is True
        assert body["max_daily_recommendations"] == 15

    async def test_put_preferences_partial_update(self, client: AsyncClient):
        reg = await _register(client, email="partial@example.com")
        token = reg.json()["access_token"]

        await client.put(
            "/api/v1/preferences",
            json={"min_budget": 100.00, "max_budget": 5000.00},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.put(
            "/api/v1/preferences",
            json={"max_budget": 7500.00},
            headers={"Authorization": f"Bearer {token}"},
        )
        body = response.json()
        assert float(body["min_budget"]) == 100.00
        assert float(body["max_budget"]) == 7500.00

    async def test_preferences_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/v1/preferences")).status_code == 401
        assert (await client.put("/api/v1/preferences", json={})).status_code == 401


class TestAISettings:
    async def test_get_ai_settings_returns_defaults(self, client: AsyncClient):
        reg = await _register(client, email="ai@example.com")
        token = reg.json()["access_token"]

        response = await client.get(
            "/api/v1/ai-settings", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["ai_enabled"] is True
        assert body["proposal_tone"] == "professional"
        assert body["confidence_threshold"] == 0.7

    async def test_put_ai_settings_updates_fields(self, client: AsyncClient):
        reg = await _register(client, email="ai2@example.com")
        token = reg.json()["access_token"]

        response = await client.put(
            "/api/v1/ai-settings",
            json={
                "ai_enabled": True,
                "proposal_tone": "friendly",
                "proposal_length": "short",
                "writing_style": "persuasive",
                "automatically_include_portfolio": False,
                "confidence_threshold": 0.9,
                "bid_recommendation_style": "aggressive",
                "ai_learning_enabled": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["proposal_tone"] == "friendly"
        assert body["proposal_length"] == "short"
        assert body["writing_style"] == "persuasive"
        assert body["automatically_include_portfolio"] is False
        assert body["confidence_threshold"] == 0.9

    async def test_put_ai_settings_rejects_invalid_tone(self, client: AsyncClient):
        reg = await _register(client, email="ai3@example.com")
        token = reg.json()["access_token"]

        response = await client.put(
            "/api/v1/ai-settings",
            json={"proposal_tone": "invalid_tone"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_ai_settings_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/v1/ai-settings")).status_code == 401
        assert (await client.put("/api/v1/ai-settings", json={})).status_code == 401


class TestNotificationPreferences:
    async def test_get_notification_preferences_returns_defaults(self, client: AsyncClient):
        reg = await _register(client, email="notif@example.com")
        token = reg.json()["access_token"]

        response = await client.get(
            "/api/v1/notification-preferences",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["push_enabled"] is True
        assert body["email_enabled"] is True
        assert body["daily_summary"] is True

    async def test_put_notification_preferences_updates_fields(self, client: AsyncClient):
        reg = await _register(client, email="notif2@example.com")
        token = reg.json()["access_token"]

        response = await client.put(
            "/api/v1/notification-preferences",
            json={
                "push_enabled": True,
                "email_enabled": False,
                "high_confidence_projects": True,
                "new_opportunities": False,
                "messages": False,
                "daily_summary": True,
                "weekly_summary": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["push_enabled"] is True
        assert body["email_enabled"] is False
        assert body["high_confidence_projects"] is True
        assert body["new_opportunities"] is False
        assert body["messages"] is False
        assert body["daily_summary"] is True
        assert body["weekly_summary"] is False

    async def test_notification_preferences_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/v1/notification-preferences")).status_code == 401
        assert (await client.put("/api/v1/notification-preferences", json={})).status_code == 401
