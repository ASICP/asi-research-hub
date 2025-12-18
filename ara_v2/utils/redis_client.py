"""
Redis client utilities for ARA v2.
Manages Redis connection for caching, rate limiting, and session storage.
Optional - gracefully degrades if Redis is unavailable.
"""

import os
from urllib.parse import urlparse

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


# Global Redis client
redis_client = None


def init_redis(app):
    """
    Initialize Redis client (optional).

    Args:
        app: Flask application instance
    """
    global redis_client

    if not REDIS_AVAILABLE:
        app.logger.warning("Redis package not installed, Redis features disabled")
        return

    redis_url = app.config.get('REDIS_URL') or os.getenv('REDIS_URL')

    if not redis_url:
        # Try localhost as fallback (development)
        redis_url = "redis://localhost:6379/0"

    try:
        # Parse Redis URL
        url = urlparse(redis_url)

        # Create Redis client
        redis_client = redis.Redis(
            host=url.hostname or 'localhost',
            port=url.port or 6379,
            db=int(url.path[1:]) if url.path and len(url.path) > 1 else 0,
            password=url.password,
            decode_responses=True,  # Automatically decode bytes to strings
            socket_connect_timeout=2,  # Short timeout
            socket_timeout=2
        )

        # Test connection
        redis_client.ping()

        app.logger.info(f"Redis initialized successfully at {url.hostname}:{url.port}")

    except redis.ConnectionError as e:
        app.logger.warning(f"Redis not available: {e}. Continuing without Redis.")
        redis_client = None
    except Exception as e:
        app.logger.warning(f"Redis initialization failed: {e}. Continuing without Redis.")
        redis_client = None


def get_redis():
    """Get Redis client instance (may be None if Redis unavailable)."""
    return redis_client
