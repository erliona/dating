"""Tests for Epic A2: Server-side validation of initData + JWT.

This test suite covers:
- HMAC-SHA256 validation of Telegram WebApp initData
- TTL checking for auth_date
- JWT token generation and validation
- Session refresh functionality
- Security logging
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import jwt
import pytest

from bot.security import (
    JWT_ALGORITHM,
    JWT_TTL_HOURS,
    ValidationError,
    generate_jwt_token,
    refresh_session,
    validate_jwt_token,
    validate_webapp_init_data,
)


class TestValidateWebAppInitData:
    """Tests for validate_webapp_init_data function."""

    def create_valid_init_data(self, bot_token: str, auth_date: int = None) -> str:
        """Helper to create valid initData with correct HMAC."""
        if auth_date is None:
            auth_date = int(time.time())

        user_data = {
            "id": 123456,
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "language_code": "en",
        }

        data = {
            "query_id": "test_query_id",
            "user": json.dumps(user_data),
            "auth_date": str(auth_date),
            "hash": "",  # Will be calculated
        }

        # Calculate HMAC
        data_check_string = "\n".join(
            [f"{k}={v}" for k, v in sorted(data.items()) if k != "hash"]
        )

        secret_key = hmac.new(
            key="WebAppData".encode(), msg=bot_token.encode(), digestmod=hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256
        ).hexdigest()

        data["hash"] = calculated_hash

        return urlencode(data)

    def test_valid_init_data(self):
        """Test validation of valid initData."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        init_data = self.create_valid_init_data(bot_token)

        result = validate_webapp_init_data(init_data, bot_token)

        assert "user" in result
        assert result["user"]["id"] == 123456
        assert result["user"]["username"] == "johndoe"
        assert "auth_date" in result

    def test_empty_init_data(self):
        """Test that empty initData raises ValidationError."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

        with pytest.raises(ValidationError, match="initData is empty"):
            validate_webapp_init_data("", bot_token)

    def test_missing_hash(self):
        """Test that missing hash raises ValidationError."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        init_data = urlencode(
            {"user": json.dumps({"id": 123}), "auth_date": str(int(time.time()))}
        )

        with pytest.raises(ValidationError, match="Missing hash"):
            validate_webapp_init_data(init_data, bot_token)

    def test_missing_auth_date(self):
        """Test that missing auth_date raises ValidationError."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        init_data = urlencode({"user": json.dumps({"id": 123}), "hash": "dummy_hash"})

        with pytest.raises(ValidationError, match="Missing auth_date"):
            validate_webapp_init_data(init_data, bot_token)

    def test_invalid_auth_date_format(self):
        """Test that invalid auth_date format raises ValidationError."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        init_data = urlencode(
            {
                "user": json.dumps({"id": 123}),
                "auth_date": "not_a_number",
                "hash": "dummy_hash",
            }
        )

        with pytest.raises(ValidationError, match="Invalid auth_date format"):
            validate_webapp_init_data(init_data, bot_token)

    def test_expired_init_data(self):
        """Test that old initData is rejected (TTL check)."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        # Create initData that's 2 hours old
        old_auth_date = int(time.time()) - 7200
        init_data = self.create_valid_init_data(bot_token, old_auth_date)

        with pytest.raises(ValidationError, match="too old"):
            validate_webapp_init_data(init_data, bot_token, max_age_seconds=3600)

    def test_future_auth_date(self):
        """Test that future auth_date is rejected."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        # Create initData with future timestamp
        future_auth_date = int(time.time()) + 3600
        init_data = self.create_valid_init_data(bot_token, future_auth_date)

        with pytest.raises(ValidationError, match="future"):
            validate_webapp_init_data(init_data, bot_token)

    def test_invalid_hmac(self):
        """Test that incorrect HMAC is rejected."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        wrong_bot_token = "654321:XYZ-ABC9876efGhi-abc12D3e4f567gh88"

        # Create initData with one token but validate with another
        init_data = self.create_valid_init_data(wrong_bot_token)

        with pytest.raises(ValidationError, match="HMAC validation failed"):
            validate_webapp_init_data(init_data, bot_token)

    def test_tampered_data(self):
        """Test that tampered data is rejected."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        init_data = self.create_valid_init_data(bot_token)

        # Tamper with the data by changing user ID
        tampered_data = init_data.replace("123456", "999999")

        with pytest.raises(ValidationError, match="HMAC validation failed"):
            validate_webapp_init_data(tampered_data, bot_token)

    def test_valid_with_custom_max_age(self):
        """Test validation with custom max_age_seconds."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        # Create initData that's 30 minutes old
        old_auth_date = int(time.time()) - 1800
        init_data = self.create_valid_init_data(bot_token, old_auth_date)

        # Should succeed with 1 hour max age
        result = validate_webapp_init_data(init_data, bot_token, max_age_seconds=3600)
        assert result["user"]["id"] == 123456

        # Should fail with 15 minutes max age
        with pytest.raises(ValidationError, match="too old"):
            validate_webapp_init_data(init_data, bot_token, max_age_seconds=900)


class TestJWTTokens:
    """Tests for JWT token generation and validation."""

    def test_generate_jwt_token(self):
        """Test JWT token generation."""
        user_id = 123456
        secret_key = "test_secret_key"

        token = generate_jwt_token(user_id, secret_key)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode without verification to check payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["user_id"] == user_id
        assert "iat" in decoded
        assert "exp" in decoded
        assert "nbf" in decoded

    def test_generate_jwt_with_additional_claims(self):
        """Test JWT generation with additional claims."""
        user_id = 123456
        secret_key = "test_secret_key"
        additional_claims = {"username": "johndoe", "role": "user"}

        token = generate_jwt_token(user_id, secret_key, additional_claims)

        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["user_id"] == user_id
        assert decoded["username"] == "johndoe"
        assert decoded["role"] == "user"

    def test_jwt_ttl(self):
        """Test that JWT has correct TTL (24 hours)."""
        user_id = 123456
        secret_key = "test_secret_key"

        before = datetime.now(timezone.utc).replace(microsecond=0)
        token = generate_jwt_token(user_id, secret_key)
        after = datetime.now(timezone.utc).replace(microsecond=0)

        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)

        # Check that expiration is approximately 24 hours from issuance
        ttl = exp_time - iat_time
        assert ttl.total_seconds() == JWT_TTL_HOURS * 3600

        # Check that issuance time is approximately now (within 2 seconds for test execution)
        # Note: JWT timestamps are in seconds, so we need to account for microsecond truncation
        assert before <= iat_time <= after + timedelta(seconds=2)

    def test_validate_valid_jwt(self):
        """Test validation of a valid JWT token."""
        user_id = 123456
        secret_key = "test_secret_key"

        token = generate_jwt_token(user_id, secret_key)
        payload = validate_jwt_token(token, secret_key)

        assert payload["user_id"] == user_id

    def test_validate_expired_jwt(self):
        """Test that expired JWT is rejected."""
        user_id = 123456
        secret_key = "test_secret_key"

        # Create a token that expired 1 hour ago
        past_time = datetime.now(timezone.utc) - timedelta(hours=25)
        payload = {
            "user_id": user_id,
            "iat": int(past_time.timestamp()),
            "exp": int((past_time + timedelta(hours=24)).timestamp()),
            "nbf": int(past_time.timestamp()),
        }

        token = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)

        with pytest.raises(ValidationError, match="expired"):
            validate_jwt_token(token, secret_key)

    def test_validate_jwt_wrong_secret(self):
        """Test that JWT with wrong secret is rejected."""
        user_id = 123456
        secret_key = "test_secret_key"
        wrong_secret = "wrong_secret_key"

        token = generate_jwt_token(user_id, secret_key)

        with pytest.raises(ValidationError, match="Invalid token"):
            validate_jwt_token(token, wrong_secret)

    def test_validate_jwt_tampered(self):
        """Test that tampered JWT is rejected."""
        user_id = 123456
        secret_key = "test_secret_key"

        token = generate_jwt_token(user_id, secret_key)

        # Tamper with the token by changing a character
        tampered_token = token[:-5] + "XXXXX"

        with pytest.raises(ValidationError, match="Invalid token"):
            validate_jwt_token(tampered_token, secret_key)

    def test_validate_jwt_missing_required_claims(self):
        """Test that JWT without required claims is rejected."""
        secret_key = "test_secret_key"

        # Create token without required user_id claim
        now = datetime.now(timezone.utc)
        payload = {
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
        }

        token = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)

        with pytest.raises(ValidationError, match="Invalid token"):
            validate_jwt_token(token, secret_key)


class TestRefreshSession:
    """Tests for session refresh functionality."""

    def create_valid_init_data(self, bot_token: str, user_id: int = 123456) -> str:
        """Helper to create valid initData."""
        auth_date = int(time.time())

        user_data = {
            "id": user_id,
            "first_name": "John",
            "username": "johndoe",
            "language_code": "en",
        }

        data = {
            "query_id": "test_query_id",
            "user": json.dumps(user_data),
            "auth_date": str(auth_date),
        }

        # Calculate HMAC
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])

        secret_key_hmac = hmac.new(
            key="WebAppData".encode(), msg=bot_token.encode(), digestmod=hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key_hmac,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        data["hash"] = calculated_hash

        return urlencode(data)

    def test_refresh_session_success(self):
        """Test successful session refresh."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        secret_key = "test_jwt_secret"
        init_data = self.create_valid_init_data(bot_token)

        validated_data, jwt_token = refresh_session(init_data, bot_token, secret_key)

        # Check validated data
        assert validated_data["user"]["id"] == 123456
        assert validated_data["user"]["username"] == "johndoe"

        # Check JWT token
        assert isinstance(jwt_token, str)
        payload = validate_jwt_token(jwt_token, secret_key)
        assert payload["user_id"] == 123456
        assert payload["username"] == "johndoe"

    def test_refresh_session_invalid_init_data(self):
        """Test that refresh fails with invalid initData."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        secret_key = "test_jwt_secret"
        invalid_init_data = "invalid_data"

        with pytest.raises(ValidationError):
            refresh_session(invalid_init_data, bot_token, secret_key)

    def test_refresh_session_expired_init_data(self):
        """Test that refresh fails with expired initData."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        secret_key = "test_jwt_secret"

        # Create old initData
        old_auth_date = int(time.time()) - 7200
        user_data = {"id": 123456, "username": "johndoe"}
        data = {
            "user": json.dumps(user_data),
            "auth_date": str(old_auth_date),
        }
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
        secret_key_hmac = hmac.new(
            key="WebAppData".encode(), msg=bot_token.encode(), digestmod=hashlib.sha256
        ).digest()
        calculated_hash = hmac.new(
            key=secret_key_hmac,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        data["hash"] = calculated_hash
        init_data = urlencode(data)

        with pytest.raises(ValidationError, match="too old"):
            refresh_session(init_data, bot_token, secret_key, max_age_seconds=3600)

    def test_refresh_session_generates_new_jwt(self):
        """Test that each refresh generates a new JWT."""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        secret_key = "test_jwt_secret"
        init_data = self.create_valid_init_data(bot_token)

        _, token1 = refresh_session(init_data, bot_token, secret_key)
        time.sleep(
            1.1
        )  # Delay to ensure different timestamps (needs >1 second for int timestamps)

        # Create new init_data to ensure different auth_date
        init_data2 = self.create_valid_init_data(bot_token)
        _, token2 = refresh_session(init_data2, bot_token, secret_key)

        # Tokens should be different (different iat)
        assert token1 != token2

        # But both should be valid
        payload1 = validate_jwt_token(token1, secret_key)
        payload2 = validate_jwt_token(token2, secret_key)

        assert payload1["user_id"] == payload2["user_id"]
        assert payload1["iat"] < payload2["iat"]  # Second token issued later


class TestSecurityIntegration:
    """Integration tests for the security module."""

    def test_full_authentication_flow(self):
        """Test complete authentication flow from initData to JWT."""
        # Simulate bot and user
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        jwt_secret = "test_jwt_secret"
        user_id = 123456

        # Step 1: User opens Mini App, Telegram provides initData
        auth_date = int(time.time())
        user_data = {
            "id": user_id,
            "first_name": "John",
            "username": "johndoe",
            "language_code": "en",
        }
        data = {
            "query_id": "test_query",
            "user": json.dumps(user_data),
            "auth_date": str(auth_date),
        }
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
        secret_key_hmac = hmac.new(
            key="WebAppData".encode(), msg=bot_token.encode(), digestmod=hashlib.sha256
        ).digest()
        calculated_hash = hmac.new(
            key=secret_key_hmac,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        data["hash"] = calculated_hash
        init_data = urlencode(data)

        # Step 2: Server validates initData and generates JWT
        validated_data, jwt_token = refresh_session(init_data, bot_token, jwt_secret)

        assert validated_data["user"]["id"] == user_id

        # Step 3: Server validates JWT for subsequent requests
        payload = validate_jwt_token(jwt_token, jwt_secret)

        assert payload["user_id"] == user_id
        assert payload["username"] == "johndoe"

        # Step 4: After 24 hours, JWT expires and needs refresh
        # (simulated by creating expired token)
        now_utc = datetime.now(timezone.utc)
        old_payload = {
            "user_id": user_id,
            "iat": int((now_utc - timedelta(hours=25)).timestamp()),
            "exp": int((now_utc - timedelta(hours=1)).timestamp()),
            "nbf": int((now_utc - timedelta(hours=25)).timestamp()),
        }
        expired_token = jwt.encode(old_payload, jwt_secret, algorithm=JWT_ALGORITHM)

        # Expired token should be rejected
        with pytest.raises(ValidationError, match="expired"):
            validate_jwt_token(expired_token, jwt_secret)

        # User needs to get new initData from Telegram and refresh session
        new_init_data = urlencode(data)  # In reality, this would be fresh from Telegram
        _, new_jwt_token = refresh_session(new_init_data, bot_token, jwt_secret)

        # New token should work
        new_payload = validate_jwt_token(new_jwt_token, jwt_secret)
        assert new_payload["user_id"] == user_id
