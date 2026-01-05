"""
Authentication middleware for ARA v2.
Provides decorators for protecting routes.
"""

from functools import wraps
from flask import request, g, current_app
from ara_v2.utils.jwt_auth import verify_token, get_token_from_header
from ara_v2.utils.errors import AuthenticationError, AuthorizationError
from ara_v2.models.user import User


def require_auth(f):
    """
    Decorator to require authentication for a route.

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user = g.current_user
            return {'message': f'Hello {user.email}'}

    Raises:
        AuthenticationError: If token is invalid or missing
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow OPTIONS requests for CORS preflight
        if request.method == 'OPTIONS':
            return current_app.response_class('', status=200)

        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            current_app.logger.info(f"Auth check for {request.path}: Header present? {bool(auth_header)}")
            
            token = get_token_from_header(auth_header)
            
            # Verify token
            payload = verify_token(token, expected_type='access')
            current_app.logger.info(f"Token verified for user {payload.get('user_id')}")

            # Get user from database
            user_id = payload.get('user_id')
            user = User.query.get(user_id)

            if not user:
                current_app.logger.warning(f"User {user_id} not found in DB")
                raise AuthenticationError('User not found')

            # Store user in Flask g object for access in route
            g.current_user = user
            g.user_id = user.id
            g.is_admin = getattr(user, 'is_admin', False)

            # Update last active timestamp
            user.update_last_active()
            from ara_v2.utils.database import db
            db.session.commit()

        except AuthenticationError as e:
            current_app.logger.warning(f"Authentication failed: {e.message}")
            raise
        except Exception as e:
            current_app.logger.error(f"Auth middleware error: {e}")
            raise AuthenticationError(str(e))

        return f(*args, **kwargs)

    return decorated_function


def require_tier(required_tier: str):
    """
    Decorator to require specific user tier.

    Args:
        required_tier: Required tier ('student', 'researcher', 'institutional')

    Usage:
        @app.route('/admin')
        @require_auth
        @require_tier('institutional')
        def admin_route():
            return {'message': 'Admin access granted'}

    Raises:
        AuthorizationError: If user doesn't have required tier
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = g.get('current_user')

            if not user:
                raise AuthenticationError('Authentication required')

            # Define tier hierarchy
            tier_levels = {
                'student': 1,
                'researcher': 2,
                'institutional': 3
            }

            user_level = tier_levels.get(user.tier, 0)
            required_level = tier_levels.get(required_tier, 999)

            if user_level < required_level:
                raise AuthorizationError(
                    f'Tier {required_tier} or higher required'
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def optional_auth(f):
    """
    Decorator that provides user info if authenticated, but doesn't require it.

    Usage:
        @app.route('/public-but-personalized')
        @optional_auth
        def public_route():
            user = g.get('current_user')
            if user:
                return {'message': f'Hello {user.email}'}
            return {'message': 'Hello guest'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                token = get_token_from_header(auth_header)
                payload = verify_token(token, expected_type='access')

                user_id = payload.get('user_id')
                user = User.query.get(user_id)

                if user:
                    g.current_user = user
                    g.user_id = user.id

        except (AuthenticationError, Exception):
            # Don't raise error, just continue without user
            pass

        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> User:
    """
    Get current authenticated user from Flask g object.

    Returns:
        User: Current user

    Raises:
        AuthenticationError: If no user is authenticated
    """
    user = g.get('current_user')
    if not user:
        raise AuthenticationError('No authenticated user')
    return user


def get_current_user_id() -> int:
    """
    Get current authenticated user ID.

    Returns:
        int: User ID

    Raises:
        AuthenticationError: If no user is authenticated
    """
    user_id = g.get('user_id')
    if not user_id:
        raise AuthenticationError('No authenticated user')
    return user_id
