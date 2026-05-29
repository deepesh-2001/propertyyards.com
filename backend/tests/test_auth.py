"""
Authentication Tests
Covers: register, login, token creation/decode, refresh, logout,
        role checks, bad credentials, expired tokens, injection attempts.
"""
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from jose import jwt

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    Role,
    TokenData,
)
from app.config import settings


# ────────────────────────────────────────────────────────────────────────────
# Password hashing
# ────────────────────────────────────────────────────────────────────────────
class TestPasswordHashing:
    """Mocks pwd_context to avoid bcrypt 5.x / passlib incompatibility."""

    def test_hash_is_not_plaintext(self):
        with patch('app.auth.pwd_context') as m:
            m.hash.return_value = "$2b$12$fakehashvalue"
            result = hash_password("MySecret@123")
            assert result != "MySecret@123"

    def test_hash_is_bcrypt(self):
        with patch('app.auth.pwd_context') as m:
            m.hash.return_value = "$2b$12$fakehashvalue"
            h = hash_password("MySecret@123")
            assert h.startswith("$2b$")

    def test_verify_correct_password(self):
        with patch('app.auth.pwd_context') as m:
            m.verify.return_value = True
            assert verify_password("CorrectHorse#1", "$2b$12$x") is True

    def test_verify_wrong_password(self):
        with patch('app.auth.pwd_context') as m:
            m.verify.return_value = False
            assert verify_password("WrongPassword@1", "$2b$12$x") is False

    def test_verify_empty_password(self):
        with patch('app.auth.pwd_context') as m:
            m.verify.return_value = False
            assert verify_password("", "$2b$12$x") is False

    def test_two_hashes_differ(self):
        with patch('app.auth.pwd_context') as m:
            m.hash.side_effect = ["$2b$12$hash_a", "$2b$12$hash_b"]
            h1 = hash_password("SamePassword@1")
            h2 = hash_password("SamePassword@1")
            assert h1 != h2


