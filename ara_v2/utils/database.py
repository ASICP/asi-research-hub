"""
Database utilities for ARA v2.
Manages SQLAlchemy database connection and session.
"""

from flask_sqlalchemy import SQLAlchemy

# Create database instance
db = SQLAlchemy()


def init_db(app):
    """
    Initialize database with Flask app.

    Args:
        app: Flask application instance
    """
    db.init_app(app)

    with app.app_context():
        # Import models here to avoid circular imports
        import ara_v2.models  # noqa

        # Create tables (only in development)
        if app.debug:
            db.create_all()

    app.logger.info("Database initialized successfully")


def get_db_session():
    """Get current database session."""
    return db.session
