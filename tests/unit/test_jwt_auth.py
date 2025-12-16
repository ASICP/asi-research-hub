"""
Unit tests for JWT authentication utilities.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from ara_v2.utils.jwt_auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    revoke_refresh_token,
    get_token_from_header
)
from ara_v2.utils.errors import AuthenticationError


class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token(self, app):
        """Test access token creation."""
        with app.app_context():
            user_id = 1
            email = "test@example.com"

            token = create_access_token(user_id, email)

            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0

    def test_access_token_payload(self, app):
        """Test access token contains correct payload."""
        with app.app_context():
            user_id = 42
            email = "user@test.com"

            token = create_access_token(user_id, email)

            # Decode without verification to check payload
            payload = jwt.decode(
                token,
                app.config['JWT_SECRET_KEY'],
                algorithms=[app.config['JWT_ALGORITHM']]
            )

            assert payload['user_id'] == user_id
            assert payload['email'] == email
            assert payload['type'] == 'access'
            assert 'exp' in payload
            assert 'iat' in payload

    def test_access_token_expiry(self, app):
        """Test access token expiration time."""
        with app.app_context():
            token = create_access_token(1, "test@example.com")

            payload = jwt.decode(
                token,
                app.config['JWT_SECRET_KEY'],
                algorithms=[app.config['JWT_ALGORITHM']]
            )

            exp = datetime.fromtimestamp(payload['exp'])
            iat = datetime.fromtimestamp(payload['iat'])
            duration = exp - iat

            # Should be 24 hours (configured in config)
            expected_duration = app.config['JWT_ACCESS_TOKEN_EXPIRY']
            assert abs(duration - expected_duration) < timedelta(seconds=2)

    def test_create_refresh_token(self, app, redis_client):
        """Test refresh token creation."""
        with app.app_context():
            user_id = 1

            token = create_refresh_token(user_id)

            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0

    def test_refresh_token_payload(self, app, redis_client):
        """Test refresh token contains correct payload."""
        with app.app_context():
            user_id = 99

            token = create_refresh_token(user_id)

            payload = jwt.decode(
                token,
                app.config['JWT_SECRET_KEY'],
                algorithms=[app.config['JWT_ALGORITHM']]
            )

            assert payload['user_id'] == user_id
            assert payload['type'] == 'refresh'
            assert 'jti' in payload  # Unique token ID
            assert 'exp' in payload
            assert 'iat' in payload

    def test_refresh_token_stored_in_redis(self, app, redis_client):
        """Test that refresh token is stored in Redis."""
        with app.app_context():
            user_id = 5

            token = create_refresh_token(user_id)

            payload = jwt.decode(
                token,
                app.config['JWT_SECRET_KEY'],
                algorithms=[app.config['JWT_ALGORITHM']]
            )

            jti = payload['jti']
            key = f"refresh_token:{jti}"

            # Check Redis storage
            stored_value = redis_client.get(key)
            assert stored_value is not None
            assert int(stored_value) == user_id


class TestTokenVerification:
    """Test JWT token verification."""

    def test_verify_valid_access_token(self, app):
        """Test verification of valid access token."""
        with app.app_context():
            token = create_access_token(1, "test@example.com")

            payload = verify_token(token, expected_type='access')

            assert payload is not None
            assert payload['user_id'] == 1
            assert payload['type'] == 'access'

    def test_verify_valid_refresh_token(self, app, redis_client):
        """Test verification of valid refresh token."""
        with app.app_context():
            token = create_refresh_token(1)

            payload = verify_token(token, expected_type='refresh')

            assert payload is not None
            assert payload['user_id'] == 1
            assert payload['type'] == 'refresh'

    def test_verify_expired_token(self, app):
        """Test verification of expired token."""
        with app.app_context():
            # Create token with past expiry
            payload = {
                'user_id': 1,
                'email': 'test@example.com',
                'exp': datetime.utcnow() - timedelta(hours=1),
                'iat': datetime.utcnow() - timedelta(hours=2),
                'type': 'access'
            }

            token = jwt.encode(
                payload,
                app.config['JWT_SECRET_KEY'],
                algorithm=app.config['JWT_ALGORITHM']
            )

            with pytest.raises(AuthenticationError) as exc_info:
                verify_token(token, expected_type='access')

            assert "expired" in str(exc_info.value).lower()

    def test_verify_wrong_token_type(self, app):
        """Test verification fails for wrong token type."""
        with app.app_context():
            # Create access token
            token = create_access_token(1, "test@example.com")

            # Try to verify as refresh token
            with pytest.raises(AuthenticationError) as exc_info:
                verify_token(token, expected_type='refresh')

            assert "Invalid token type" in str(exc_info.value)

    def test_verify_invalid_token(self, app):
        """Test verification of completely invalid token."""
        with app.app_context():
            with pytest.raises(AuthenticationError) as exc_info:
                verify_token("not.a.valid.token", expected_type='access')

            assert "Invalid token" in str(exc_info.value)

    def test_verify_token_wrong_signature(self, app):
        """Test verification fails with wrong signature."""
        with app.app_context():
            # Create token with different secret
            payload = {
                'user_id': 1,
                'email': 'test@example.com',
                'exp': datetime.utcnow() + timedelta(hours=1),
                'type': 'access'
            }

            token = jwt.encode(payload, "wrong-secret", algorithm='HS256')

            with pytest.raises(AuthenticationError):
                verify_token(token, expected_type='access')

    def test_verify_revoked_refresh_token(self, app, redis_client):
        """Test verification fails for revoked refresh token."""
        with app.app_context():
            token = create_refresh_token(1)

            # Revoke the token
            revoke_refresh_token(token)

            # Verification should fail
            with pytest.raises(AuthenticationError) as exc_info:
                verify_token(token, expected_type='refresh')

            assert "revoked" in str(exc_info.value).lower()


class TestTokenRevocation:
    """Test refresh token revocation."""

    def test_revoke_refresh_token(self, app, redis_client):
        """Test refresh token revocation."""
        with app.app_context():
            token = create_refresh_token(1)

            # Verify token exists in Redis
            payload = jwt.decode(
                token,
                app.config['JWT_SECRET_KEY'],
                algorithms=[app.config['JWT_ALGORITHM']]
            )
            jti = payload['jti']
            assert redis_client.exists(f"refresh_token:{jti}")

            # Revoke token
            revoke_refresh_token(token)

            # Verify token removed from Redis
            assert not redis_client.exists(f"refresh_token:{jti}")

    def test_revoke_invalid_token(self, app, redis_client):
        """Test revoking invalid token doesn't raise error."""
        with app.app_context():
            # Should not raise exception
            revoke_refresh_token("invalid.token.here")

    def test_revoke_already_revoked_token(self, app, redis_client):
        """Test revoking already revoked token."""
        with app.app_context():
            token = create_refresh_token(1)

            # Revoke twice
            revoke_refresh_token(token)
            revoke_refresh_token(token)  # Should not raise error


