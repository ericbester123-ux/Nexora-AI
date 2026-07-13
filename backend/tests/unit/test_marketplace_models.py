"""Tests for marketplace models."""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.marketplace_account import MarketplaceAccount
from app.models.marketplace_token import MarketplaceToken
from app.models.marketplace_sync_history import MarketplaceSyncHistory


class TestMarketplaceAccount:
    def test_create_marketplace_account(self):
        account = MarketplaceAccount(
            user_id=uuid.uuid4(),
            provider="freelancer",
            external_user_id="12345",
            username="testuser",
            display_name="Test User",
            is_active=True,
            sync_status="never",
            connected_at=datetime.now(timezone.utc),
        )
        assert account.provider == "freelancer"
        assert account.username == "testuser"
        assert account.is_active is True
        assert account.sync_status == "never"
        assert str(account) == f"<MarketplaceAccount id={account.id} provider='freelancer' user_id={account.user_id}>"

    def test_marketplace_account_defaults(self):
        account = MarketplaceAccount(
            user_id=uuid.uuid4(),
            provider="upwork",
            is_active=True,
            sync_status="never",
            connected_at=datetime.now(timezone.utc),
        )
        assert account.is_active is True
        assert account.sync_status == "never"
        assert account.external_user_id is None
        assert account.rating is None


class TestMarketplaceToken:
    def test_create_token(self):
        token = MarketplaceToken(
            account_id=uuid.uuid4(),
            token_type="access",
            encrypted_token="gAAAAABnZ...",
            is_active=True,
            expires_at=datetime.now(timezone.utc),
        )
        assert token.token_type == "access"
        assert token.is_active is True
        assert str(token) == f"<MarketplaceToken id={token.id} type='access' account_id={token.account_id}>"

    def test_token_defaults(self):
        token = MarketplaceToken(
            account_id=uuid.uuid4(),
            token_type="refresh",
            encrypted_token="encrypted_string",
            is_active=True,
        )
        assert token.is_active is True
        assert token.expires_at is None


class TestMarketplaceSyncHistory:
    def test_create_sync_history(self):
        history = MarketplaceSyncHistory(
            account_id=uuid.uuid4(),
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            projects_found=0,
            projects_imported=0,
        )
        assert history.status == "in_progress"
        assert history.projects_found == 0
        assert history.projects_imported == 0
        assert str(history) == f"<MarketplaceSyncHistory id={history.id} status='in_progress' account_id={history.account_id}>"

    def test_sync_history_defaults(self):
        history = MarketplaceSyncHistory(
            account_id=uuid.uuid4(),
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            duration_ms=1500.0,
            projects_found=10,
            projects_imported=5,
            projects_updated=3,
            projects_skipped=1,
            projects_failed=1,
        )
        assert history.projects_found == 10
        assert history.projects_imported == 5
        assert history.projects_updated == 3
        assert history.duration_ms == 1500.0
