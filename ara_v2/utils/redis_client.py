"""
Redis client utilities for ARA v2.
Manages Redis connection for caching, rate limiting, and session storage.
"""

import redis
from urllib.parse import urlparse


# Global Redis client
redis_client = None


def init_redis(app):
    """
    Initialize Redis client.

    Args:
        app: Flask application instance
    """
    global redis_client

    redis_url = app.config.get('REDIS_URL')

    if not redis_url:
        app.logger.warning("REDIS_URL not configured, Redis features disabled")
        return

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
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # Test connection
        redis_client.ping()

        app.logger.info("Redis initialized successfully")

    except redis.ConnectionError as e:
        app.logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None
    except Exception as e:
        app.logger.error(f"Redis initialization error: {e}")
        redis_client = None


def get_redis():
    """Get Redis client instance."""
    return redis_client
