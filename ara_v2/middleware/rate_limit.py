"""
Rate limiting middleware for ARA v2.
Uses Flask-Limiter with Redis backend.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create limiter instance (initialized in app factory)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri=None  # Will be set in app factory
)
