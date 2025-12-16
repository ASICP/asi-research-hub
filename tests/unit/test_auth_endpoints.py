"""
Integration tests for authentication endpoints.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from ara_v2.models.user import User
from ara_v2.utils.database import db


class TestRegisterEndpoint:
    """Test POST /api/register endpoint."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post('/api/register', json={
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'tier': 'researcher'
        })

        assert response.status_code == 201
        data = response.json

        # Check response structure
        assert 'user' in data
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'token_type' in data

        # Check user data
        assert data['user']['email'] == 'newuser@example.com'
        assert data['user']['tier'] == 'researcher'
        assert 'id' in data['user']

        # Check tokens
        assert data['token_type'] == 'Bearer'
        assert len(data['access_token']) > 0
        assert len(data['refresh_token']) > 0

    def test_register_default_tier(self, client):
        """Test registration with default tier."""
        response = client.post('/api/register', json={
            'email': 'defaulttier@example.com',
            'password': 'SecurePass123!'
        })

        assert response.status_code == 201
        assert response.json['user']['tier'] == 'researcher'

    def test_register_student_tier(self, client):
        """Test registration with student tier."""
        response = client.post('/api/register', json={
            'email': 'student@example.com',
            'password': 'SecurePass123!',
            'tier': 'student'
        })

        assert response.status_code == 201
        assert response.json['user']['tier'] == 'student'

    def test_register_institutional_tier(self, client):
        """Test registration with institutional tier."""
        response = client.post('/api/register', json={
            'email': 'institution@example.com',
            'password': 'SecurePass123!',
            'tier': 'institutional'
        })

        assert response.status_code == 201
        assert response.json['user']['tier'] == 'institutional'

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        response = client.post('/api/register', json={
            'email': test_user.email,
            'password': 'SecurePass123!',
            'tier': 'researcher'
        })

        assert response.status_code == 409
        assert 'already registered' in response.json['error'].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post('/api/register', json={
            'email': 'not-an-email',
            'password': 'SecurePass123!',
            'tier': 'researcher'
        })

        assert response.status_code == 400
        assert 'email' in response.json['error'].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/api/register', json={
            'email': 'user@example.com',
            'password': 'weak',
            'tier': 'researcher'
        })

        assert response.status_code == 400
        assert 'password' in response.json['error'].lower()

    def test_register_invalid_tier(self, client):
        """Test registration with invalid tier."""
        response = client.post('/api/register', json={
            'email': 'user@example.com',
            'password': 'SecurePass123!',
            'tier': 'invalid_tier'
        })

        assert response.status_code == 400
        assert 'tier' in response.json['error'].lower()

    def test_register_missing_email(self, client):
        """Test registration without email."""
        response = client.post('/api/register', json={
            'password': 'SecurePass123!',
            'tier': 'researcher'
        })

        assert response.status_code == 400

    def test_register_missing_password(self, client):
        """Test registration without password."""
        response = client.post('/api/register', json={
            'email': 'user@example.com',
            'tier': 'researcher'
        })

        assert response.status_code == 400

    def test_register_empty_body(self, client):
        """Test registration with empty request body."""
        response = client.post('/api/register', json={})

        assert response.status_code == 400