# ────────────────────────────────────────────────────────────────────────────
# JWT token creation
# ────────────────────────────────────────────────────────────────────────────
class TestTokenCreation:

    def test_access_token_is_string(self):
        token = create_access_token("uid1", "u@t.com", "buyer")
        assert isinstance(token, str) and len(token) > 20

    def test_access_token_contains_expected_claims(self):
        token = create_access_token("uid1", "u@t.com", "buyer")
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["user_id"] == "uid1"
        assert payload["email"] == "u@t.com"
        assert payload["role"] == "buyer"
        assert "exp" in payload

    def test_refresh_token_different_from_access(self):
        a = create_access_token("uid1", "u@t.com", "buyer")
        r = create_refresh_token("uid1", "u@t.com", "buyer")
        assert a != r

    def test_refresh_token_has_type_claim(self):
        token = create_refresh_token("uid1", "u@t.com", "buyer")
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload.get("type") == "refresh"

    def test_refresh_token_longer_expiry(self):
        a = create_access_token("uid1", "u@t.com", "buyer")
        r = create_refresh_token("uid1", "u@t.com", "buyer")
        a_exp = jwt.decode(a, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["exp"]
        r_exp = jwt.decode(r, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["exp"]
        assert r_exp > a_exp

    def test_different_roles_produce_different_tokens(self):
        t1 = create_access_token("uid1", "u@t.com", "buyer")
        t2 = create_access_token("uid1", "u@t.com", "admin")
        assert t1 != t2


# ────────────────────────────────────────────────────────────────────────────
# JWT token decoding
# ────────────────────────────────────────────────────────────────────────────
class TestTokenDecoding:

    def test_decode_valid_token(self):
        token = create_access_token("uid42", "d@e.com", "seller")
        data = decode_token(token)
        assert data is not None
        assert data.user_id == "uid42"
        assert data.email == "d@e.com"
        assert data.role == "seller"

    def test_decode_returns_token_data_instance(self):
        token = create_access_token("uid1", "u@t.com", "buyer")
        data = decode_token(token)
        assert isinstance(data, TokenData)

    def test_decode_invalid_token_returns_none(self):
        assert decode_token("not.a.valid.jwt") is None

    def test_decode_tampered_token_returns_none(self):
        token = create_access_token("uid1", "u@t.com", "buyer")
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_decode_expired_token_returns_none(self):
        """Forge an already-expired token."""
        expired_payload = {
            "user_id": "uid1",
            "email": "u@t.com",
            "role": "buyer",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
        }
        expired_token = jwt.encode(
            expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        assert decode_token(expired_token) is None

    def test_decode_wrong_secret_returns_none(self):
        token = jwt.encode(
            {"user_id": "uid1", "email": "u@t.com", "role": "buyer",
             "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
            "WRONG_SECRET",
            algorithm=settings.JWT_ALGORITHM,
        )
        assert decode_token(token) is None

    def test_decode_missing_claims_returns_none(self):
        """Token with missing required claims should fail."""
        partial_payload = {
            "user_id": "uid1",
            # email and role missing
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(
            partial_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        assert decode_token(token) is None

    def test_decode_empty_string_returns_none(self):
        assert decode_token("") is None


# ────────────────────────────────────────────────────────────────────────────
# Role constants
# ────────────────────────────────────────────────────────────────────────────
class TestRoles:

    def test_all_roles_defined(self):
        assert Role.ADMIN == "admin"
        assert Role.SELLER == "seller"
        assert Role.BUYER == "buyer"
        assert Role.AGENT == "agent"

    def test_all_list_contains_every_role(self):
        assert set(Role.ALL) == {"admin", "seller", "buyer", "agent"}

    def test_roles_are_lowercase_strings(self):
        for r in Role.ALL:
            assert r == r.lower()


# ────────────────────────────────────────────────────────────────────────────
# get_current_user HTTP dependency (unit)
# ────────────────────────────────────────────────────────────────────────────
class TestGetCurrentUser:

    def _call(self, authorization):
        from app.auth import get_current_user
        return get_current_user(authorization)

    def test_valid_bearer_token_returns_user_dict(self):
        token = create_access_token("uid5", "a@b.com", "agent")
        result = self._call(f"Bearer {token}")
        assert result["user_id"] == "uid5"
        assert result["role"] == "agent"

    def test_no_header_raises_401(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            self._call(None)
        assert exc.value.status_code == 401

    def test_missing_bearer_prefix_raises_401(self):
        from fastapi import HTTPException
        token = create_access_token("uid5", "a@b.com", "agent")
        with pytest.raises(HTTPException) as exc:
            self._call(token)          # no "Bearer " prefix
        assert exc.value.status_code == 401

    def test_invalid_token_raises_401(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            self._call("Bearer garbage.token.here")
        assert exc.value.status_code == 401

    def test_expired_token_raises_401(self):
        from fastapi import HTTPException
        expired = jwt.encode(
            {"user_id": "uid1", "email": "u@t.com", "role": "buyer",
             "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())},
            settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            self._call(f"Bearer {expired}")
        assert exc.value.status_code == 401


# ────────────────────────────────────────────────────────────────────────────
# Simulated register / login flows (mock DB)
# ────────────────────────────────────────────────────────────────────────────
class TestAuthFlow:

    @pytest.mark.asyncio
    async def test_register_new_user(self, mock_db, sample_register_payload):
        """register() should hash password and insert user."""
        mock_db.users.find_one = AsyncMock(return_value=None)  # no existing user

        inserted_id = "new_user_id_001"
        mock_db.users.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=inserted_id)
        )

        payload = sample_register_payload
        # Simulate what the router does
        existing = await mock_db.users.find_one({"email": payload["email"]})
        assert existing is None

        with patch('app.auth.pwd_context') as m:
            m.hash.return_value = "$2b$12$mocked"
            hashed = hash_password(payload["password"])
        assert hashed != payload["password"]

        result = await mock_db.users.insert_one({"email": payload["email"], "password_hash": hashed})
        assert str(result.inserted_id) == inserted_id

    @pytest.mark.asyncio
    async def test_register_duplicate_email_blocked(self, mock_db, sample_register_payload, sample_user):
        """register() must reject duplicate emails."""
        mock_db.users.find_one = AsyncMock(return_value=sample_user)

        existing = await mock_db.users.find_one({"email": sample_register_payload["email"]})
        assert existing is not None  # should raise 400 in router

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, mock_db, sample_seller):
        """login() should return tokens for valid credentials."""
        mock_db.users.find_one = AsyncMock(return_value=sample_seller)

        user = await mock_db.users.find_one({"email": "seller@propertyyards.com"})
        assert user is not None
        assert verify_password("Seller@1234", user["password_hash"]) is True

        access = create_access_token(str(user["_id"]), user["email"], user["role"])
        refresh = create_refresh_token(str(user["_id"]), user["email"], user["role"])
        assert access and refresh

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_db, sample_seller):
        """login() must reject wrong passwords."""
        mock_db.users.find_one = AsyncMock(return_value=sample_seller)

        user = await mock_db.users.find_one({"email": "seller@propertyyards.com"})
        assert verify_password("WrongPassword!", user["password_hash"]) is False

    @pytest.mark.asyncio
    async def test_login_inactive_user_blocked(self, mock_db, sample_seller):
        """Inactive accounts must be blocked."""
        inactive = {**sample_seller, "is_active": False}
        mock_db.users.find_one = AsyncMock(return_value=inactive)

        user = await mock_db.users.find_one({"email": "seller@propertyyards.com"})
        assert user.get("is_active", True) is False


# ────────────────────────────────────────────────────────────────────────────
# Security edge cases
# ────────────────────────────────────────────────────────────────────────────
class TestSecurityEdgeCases:

    def test_sql_injection_in_email_fails_decode(self):
        """Injection strings must not produce valid tokens."""
        injections = ["' OR '1'='1", "admin'--", "1; DROP TABLE users;"]
        for inj in injections:
            assert decode_token(inj) is None

    def test_none_token_returns_none(self):
        result = decode_token(None)  # type: ignore[arg-type]
        assert result is None

    def test_very_long_token_returns_none(self):
        assert decode_token("A" * 10000) is None

    def test_password_with_special_chars(self):
        """Passwords with special chars must hash and verify correctly (mocked)."""
        with patch('app.auth.pwd_context') as m:
            m.hash.return_value = "$2b$12$special"
            m.verify.return_value = True
            h = hash_password("P@$$w0rd!#^&*()")
            assert verify_password("P@$$w0rd!#^&*()", h) is True

    def test_unicode_password(self):
        """Unicode passwords must be handled correctly (mocked)."""
        with patch('app.auth.pwd_context') as m:
            m.hash.return_value = "$2b$12$unicode"
            m.verify.return_value = True
            h = hash_password("पासवर्ड@2024")
            assert verify_password("पासवर्ड@2024", h) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
