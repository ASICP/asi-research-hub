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
    
    For Cloud Run deployments, Redis is disabled since Cloud Run
    cannot run background processes like Redis server.

    Args:
        app: Flask application instance
    """
    global redis_client

    # Skip Redis initialization for Cloud Run compatibility
    # Cloud Run is stateless and cannot run Redis as a background process
    redis_url = app.config.get('REDIS_URL') or os.getenv('REDIS_URL')
    
    if not redis_url:
        app.logger.info("Redis disabled (no REDIS_URL configured) - using in-memory alternatives")
        redis_client = None
        return

    if not REDIS_AVAILABLE:
        app.logger.info("Redis package not available - using in-memory alternatives")
        redis_client = None
        return

    try:
        # Parse Redis URL
        url = urlparse(redis_url)

        # Create Redis client with short timeout
        redis_client = redis.Redis(
            host=url.hostname or 'localhost',
            port=url.port or 6379,
            db=int(url.path[1:]) if url.path and len(url.path) > 1 else 0,
            password=url.password,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )

        # Test connection
        redis_client.ping()
        app.logger.info(f"Redis initialized successfully at {url.hostname}:{url.port}")

    except Exception as e:
        app.logger.info(f"Redis not available: {e}. Using in-memory alternatives.")
        redis_client = None


def get_redis():
    """Get Redis client instance (may be None if Redis unavailable)."""
    return redis_client
