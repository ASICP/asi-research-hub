"""
Configuration management for ARA v2.
Loads settings from environment variables with sensible defaults.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost:5432/ara_v2'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_TOKEN_EXPIRY = timedelta(
        hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRY_HOURS', 24))
    )
    JWT_REFRESH_TOKEN_EXPIRY = timedelta(
        days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRY_DAYS', 30))
    )

    # Claude API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    CLAUDE_DAILY_BUDGET = float(os.getenv('CLAUDE_DAILY_BUDGET', '5.00'))
    CLAUDE_MONTHLY_BUDGET = float(os.getenv('CLAUDE_MONTHLY_BUDGET', '100.00'))
    CLAUDE_MAX_CALLS_PER_MIN = int(os.getenv('CLAUDE_MAX_CALLS_PER_MIN', '10'))
    CLAUDE_MAX_CALLS_PER_HOUR = int(os.getenv('CLAUDE_MAX_CALLS_PER_HOUR', '200'))

    # External APIs
    SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY', '')
    CROSSREF_EMAIL = os.getenv('CROSSREF_EMAIL', '')

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', REDIS_URL)
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '1000 per day;100 per hour')

    # Security
    FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY', '')

    # Gov Dash
    GOV_DASH_API_KEYS = os.getenv('GOV_DASH_API_KEYS', '').split(',')

    # Application Settings
    MAX_PAPERS_PER_SEARCH = int(os.getenv('MAX_PAPERS_PER_SEARCH', '100'))
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))

    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/2')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/ara_v2.log')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # Monitoring
    ENABLE_PROMETHEUS_METRICS = os.getenv('ENABLE_PROMETHEUS_METRICS', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

    # Stricter security in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True

    # Use test database (can be overridden by TEST_DATABASE_URL env var)
    # Default to in-memory SQLite for fast unit tests
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    )

    # Use separate Redis database for testing
    REDIS_URL = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1')

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Disable rate limiting in tests (can be enabled per-test)
    RATELIMIT_ENABLED = False


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
