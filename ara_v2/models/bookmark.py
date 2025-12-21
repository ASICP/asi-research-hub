"""
Bookmark model for ARA v2.
Allows users to save papers with personal notes.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ara_v2.utils.database import db


class Bookmark(db.Model):
    """User bookmark for a paper with optional notes."""

    __tablename__ = 'bookmarks'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    paper_id = Column(
        Integer,
        ForeignKey('papers.id', ondelete='CASCADE'),
        nullable=False
    )
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship('User', back_populates='bookmarks')
    paper = relationship('Paper')

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'paper_id', name='uq_user_paper_bookmark'),
    )

    def __repr__(self):
        return f'<Bookmark user_id={self.user_id} paper_id={self.paper_id}>'

    def to_dict(self, include_paper=False):
        """Convert bookmark to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'paper_id': self.paper_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_paper and self.paper:
            data['paper'] = self.paper.to_dict(include_tags=True, include_scores=True)

        return data
