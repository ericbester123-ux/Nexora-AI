"""
MarketplaceAuthService handles OAuth flows, connect/disconnect/reconnect.
"""

import uuid
from datetime import datetime, timezone, timedelta

from app.core.config import get_settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import encrypt_token, decrypt_token
from app.infrastructure.providers.marketplace_base import MarketplaceProvider
from app.repositories.marketplace_account_repository import MarketplaceAccountRepository
from app.repositories.marketplace_token_repository import MarketplaceTokenRepository


class MarketplaceAuthService:
    def __init__(
        self,
        account_repo: MarketplaceAccountRepository,
        token_repo: MarketplaceTokenRepository,
    ):
        self._account_repo = account_repo
        self._token_repo = token_repo

    async def get_accounts(self, user_id: uuid.UUID) -> list[dict]:
        accounts = await self._account_repo.get_by_user_id(user_id)
        result = []
        for account in accounts:
            tokens = await self._token_repo.get_by_account_id(account.id)
            result.append({
                "id": str(account.id),
                "provider": account.provider,
                "external_user_id": account.external_user_id,
                "username": account.username,
                "display_name": account.display_name,
                "email": account.email,
                "avatar_url": account.avatar_url,
                "profile_url": account.profile_url,
                "rating": account.rating,
                "reviews_count": account.reviews_count,
                "projects_completed": account.projects_completed,
                "verification_status": account.verification_status,
                "member_since": account.member_since.isoformat() if account.member_since else None,
                "is_active": account.is_active,
                "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
                "sync_status": account.sync_status,
                "sync_error_message": account.sync_error_message,
                "connected_at": account.connected_at.isoformat() if account.connected_at else None,
                "has_valid_token": any(
                    t.token_type == "access" and t.is_active
                    for t in tokens
                ) if tokens else False,
            })
        return result

    async def get_account(self, user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
        account = await self._account_repo.get_by_id(account_id)
        if not account or account.user_id != user_id or not account.is_active:
            raise NotFoundError("Account not found")
        tokens = await self._token_repo.get_by_account_id(account.id)
        access_token = await self._token_repo.get_active_access_token(account.id)
        return {
            "id": str(account.id),
            "provider": account.provider,
            "external_user_id": account.external_user_id,
            "username": account.username,
            "display_name": account.display_name,
            "email": account.email,
            "avatar_url": account.avatar_url,
            "profile_url": account.profile_url,
            "rating": account.rating,
            "reviews_count": account.reviews_count,
            "projects_completed": account.projects_completed,
            "verification_status": account.verification_status,
            "member_since": account.member_since.isoformat() if account.member_since else None,
            "is_active": account.is_active,
            "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
            "sync_status": account.sync_status,
            "sync_error_message": account.sync_error_message,
            "connected_at": account.connected_at.isoformat() if account.connected_at else None,
            "disconnected_at": account.disconnected_at.isoformat() if account.disconnected_at else None,
            "has_valid_token": any(
                t.token_type == "access" and t.is_active
                for t in tokens
            ) if tokens else False,
            "token_expires_at": access_token.expires_at.isoformat() if access_token and access_token.expires_at else None,
        }

    async def exchange_and_connect(
        self,
        user_id: uuid.UUID,
        provider: MarketplaceProvider,
        code: str,
        redirect_uri: str,
    ) -> dict:
        settings = get_settings()
        client_id = settings.FREELANCER_CLIENT_ID
        client_secret = settings.FREELANCER_CLIENT_SECRET

        if not client_id or not client_secret:
            raise BadRequestError(f"{provider.get_platform_name()} is not configured on this server")

        # Exchange code for tokens
        token_data = await provider.exchange_code(code, redirect_uri, client_id, client_secret)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")

        if not access_token:
            raise BadRequestError("No access token received from provider")

        # Get user profile from provider
        profile = await provider.get_user_profile(access_token)

        # Check if already connected via external ID
        existing_by_external = await self._account_repo.get_by_external_id(
            provider.get_platform_name(), profile.external_user_id
        )
        if existing_by_external:
            raise ConflictError(
                f"{provider.get_platform_name().title()} account already connected. "
                "Disconnect first to connect a different account."
            )

        # Calculate expiry
        expires_at = None
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        # Check for existing email-only account to upgrade
        existing_email_account = await self._account_repo.get_by_provider(
            user_id, provider.get_platform_name()
        )

        if existing_email_account and not existing_email_account.external_user_id:
            # Upgrade the email-only placeholder account
            account = await self._account_repo.update(
                existing_email_account,
                external_user_id=profile.external_user_id,
                username=profile.username,
                display_name=profile.display_name,
                email=profile.email,
                avatar_url=profile.avatar_url,
                profile_url=profile.profile_url,
                rating=profile.rating,
                reviews_count=profile.reviews_count,
                projects_completed=profile.projects_completed,
                verification_status=profile.verification_status,
                member_since=profile.member_since,
                connected_at=datetime.now(timezone.utc),
            )
        else:
            # Create new account
            account = await self._account_repo.create(
                user_id=user_id,
                provider=provider.get_platform_name(),
                external_user_id=profile.external_user_id,
                username=profile.username,
                display_name=profile.display_name,
                email=profile.email,
                avatar_url=profile.avatar_url,
                profile_url=profile.profile_url,
                rating=profile.rating,
                reviews_count=profile.reviews_count,
                projects_completed=profile.projects_completed,
                verification_status=profile.verification_status,
                member_since=profile.member_since,
                connected_at=datetime.now(timezone.utc),
            )

        # Store encrypted tokens
        await self._token_repo.create(
            account_id=account.id,
            token_type="access",
            encrypted_token=encrypt_token(access_token),
            expires_at=expires_at,
        )
        if refresh_token:
            await self._token_repo.create(
                account_id=account.id,
                token_type="refresh",
                encrypted_token=encrypt_token(refresh_token),
            )

        return {
            "id": str(account.id),
            "provider": account.provider,
            "external_user_id": profile.external_user_id,
            "username": profile.username,
            "display_name": profile.display_name,
            "avatar_url": profile.avatar_url,
            "message": f"{provider.get_platform_name().title()} account connected successfully.",
        }

    async def disconnect(self, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
        account = await self._account_repo.get_by_id(account_id)
        if not account or account.user_id != user_id or not account.is_active:
            raise NotFoundError("Account not found")
        await self._token_repo.deactivate_all(account_id)
        await self._account_repo.update(
            account,
            is_active=False,
            disconnected_at=datetime.now(timezone.utc),
        )

    async def reconnect(self, user_id: uuid.UUID, account_id: uuid.UUID, provider: MarketplaceProvider) -> str:
        account = await self._account_repo.get_by_id(account_id)
        if not account or account.user_id != user_id or not account.is_active:
            raise NotFoundError("Account not found")

        # Try to get existing refresh token
        tokens = await self._token_repo.get_by_account_id(account_id, token_type="refresh")
        if not tokens:
            raise BadRequestError("No refresh token available. Please reconnect manually.")

        refresh_token = decrypt_token(tokens[0].encrypted_token)
        settings = get_settings()

        try:
            token_data = await provider.refresh_access_token(
                refresh_token,
                settings.FREELANCER_CLIENT_ID,
                settings.FREELANCER_CLIENT_SECRET,
            )

            new_access = token_data.get("access_token")
            new_refresh = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")

            if not new_access:
                raise BadRequestError("No access token received from refresh")

            expires_at = None
            if expires_in:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

            # Deactivate old tokens and store new ones
            await self._token_repo.deactivate_all(account_id)
            await self._token_repo.create(
                account_id=account_id,
                token_type="access",
                encrypted_token=encrypt_token(new_access),
                expires_at=expires_at,
            )
            if new_refresh:
                await self._token_repo.create(
                    account_id=account_id,
                    token_type="refresh",
                    encrypted_token=encrypt_token(new_refresh),
                )

            return "Reconnected successfully"
        except Exception as e:
            # If refresh fails, deactivate tokens so user must reconnect
            await self._token_repo.deactivate_all(account_id)
            raise BadRequestError(f"Failed to reconnect: {str(e)}. Please reconnect manually.")

    # Helper for provider access (called by sync service)
    async def get_provider_token(self, account_id: uuid.UUID) -> str | None:
        token = await self._token_repo.get_active_access_token(account_id)
        if not token:
            return None
        return decrypt_token(token.encrypted_token)

    async def store_new_tokens(
        self, account_id: uuid.UUID, access_token: str, refresh_token: str | None, expires_in: int | None
    ) -> None:
        await self._token_repo.deactivate_all(account_id)
        expires_at = None
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        await self._token_repo.create(
            account_id=account_id,
            token_type="access",
            encrypted_token=encrypt_token(access_token),
            expires_at=expires_at,
        )
        if refresh_token:
            await self._token_repo.create(
                account_id=account_id,
                token_type="refresh",
                encrypted_token=encrypt_token(refresh_token),
            )