class TestLoginEndpoint:
    """Test POST /api/login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'TestPassword123!'  # From fixture
        })

        assert response.status_code == 200
        data = response.json

        # Check response structure
        assert 'user' in data
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'token_type' in data

        # Check user data
        assert data['user']['email'] == test_user.email
        assert data['user']['id'] == test_user.id

        # Check tokens
        assert len(data['access_token']) > 0
        assert len(data['refresh_token']) > 0

    def test_login_case_insensitive_email(self, client, test_user):
        """Test login with different email case."""
        response = client.post('/api/login', json={
            'email': test_user.email.upper(),
            'password': 'TestPassword123!'
        })

        assert response.status_code == 200

    def test_login_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'WrongPassword123!'
        })

        assert response.status_code == 401
        assert 'invalid' in response.json['error'].lower()

    def test_login_nonexistent_email(self, client):
        """Test login with non-existent email."""
        response = client.post('/api/login', json={
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!'
        })

        assert response.status_code == 401
        assert 'invalid' in response.json['error'].lower()

    def test_login_missing_email(self, client):
        """Test login without email."""
        response = client.post('/api/login', json={
            'password': 'TestPassword123!'
        })

        assert response.status_code == 400

    def test_login_missing_password(self, client):
        """Test login without password."""
        response = client.post('/api/login', json={
            'email': 'test@example.com'
        })

        assert response.status_code == 400

    def test_login_empty_body(self, client):
        """Test login with empty request body."""
        response = client.post('/api/login', json={})

        assert response.status_code == 400


class TestRefreshEndpoint:
    """Test POST /api/refresh endpoint."""

    def test_refresh_success(self, client, test_user, app):
        """Test successful token refresh."""
        # Login first to get refresh token
        login_response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'TestPassword123!'
        })

        refresh_token = login_response.json['refresh_token']

        # Refresh access token
        response = client.post('/api/refresh', json={
            'refresh_token': refresh_token
        })

        assert response.status_code == 200
        data = response.json

        assert 'access_token' in data
        assert 'token_type' in data
        assert len(data['access_token']) > 0

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post('/api/refresh', json={
            'refresh_token': 'invalid.token.here'
        })

        assert response.status_code == 401

    def test_refresh_access_token_as_refresh(self, client, test_user, app):
        """Test that access token cannot be used for refresh."""
        # Login to get access token
        login_response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'TestPassword123!'
        })

        access_token = login_response.json['access_token']

        # Try to use access token for refresh
        response = client.post('/api/refresh', json={
            'refresh_token': access_token
        })

        assert response.status_code == 401
        assert 'type' in response.json['error'].lower()

    def test_refresh_missing_token(self, client):
        """Test refresh without token."""
        response = client.post('/api/refresh', json={})

        assert response.status_code == 400


class TestLogoutEndpoint:
    """Test POST /api/logout endpoint."""

    def test_logout_success(self, client, test_user, app):
        """Test successful logout."""
        # Login first
        login_response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'TestPassword123!'
        })

        access_token = login_response.json['access_token']
        refresh_token = login_response.json['refresh_token']

        # Logout
        response = client.post(
            '/api/logout',
            json={'refresh_token': refresh_token},
            headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 200
        assert 'Logged out successfully' in response.json['message']

        # Try to use refresh token (should fail)
        refresh_response = client.post('/api/refresh', json={
            'refresh_token': refresh_token
        })

        assert refresh_response.status_code == 401

    def test_logout_without_auth(self, client):
        """Test logout without authentication."""
        response = client.post('/api/logout', json={
            'refresh_token': 'some.token.here'
        })

        assert response.status_code == 401

    def test_logout_missing_refresh_token(self, client, test_user, app):
        """Test logout without refresh token in body."""
        # Login first
        login_response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'TestPassword123!'
        })

        access_token = login_response.json['access_token']

        # Logout without refresh token
        response = client.post(
            '/api/logout',
            json={},
            headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 400


class TestMeEndpoint:
    """Test GET /api/me endpoint."""

    def test_me_success(self, client, test_user, app):
        """Test getting current user profile."""
        # Login first
        login_response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'TestPassword123!'
        })

        access_token = login_response.json['access_token']

        # Get profile
        response = client.get(
            '/api/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 200
        data = response.json

        assert data['id'] == test_user.id
        assert data['email'] == test_user.email
        assert data['tier'] == test_user.tier
        assert 'created_at' in data

    def test_me_without_auth(self, client):
        """Test getting profile without authentication."""
        response = client.get('/api/me')

        assert response.status_code == 401

    def test_me_invalid_token(self, client):
        """Test getting profile with invalid token."""
        response = client.get(
            '/api/me',
            headers={'Authorization': 'Bearer invalid.token.here'}
        )

        assert response.status_code == 401


class TestAuthenticationFlow:
    """Test complete authentication flows."""

    def test_complete_registration_flow(self, client, app):
        """Test complete flow: register -> use token -> logout."""
        # 1. Register
        register_response = client.post('/api/register', json={
            'email': 'flowtest@example.com',
            'password': 'FlowTest123!',
            'tier': 'researcher'
        })

        assert register_response.status_code == 201
        access_token = register_response.json['access_token']
        refresh_token = register_response.json['refresh_token']

        # 2. Use access token to get profile
        me_response = client.get(
            '/api/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        assert me_response.status_code == 200
        assert me_response.json['email'] == 'flowtest@example.com'

        # 3. Logout
        logout_response = client.post(
            '/api/logout',
            json={'refresh_token': refresh_token},
            headers={'Authorization': f'Bearer {access_token}'}
        )

        assert logout_response.status_code == 200

    def test_complete_login_refresh_flow(self, client, test_user, app):
        """Test complete flow: login -> refresh -> use new token."""
        # 1. Login
        login_response = client.post('/api/login', json={
            'email': test_user.email,
            'password': 'TestPassword123!'
        })

        assert login_response.status_code == 200
        refresh_token = login_response.json['refresh_token']

        # 2. Refresh access token
        refresh_response = client.post('/api/refresh', json={
            'refresh_token': refresh_token
        })

        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json['access_token']

        # 3. Use new access token
        me_response = client.get(
            '/api/me',
            headers={'Authorization': f'Bearer {new_access_token}'}
        )

        assert me_response.status_code == 200
        assert me_response.json['email'] == test_user.email
