"""
User Activity model for ARA v2.
Tracks user actions for analytics and behavioral insights.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from ara_v2.utils.database import db


class UserActivity(db.Model):
    """Track user actions for analytics."""

    __tablename__ = 'user_activity'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    action_type = Column(String(50), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey('papers.id'))
    metadata = Column(JSONB)  # Additional action-specific data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship('User', back_populates='activities')
    paper = relationship('Paper', back_populates='activities')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('search', 'view_paper', 'bookmark', 'unbookmark', "
            "'export_notebooklm', 'view_mindmap', 'adjust_weights')",
            name='check_action_type'
        ),
    )

    def __repr__(self):
        return f'<UserActivity user_id={self.user_id} action={self.action_type}>'

    def to_dict(self):
        """Convert activity to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'paper_id': self.paper_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
