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
    
    Uses in-memory storage for Cloud Run compatibility.
    Cloud Run is stateless and cannot run Redis as a background process.

    Returns:
        str: memory:// for stateless Cloud Run deployments
    """
    # Always use in-memory storage for Cloud Run compatibility
    # Redis requires a persistent background process which Cloud Run doesn't support
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
