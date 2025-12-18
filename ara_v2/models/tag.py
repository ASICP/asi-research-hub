"""
Tag models for ARA v2.
Handles tags, paper-tag associations, and tag combinations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL, UniqueConstraint, ARRAY
from sqlalchemy.orm import relationship
from ara_v2.utils.database import db


class Tag(db.Model):
    """Tag model for categorizing papers."""

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    frequency = Column(Integer, default=0, nullable=False)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    growth_rate = Column(DECIMAL(5, 4), default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    papers = relationship('PaperTag', back_populates='tag')

    def __repr__(self):
        return f'<Tag {self.name}>'

    def to_dict(self):
        """Convert tag to dictionary (for API responses)."""
        return {
            'id': self.id,
            'name': self.name,
            'frequency': self.frequency,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'growth_rate': float(self.growth_rate) if self.growth_rate else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def increment_frequency(self):
        """Increment tag frequency and update statistics."""
        self.frequency += 1
        self.last_seen = datetime.utcnow()

        if not self.first_seen:
            self.first_seen = datetime.utcnow()

        # Calculate growth rate (papers per month)
        if self.first_seen:
            months = max(1, (datetime.utcnow() - self.first_seen).days / 30)
            self.growth_rate = self.frequency / months


class TagCombo(db.Model):
    """Track novel tag combinations."""

    __tablename__ = 'tag_combos'

    id = Column(Integer, primary_key=True)
    tag_ids = Column(ARRAY(Integer), nullable=False)
    frequency = Column(Integer, default=1, nullable=False)
    first_paper_id = Column(Integer, ForeignKey('papers.id'))
    is_novel = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('tag_ids', name='uq_tag_combo_ids'),
    )

    def __repr__(self):
        return f'<TagCombo {self.tag_ids}>'

    def to_dict(self):
        """Convert tag combo to dictionary."""
        return {
            'id': self.id,
            'tag_ids': self.tag_ids,
            'frequency': self.frequency,
            'first_paper_id': self.first_paper_id,
            'is_novel': self.is_novel,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def normalize_tag_ids(tag_ids):
        """Ensure tag IDs are sorted for consistent storage."""
        return sorted(tag_ids)
