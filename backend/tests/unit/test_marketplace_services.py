"""Tests for marketplace services."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.marketplace_auth_service import MarketplaceAuthService
from app.services.marketplace_sync_service import MarketplaceSyncService
from app.infrastructure.providers.marketplace_base import MarketplaceUserProfile


@pytest.fixture
def mock_account_repo():
    repo = MagicMock()
    repo.get_by_user_id = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_provider = AsyncMock(return_value=None)
    repo.get_by_external_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_token_repo():
    repo = MagicMock()
    repo.get_by_account_id = AsyncMock(return_value=[])
    repo.get_active_access_token = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.deactivate_all = AsyncMock()
    return repo


@pytest.fixture
def auth_service(mock_account_repo, mock_token_repo):
    return MarketplaceAuthService(
        account_repo=mock_account_repo,
        token_repo=mock_token_repo,
    )


class TestMarketplaceAuthService:
    async def test_get_accounts_empty(self, auth_service, mock_account_repo):
        mock_account_repo.get_by_user_id.return_value = []
        accounts = await auth_service.get_accounts(uuid.uuid4())
        assert accounts == []

    async def test_exchange_and_connect_creates_account(self, auth_service, mock_account_repo, mock_token_repo):
        user_id = uuid.uuid4()
        mock_provider = MagicMock()
        mock_provider.get_platform_name.return_value = "freelancer"

        mock_provider.exchange_code = AsyncMock(return_value={
            "access_token": "access123",
            "refresh_token": "refresh123",
            "expires_in": 3600,
        })
        mock_provider.get_user_profile = AsyncMock(return_value=MarketplaceUserProfile(
            external_user_id="ext456",
            username="testuser",
            display_name="Test User",
        ))

        mock_account_repo.get_by_external_id.return_value = None
        mock_account_repo.create.return_value = MagicMock(
            id=uuid.uuid4(),
            provider="freelancer",
            external_user_id="ext456",
            username="testuser",
            display_name="Test User",
        )

        with patch("app.services.marketplace_auth_service.get_settings") as mock_settings, \
             patch("app.services.marketplace_auth_service.encrypt_token", return_value="encrypted"):
            mock_settings.return_value.FREELANCER_CLIENT_ID = "client_id"
            mock_settings.return_value.FREELANCER_CLIENT_SECRET = "client_secret"
            mock_settings.return_value.TOKEN_ENCRYPTION_KEY = "test-key"

            result = await auth_service.exchange_and_connect(
                user_id=user_id,
                provider=mock_provider,
                code="authcode",
                redirect_uri="http://localhost:3000/callback",
            )

        assert result["provider"] == "freelancer"
        assert result["username"] == "testuser"
        mock_account_repo.create.assert_called_once()
        mock_token_repo.create.assert_called()

    async def test_disconnect_deactivates_account(self, auth_service, mock_account_repo, mock_token_repo):
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        mock_account = MagicMock()
        mock_account.user_id = user_id
        mock_account.is_active = True
        mock_account_repo.get_by_id.return_value = mock_account

        await auth_service.disconnect(user_id, account_id)

        mock_token_repo.deactivate_all.assert_called_once_with(account_id)
        mock_account_repo.update.assert_called_once()


class TestMarketplaceSyncService:
    @pytest.mark.asyncio
    async def test_sync_account_no_token_raises_error(self):
        mock_account_repo = MagicMock()
        mock_sync_repo = MagicMock()
        mock_opp_repo = MagicMock()
        mock_import_repo = MagicMock()
        mock_opp_service = MagicMock()
        mock_auth_service = MagicMock()
        mock_auth_service.get_provider_token = AsyncMock(return_value=None)

        service = MarketplaceSyncService(
            account_repo=mock_account_repo,
            sync_history_repo=mock_sync_repo,
            opportunity_repo=mock_opp_repo,
            import_history_repo=mock_import_repo,
            opportunity_service=mock_opp_service,
            auth_service=mock_auth_service,
        )

        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        mock_account = MagicMock()
        mock_account.user_id = user_id
        mock_account.is_active = True
        mock_account_repo.get_by_id.return_value = mock_account

        with pytest.raises(Exception):
            await service.sync_account(user_id, account_id, MagicMock())
