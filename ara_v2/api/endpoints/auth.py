"""
Authentication endpoints for ARA v2.
Handles user registration, login, token refresh, and logout.
"""

from flask import Blueprint, request, jsonify, current_app
from ara_v2.models.user import User
from ara_v2.utils.database import db
from ara_v2.utils.password import (
    validate_password,
    validate_email,
    hash_password,
    verify_password
)
from ara_v2.utils.jwt_auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    revoke_refresh_token,
    get_token_from_header
)
from ara_v2.middleware.auth import require_auth, get_current_user
from ara_v2.utils.errors import (
    ValidationError,
    AuthenticationError,
    ConflictError
)
from ara_v2.utils.rate_limiter import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour")  # Strict limit to prevent abuse
def register():
    """
    Register a new user.

    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "tier": "researcher"  # Optional: student, researcher, institutional
        }

    Returns:
        {
            "user": {
                "id": 1,
                "email": "user@example.com",
                "tier": "researcher",
                "created_at": "2025-12-14T10:00:00Z"
            },
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "Bearer"
        }

    Raises:
        ValidationError: If email/password invalid
        ConflictError: If email already registered
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        tier = data.get('tier', 'researcher')

        # Validate email
        email_valid, email_error = validate_email(email)
        if not email_valid:
            raise ValidationError(email_error)

        # Validate password
        password_valid, password_error = validate_password(password)
        if not password_valid:
            raise ValidationError(password_error)

        # Validate tier
        valid_tiers = ['student', 'researcher', 'institutional']
        if tier not in valid_tiers:
            raise ValidationError(f'Invalid tier. Must be one of: {", ".join(valid_tiers)}')

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ConflictError('Email already registered')

        # Create new user
        user = User(
            email=email,
            password_hash=hash_password(password),
            tier=tier
        )

        db.session.add(user)
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        current_app.logger.info(f"New user registered: {user.email} (ID: {user.id})")

        return jsonify({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }), 201

    except (ValidationError, ConflictError) as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        raise


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")  # Prevent brute force attacks
def login():
    """
    Authenticate user and return tokens.

    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }

    Returns:
        {
            "user": {
                "id": 1,
                "email": "user@example.com",
                "tier": "researcher"
            },
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "Bearer"
        }

    Raises:
        AuthenticationError: If credentials are invalid
        ValidationError: If email/password missing
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            raise ValidationError('Email and password are required')

        # Find user
        user = User.query.filter_by(email=email).first()

        if not user:
            raise AuthenticationError('Invalid email or password')

        # Verify password
        if not verify_password(user.password_hash, password):
            current_app.logger.warning(f"Failed login attempt for: {email}")
            raise AuthenticationError('Invalid email or password')

        # Generate tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        # Update last login
        user.update_last_active()
        db.session.commit()

        current_app.logger.info(f"User logged in: {user.email} (ID: {user.id})")

        return jsonify({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }), 200

    except (ValidationError, AuthenticationError) as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        raise


@auth_bp.route('/refresh', methods=['POST'])
@limiter.limit("20 per hour")  # Allow reasonable token refreshes
def refresh():
    """
    Refresh access token using refresh token.

    Request body:
        {
            "refresh_token": "eyJ..."
        }

    Returns:
        {
            "access_token": "eyJ...",
            "token_type": "Bearer"
        }

    Raises:
        AuthenticationError: If refresh token is invalid or expired
        ValidationError: If refresh token missing
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        refresh_token = data.get('refresh_token', '')

        if not refresh_token:
            raise ValidationError('Refresh token is required')

        # Verify refresh token
        payload = verify_token(refresh_token, expected_type='refresh')

        user_id = payload.get('user_id')

        # Get user
        user = User.query.get(user_id)

        if not user:
            raise AuthenticationError('User not found')

        # Generate new access token
        access_token = create_access_token(user.id, user.email)

        current_app.logger.info(f"Token refreshed for user: {user.email} (ID: {user.id})")

        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer'
        }), 200

    except (ValidationError, AuthenticationError) as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        raise


@auth_bp.route('/logout', methods=['POST'])
@require_auth
@limiter.limit("30 per hour")
def logout():
    """
    Revoke refresh token (logout).

    Requires: Authorization header with access token

    Request body:
        {
            "refresh_token": "eyJ..."
        }

    Returns:
        {
            "message": "Logged out successfully"
        }

    Raises:
        ValidationError: If refresh token missing
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        refresh_token = data.get('refresh_token', '')

        if not refresh_token:
            raise ValidationError('Refresh token is required')

        # Revoke the refresh token
        revoke_refresh_token(refresh_token)

        user = get_current_user()
        current_app.logger.info(f"User logged out: {user.email} (ID: {user.id})")

        return jsonify({
            'message': 'Logged out successfully'
        }), 200

    except ValidationError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        raise


@auth_bp.route('/me', methods=['GET'])
@require_auth
def me():
    """
    Get current authenticated user profile.

    Requires: Authorization header with access token

    Returns:
        {
            "id": 1,
            "email": "user@example.com",
            "tier": "researcher",
            "created_at": "2025-12-14T10:00:00Z",
            "last_active": "2025-12-14T12:30:00Z"
        }
    """
    try:
        user = get_current_user()

        return jsonify(user.to_dict()), 200

    except Exception as e:
        current_app.logger.error(f"Get user profile error: {str(e)}")
        raise