class TestHeaderParsing:
    """Test Authorization header parsing."""

    def test_get_token_from_valid_header(self):
        """Test extracting token from valid Authorization header."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        header = f"Bearer {token}"

        extracted_token = get_token_from_header(header)

        assert extracted_token == token

    def test_get_token_case_insensitive(self):
        """Test Bearer keyword is case insensitive."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        headers = [
            f"Bearer {token}",
            f"bearer {token}",
            f"BEARER {token}",
        ]

        for header in headers:
            extracted_token = get_token_from_header(header)
            assert extracted_token == token

    def test_get_token_missing_header(self):
        """Test error when header is missing."""
        with pytest.raises(AuthenticationError) as exc_info:
            get_token_from_header(None)

        assert "No authorization header" in str(exc_info.value)

    def test_get_token_empty_header(self):
        """Test error when header is empty."""
        with pytest.raises(AuthenticationError) as exc_info:
            get_token_from_header("")

        assert "No authorization header" in str(exc_info.value)

    def test_get_token_invalid_format_no_bearer(self):
        """Test error when Bearer keyword is missing."""
        with pytest.raises(AuthenticationError) as exc_info:
            get_token_from_header("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

        assert "Invalid authorization header format" in str(exc_info.value)
        assert "Bearer" in str(exc_info.value)

    def test_get_token_invalid_format_wrong_scheme(self):
        """Test error when wrong authentication scheme is used."""
        with pytest.raises(AuthenticationError) as exc_info:
            get_token_from_header("Basic dXNlcjpwYXNz")

        assert "Invalid authorization header format" in str(exc_info.value)

    def test_get_token_invalid_format_too_many_parts(self):
        """Test error when header has too many parts."""
        with pytest.raises(AuthenticationError) as exc_info:
            get_token_from_header("Bearer token extra parts")

        assert "Invalid authorization header format" in str(exc_info.value)
