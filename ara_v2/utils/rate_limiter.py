"""
Rate limiting utilities for ARA v2.
Provides Flask-Limiter configuration with Redis backend.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from ara_v2.utils.redis_client import get_redis


def get_limiter_storage_uri():
    """
    Get Redis URI for rate limiter storage.

    Returns:
        str: Redis URI or None if Redis unavailable
    """
    redis_client = get_redis()
    if redis_client:
        # Flask-Limiter expects redis:// URI format
        return redis_client.connection_pool.connection_kwargs.get('host', 'localhost')
    return None


# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/0",  # Default, will be overridden by app config
    default_limits=["1000 per day", "100 per hour"],  # Global limits
    strategy="fixed-window",
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)


def init_limiter(app):
    """
    Initialize rate limiter with Flask app.

    Args:
        app: Flask application instance
    """
    # Use Redis URI from app config if available
    storage_uri = app.config.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/0')

    limiter.init_app(app)

    app.logger.info(f"Rate limiter initialized with storage: {storage_uri}")
