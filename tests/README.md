# ARA v2 Tests

Comprehensive test suite for ARA v2 authentication system.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_password.py     # Password validation and hashing
│   ├── test_jwt_auth.py     # JWT token creation and verification
│   ├── test_auth_middleware.py  # Authentication decorators
│   └── test_auth_endpoints.py   # API endpoint integration tests
└── integration/             # Integration tests (slower, with dependencies)
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=ara_v2 --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_password.py
```

### Run specific test class
```bash
pytest tests/unit/test_password.py::TestPasswordValidation
```

### Run specific test
```bash
pytest tests/unit/test_password.py::TestPasswordValidation::test_valid_password
```

### Run tests by marker
```bash
# Run only authentication tests
pytest -m auth

# Run only unit tests
pytest -m unit

# Run database tests
pytest -m db
```

### Run with verbose output
```bash
pytest -v
pytest -vv  # Extra verbose
```

## Test Markers

Tests can be marked with the following markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests with external dependencies
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.auth` - Authentication related tests
- `@pytest.mark.db` - Database related tests
- `@pytest.mark.redis` - Redis related tests
- `@pytest.mark.api` - API endpoint tests

## Prerequisites

### 1. Install test dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up test database (optional)
By default, tests use in-memory SQLite. For PostgreSQL:

```bash
# Create test database
createdb ara_v2_test

# Set environment variable
export TEST_DATABASE_URL=postgresql://localhost:5432/ara_v2_test
```

### 3. Ensure Redis is running
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest

# Verify
redis-cli ping  # Should return PONG
```

## Test Coverage

Current coverage (Week 2 - Authentication):

- ✅ Password utilities (validation, hashing)
- ✅ JWT utilities (token creation, verification, revocation)
- ✅ Authentication middleware (decorators)
- ✅ Authentication endpoints (register, login, refresh, logout, me)

Target: 80%+ code coverage

## Writing New Tests

### Example unit test:
```python
import pytest
from ara_v2.utils.password import validate_password

def test_password_validation():
    """Test password validation."""
    is_valid, message = validate_password("SecurePass123!")
    assert is_valid is True
```

### Example integration test:
```python
def test_register_endpoint(client):
    """Test user registration."""
    response = client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'tier': 'researcher'
    })

    assert response.status_code == 201
    assert 'access_token' in response.json
```

### Using fixtures:
```python
def test_with_user(test_user, client):
    """Test using the test_user fixture."""
    # test_user is already created and saved to database
    assert test_user.email == 'test@example.com'
```

## Available Fixtures

From `conftest.py`:

- `app` - Flask application instance
- `db` - Database session (cleaned between tests)
- `client` - Test client for API requests
- `redis_client` - Redis client (cleaned between tests)
- `test_user` - Standard test user
- `student_user` - Student tier user
- `institutional_user` - Institutional tier user
- `multiple_users` - List of 5 test users

## Continuous Integration

Tests should pass before merging:

```bash
# Run full test suite with coverage
pytest --cov=ara_v2 --cov-report=term-missing --cov-fail-under=80

# Run with strict mode
pytest --strict-markers
```

## Troubleshooting

### Database connection errors
```bash
# Check PostgreSQL is running
pg_isready

# Reset test database
dropdb ara_v2_test
createdb ara_v2_test
```

### Redis connection errors
```bash
# Check Redis is running
redis-cli ping

# Check Redis is on correct port
redis-cli -p 6379 ping
```

### Import errors
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Fixture not found
Ensure `conftest.py` is in the tests directory and properly configured.

## Next Steps

Week 3 tests (upcoming):
- Paper search and retrieval
- Tag assignment
- External API connectors

Week 4 tests (upcoming):
- Bookmarks CRUD
- Full integration testing
- Performance testing
