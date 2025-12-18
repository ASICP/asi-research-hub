"""
Rate limiting utilities for ARA v2.
Provides Flask-Limiter configuration with Redis backend or memory fallback.
"""

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def get_limiter_storage_uri():
    """
    Get storage URI for rate limiter.

    Returns:
        str: Redis URI if available, otherwise memory://
    """
    redis_url = os.getenv('REDIS_URL')

    if redis_url:
        return redis_url

    # Try localhost Redis (development)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        return "redis://localhost:6379/0"
    except:
        # Fallback to memory (works in single-instance deployments)
        return "memory://"


# Initialize Flask-Limiter with automatic storage detection
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_limiter_storage_uri(),
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
    storage_uri = limiter._storage_uri

    limiter.init_app(app)

    app.logger.info(f"Rate limiter initialized with storage: {storage_uri}")
