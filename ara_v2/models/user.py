"""
User model for ARA v2.
Handles user accounts and authentication.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from ara_v2.utils.database import db


class User(db.Model):
    """User model for authentication and profile management."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))

    # User tier for analytics
    tier = Column(
        String(20),
        nullable=False,
        default='researcher'
    )

    # Region for analytics
    region = Column(
        String(10),
        nullable=False,
        default='OTHER'
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Privacy settings (stored as JSON in activity tracking)
    # privacy_settings will be checked in activity logging

    # Relationships
    bookmarks = relationship('Bookmark', back_populates='user', cascade='all, delete-orphan')
    activities = relationship('UserActivity', back_populates='user', cascade='all, delete-orphan')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "tier IN ('student', 'researcher', 'institutional')",
            name='check_user_tier'
        ),
        CheckConstraint(
            "region IN ('NA', 'EU', 'ASIA', 'OTHER')",
            name='check_user_region'
        ),
    )

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self, include_email=True):
        """Convert user to dictionary (for API responses)."""
        data = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'tier': self.tier,
            'region': self.region,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
        }

        if include_email:
            data['email'] = self.email

        return data

    def update_last_active(self):
        """Update last active timestamp."""
        self.last_active = datetime.utcnow()
