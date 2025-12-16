"""
Unit tests for authentication middleware.
"""

import pytest
from flask import g
from ara_v2.middleware.auth import (
    require_auth,
    require_tier,
    optional_auth,
    get_current_user,
    get_current_user_id
)
from ara_v2.utils.errors import AuthenticationError, AuthorizationError
from ara_v2.utils.jwt_auth import create_access_token


class TestRequireAuthDecorator:
    """Test @require_auth decorator."""

    def test_require_auth_valid_token(self, app, test_user, client):
        """Test that valid token allows access."""
        with app.app_context():
            # Create protected route
            @app.route('/protected')
            @require_auth
            def protected_route():
                user = g.current_user
                return {'message': f'Hello {user.email}'}

            # Create valid token
            token = create_access_token(test_user.id, test_user.email)

            # Make request with token
            response = client.get(
                '/protected',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200
            assert 'message' in response.json
            assert test_user.email in response.json['message']

    def test_require_auth_missing_header(self, app, client):
        """Test that missing Authorization header is rejected."""
        with app.app_context():
            @app.route('/protected')
            @require_auth
            def protected_route():
                return {'message': 'Should not reach here'}

            response = client.get('/protected')

            assert response.status_code == 401

    def test_require_auth_invalid_token(self, app, client):
        """Test that invalid token is rejected."""
        with app.app_context():
            @app.route('/protected')
            @require_auth
            def protected_route():
                return {'message': 'Should not reach here'}

            response = client.get(
                '/protected',
                headers={'Authorization': 'Bearer invalid.token.here'}
            )

            assert response.status_code == 401

    def test_require_auth_expired_token(self, app, test_user, client):
        """Test that expired token is rejected."""
        with app.app_context():
            from datetime import datetime, timedelta
            import jwt

            # Create expired token
            payload = {
                'user_id': test_user.id,
                'email': test_user.email,
                'exp': datetime.utcnow() - timedelta(hours=1),
                'iat': datetime.utcnow() - timedelta(hours=2),
                'type': 'access'
            }

            token = jwt.encode(
                payload,
                app.config['JWT_SECRET_KEY'],
                algorithm=app.config['JWT_ALGORITHM']
            )

            @app.route('/protected')
            @require_auth
            def protected_route():
                return {'message': 'Should not reach here'}

            response = client.get(
                '/protected',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 401

    def test_require_auth_nonexistent_user(self, app, client):
        """Test that token for deleted user is rejected."""
        with app.app_context():
            # Create token for non-existent user ID
            token = create_access_token(99999, "ghost@example.com")

            @app.route('/protected')
            @require_auth
            def protected_route():
                return {'message': 'Should not reach here'}

            response = client.get(
                '/protected',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 401

    def test_require_auth_sets_g_variables(self, app, test_user, client):
        """Test that decorator sets g.current_user and g.user_id."""
        with app.app_context():
            token = create_access_token(test_user.id, test_user.email)

            @app.route('/protected')
            @require_auth
            def protected_route():
                assert g.current_user is not None
                assert g.current_user.id == test_user.id
                assert g.user_id == test_user.id
                return {'status': 'ok'}

            response = client.get(
                '/protected',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200


class TestRequireTierDecorator:
    """Test @require_tier decorator."""

    def test_require_tier_student_access(self, app, test_user, client):
        """Test that student tier can access student-level routes."""
        with app.app_context():
            test_user.tier = 'student'
            token = create_access_token(test_user.id, test_user.email)

            @app.route('/student-route')
            @require_auth
            @require_tier('student')
            def student_route():
                return {'message': 'Student access granted'}

            response = client.get(
                '/student-route',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200

    def test_require_tier_researcher_access(self, app, test_user, client):
        """Test that researcher tier can access researcher routes."""
        with app.app_context():
            test_user.tier = 'researcher'
            token = create_access_token(test_user.id, test_user.email)

            @app.route('/researcher-route')
            @require_auth
            @require_tier('researcher')
            def researcher_route():
                return {'message': 'Researcher access granted'}

            response = client.get(
                '/researcher-route',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200

    def test_require_tier_institutional_access(self, app, test_user, client):
        """Test that institutional tier can access all routes."""
        with app.app_context():
            test_user.tier = 'institutional'
            token = create_access_token(test_user.id, test_user.email)

            @app.route('/institutional-route')
            @require_auth
            @require_tier('institutional')
            def institutional_route():
                return {'message': 'Institutional access granted'}

            response = client.get(
                '/institutional-route',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200

    def test_require_tier_hierarchy(self, app, test_user, client):
        """Test that higher tiers can access lower tier routes."""
        with app.app_context():
            test_user.tier = 'institutional'
            token = create_access_token(test_user.id, test_user.email)

            @app.route('/student-only')
            @require_auth
            @require_tier('student')
            def student_only():
                return {'message': 'Access granted'}

            response = client.get(
                '/student-only',
                headers={'Authorization': f'Bearer {token}'}
            )

            # Institutional (level 3) should access student (level 1) routes
            assert response.status_code == 200

    def test_require_tier_insufficient_access(self, app, test_user, client):
        """Test that lower tiers cannot access higher tier routes."""
        with app.app_context():
            test_user.tier = 'student'
            token = create_access_token(test_user.id, test_user.email)

            @app.route('/institutional-only')
            @require_auth
            @require_tier('institutional')
            def institutional_only():
                return {'message': 'Should not reach here'}

            response = client.get(
                '/institutional-only',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 403

    def test_require_tier_without_auth(self, app, client):
        """Test that @require_tier requires authentication."""
        with app.app_context():
            @app.route('/tier-route')
            @require_tier('researcher')
            def tier_route():
                return {'message': 'Should not reach here'}

            response = client.get('/tier-route')

            assert response.status_code == 401


class TestOptionalAuthDecorator:
    """Test @optional_auth decorator."""

    def test_optional_auth_with_valid_token(self, app, test_user, client):
        """Test that valid token sets user in g."""
        with app.app_context():
            token = create_access_token(test_user.id, test_user.email)

            @app.route('/optional-route')
            @optional_auth
            def optional_route():
                user = g.get('current_user')
                if user:
                    return {'message': f'Hello {user.email}'}
                return {'message': 'Hello guest'}

            response = client.get(
                '/optional-route',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200
            assert test_user.email in response.json['message']

    def test_optional_auth_without_token(self, app, client):
        """Test that missing token doesn't block access."""
        with app.app_context():
            @app.route('/optional-route')
            @optional_auth
            def optional_route():
                user = g.get('current_user')
                if user:
                    return {'message': f'Hello {user.email}'}
                return {'message': 'Hello guest'}

            response = client.get('/optional-route')

            assert response.status_code == 200
            assert 'guest' in response.json['message']

    def test_optional_auth_with_invalid_token(self, app, client):
        """Test that invalid token doesn't block access."""
        with app.app_context():
            @app.route('/optional-route')
            @optional_auth
            def optional_route():
                user = g.get('current_user')
                if user:
                    return {'message': f'Hello {user.email}'}
                return {'message': 'Hello guest'}

            response = client.get(
                '/optional-route',
                headers={'Authorization': 'Bearer invalid.token'}
            )

            # Should still succeed but without user
            assert response.status_code == 200
            assert 'guest' in response.json['message']


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_current_user_with_user(self, app, test_user):
        """Test getting current user when authenticated."""
        with app.app_context():
            with app.test_request_context():
                g.current_user = test_user

                user = get_current_user()

                assert user is not None
                assert user.id == test_user.id

    def test_get_current_user_without_user(self, app):
        """Test getting current user when not authenticated."""
        with app.app_context():
            with app.test_request_context():
                with pytest.raises(AuthenticationError) as exc_info:
                    get_current_user()

                assert "No authenticated user" in str(exc_info.value)

    def test_get_current_user_id_with_user(self, app, test_user):
        """Test getting current user ID when authenticated."""
        with app.app_context():
            with app.test_request_context():
                g.user_id = test_user.id

                user_id = get_current_user_id()

                assert user_id == test_user.id

    def test_get_current_user_id_without_user(self, app):
        """Test getting current user ID when not authenticated."""
        with app.app_context():
            with app.test_request_context():
                with pytest.raises(AuthenticationError) as exc_info:
                    get_current_user_id()

                assert "No authenticated user" in str(exc_info.value)
