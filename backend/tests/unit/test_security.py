"""
Unit tests for `app.core.security`.

These are pure unit tests: no database, no HTTP layer — just the hashing
and token primitives.
"""

import uuid

import pytest

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_produces_different_hash_than_plaintext(self):
        hashed = hash_password("SuperSecret123")
        assert hashed != "SuperSecret123"

    def test_verify_password_succeeds_for_correct_password(self):
        hashed = hash_password("SuperSecret123")
        assert verify_password("SuperSecret123", hashed) is True

    def test_verify_password_fails_for_incorrect_password(self):
        hashed = hash_password("SuperSecret123")
        assert verify_password("WrongPassword", hashed) is False

    def test_hashing_same_password_twice_produces_different_hashes(self):
        # bcrypt uses a random salt, so hashes must differ even for the same input.
        first = hash_password("SuperSecret123")
        second = hash_password("SuperSecret123")
        assert first != second


class TestJWTTokens:
    def test_access_token_round_trips_and_has_correct_type(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token, expected_type=TokenType.ACCESS)
        assert payload.sub == str(user_id)
        assert payload.type == TokenType.ACCESS

    def test_refresh_token_round_trips_and_has_correct_type(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token, expected_type=TokenType.REFRESH)
        assert payload.sub == str(user_id)
        assert payload.type == TokenType.REFRESH

    def test_decode_rejects_wrong_expected_type(self):
        user_id = uuid.uuid4()
        access_token = create_access_token(user_id)
        with pytest.raises(InvalidTokenError):
            decode_token(access_token, expected_type=TokenType.REFRESH)

    def test_decode_rejects_malformed_token(self):
        with pytest.raises(InvalidTokenError):
            decode_token("not.a.validtoken")

    def test_decode_rejects_tampered_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
        with pytest.raises(InvalidTokenError):
            decode_token(tampered, expected_type=TokenType.ACCESS)

    def test_two_tokens_for_same_user_are_unique(self):
        # jti (JWT ID) should make even same-subject tokens unique.
        user_id = uuid.uuid4()
        token_a = create_access_token(user_id)
        token_b = create_access_token(user_id)
        assert token_a != token_b

    def test_decode_rejects_expired_token(self):
        import uuid as uuid_module
        from datetime import datetime, timedelta, timezone

        from jose import jwt

        from app.core.config import get_settings

        settings = get_settings()
        user_id = uuid_module.uuid4()
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": str(user_id),
            "exp": int((now - timedelta(minutes=5)).timestamp()),
            "iat": int((now - timedelta(minutes=10)).timestamp()),
            "jti": str(uuid_module.uuid4()),
            "type": TokenType.ACCESS.value,
        }
        expired_token = jwt.encode(
            expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        with pytest.raises(TokenExpiredError):
            decode_token(expired_token, expected_type=TokenType.ACCESS)
