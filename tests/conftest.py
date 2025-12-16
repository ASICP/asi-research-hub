"""
Pytest configuration and shared fixtures.
"""

import pytest
import os
from ara_v2.app import create_app
from ara_v2.utils.database import db as _db
from ara_v2.models.user import User
from ara_v2.utils.password import hash_password
from ara_v2.utils.redis_client import redis_client


@pytest.fixture(scope='session')
def app():
    """
    Create and configure a Flask application for testing.

    Scope: session - created once per test session
    """
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://localhost:5432/ara_v2_test'
    )
    os.environ['REDIS_URL'] = os.getenv(
        'TEST_REDIS_URL',
        'redis://localhost:6379/1'  # Use database 1 for testing
    )

    # Create app with testing config
    app = create_app('testing')

    # Establish application context
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db(app):
    """
    Create a clean database for each test.

    Scope: function - new database for each test
    """
    with app.app_context():
        # Create all tables
        _db.create_all()

        yield _db

        # Cleanup
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """
    Create a test client for making requests.

    Scope: function - new client for each test
    """
    return app.test_client()


@pytest.fixture(scope='function')
def redis_client_fixture(app):
    """
    Provide Redis client and clean up after test.

    Scope: function - clean Redis for each test
    """
    with app.app_context():
        # Flush test database before test
        redis_client.flushdb()

        yield redis_client

        # Flush test database after test
        redis_client.flushdb()


# Alias for clearer test code
@pytest.fixture(scope='function')
def redis_client(redis_client_fixture):
    """Alias for redis_client_fixture."""
    return redis_client_fixture


@pytest.fixture(scope='function')
def test_user(db):
    """
    Create a test user.

    Returns:
        User: Test user with known credentials
    """
    user = User(
        email='test@example.com',
        password_hash=hash_password('TestPassword123!'),
        tier='researcher'
    )

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture(scope='function')
def student_user(db):
    """
    Create a student tier user.

    Returns:
        User: Student tier user
    """
    user = User(
        email='student@example.com',
        password_hash=hash_password('StudentPass123!'),
        tier='student'
    )

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture(scope='function')
def institutional_user(db):
    """
    Create an institutional tier user.

    Returns:
        User: Institutional tier user
    """
    user = User(
        email='institution@example.com',
        password_hash=hash_password('InstitutionPass123!'),
        tier='institutional'
    )

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture(scope='function')
def multiple_users(db):
    """
    Create multiple test users.

    Returns:
        list[User]: List of test users
    """
    users = [
        User(
            email=f'user{i}@example.com',
            password_hash=hash_password(f'Password{i}123!'),
            tier='researcher'
        )
        for i in range(1, 6)
    ]

    db.session.add_all(users)
    db.session.commit()

    return users


@pytest.fixture
def runner(app):
    """
    Create a CLI test runner.

    Returns:
        FlaskCliRunner: CLI test runner
    """
    return app.test_cli_runner()


# Cleanup fixtures
@pytest.fixture(autouse=True, scope='function')
def cleanup_g():
    """
    Clean up Flask g object after each test.

    autouse=True means this runs automatically for every test
    """
    from flask import g
    yield
    # Clear g after test
    g.__dict__.clear()
