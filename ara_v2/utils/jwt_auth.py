"""
JWT authentication utilities for ARA v2.
Handles JWT token creation, verification, and refresh tokens.
"""

import jwt
import secrets
from datetime import datetime, timedelta
from flask import current_app
from ara_v2.utils.redis_client import get_redis
from ara_v2.utils.errors import AuthenticationError


def create_access_token(user_id: int, email: str) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User's database ID
        email: User's email address

    Returns:
        str: JWT access token
    """
    config = current_app.config

    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + config['JWT_ACCESS_TOKEN_EXPIRY'],
        'iat': datetime.utcnow(),
        'type': 'access'
    }

    return jwt.encode(
        payload,
        config['JWT_SECRET_KEY'],
        algorithm=config['JWT_ALGORITHM']
    )


def create_refresh_token(user_id: int) -> str:
    """
    Create JWT refresh token and store in Redis.

    Args:
        user_id: User's database ID

    Returns:
        str: JWT refresh token
    """
    config = current_app.config
    redis_client = get_redis()

    # Generate unique token ID
    jti = secrets.token_urlsafe(32)

    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + config['JWT_REFRESH_TOKEN_EXPIRY'],
        'iat': datetime.utcnow(),
        'type': 'refresh',
        'jti': jti
    }

    token = jwt.encode(
        payload,
        config['JWT_SECRET_KEY'],
        algorithm=config['JWT_ALGORITHM']
    )

    # Store refresh token in Redis for revocation support
    if redis_client:
        expiry_seconds = int(config['JWT_REFRESH_TOKEN_EXPIRY'].total_seconds())
        redis_client.setex(
            f"refresh_token:{jti}",
            expiry_seconds,
            user_id
        )

    return token


def verify_token(token: str, expected_type: str = 'access') -> dict:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token to verify
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        dict: Decoded token payload

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    config = current_app.config

    try:
        payload = jwt.decode(
            token,
            config['JWT_SECRET_KEY'],
            algorithms=[config['JWT_ALGORITHM']]
        )

        # Check token type
        if payload.get('type') != expected_type:
            raise AuthenticationError('Invalid token type')

        # For refresh tokens, check if revoked
        if expected_type == 'refresh':
            jti = payload.get('jti')
            redis_client = get_redis()

            if redis_client and not redis_client.exists(f"refresh_token:{jti}"):
                raise AuthenticationError('Token has been revoked')

        return payload

    except jwt.ExpiredSignatureError:
        raise AuthenticationError('Token has expired')
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f'Invalid token: {str(e)}')


def revoke_refresh_token(token: str):
    """
    Revoke a refresh token.

    Args:
        token: Refresh token to revoke
    """
    redis_client = get_redis()

    if not redis_client:
        return  # Can't revoke without Redis

    try:
        config = current_app.config
        payload = jwt.decode(
            token,
            config['JWT_SECRET_KEY'],
            algorithms=[config['JWT_ALGORITHM']]
        )

        jti = payload.get('jti')
        if jti:
            redis_client.delete(f"refresh_token:{jti}")
            current_app.logger.info(f"Revoked refresh token: {jti}")

    except jwt.InvalidTokenError:
        pass  # Token already invalid, no need to revoke


def get_token_from_header(authorization_header: str) -> str:
    """
    Extract token from Authorization header.

    Args:
        authorization_header: Authorization header value

    Returns:
        str: Token

    Raises:
        AuthenticationError: If header format is invalid
    """
    if not authorization_header:
        raise AuthenticationError('No authorization header provided')

    parts = authorization_header.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise AuthenticationError('Invalid authorization header format (use: Bearer <token>)')

    return parts[1]
