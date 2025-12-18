"""
PaperTag association model for ARA v2.
Links papers to tags with additional metadata.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Boolean, DECIMAL, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from ara_v2.utils.database import db


class PaperTag(db.Model):
    """Association between papers and tags."""

    __tablename__ = 'paper_tags'

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), nullable=False)
    confidence = Column(DECIMAL(3, 2), default=1.0)
    is_novel_combo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    paper = relationship('Paper', back_populates='tags')
    tag = relationship('Tag', back_populates='papers')

    # Constraints
    __table_args__ = (
        UniqueConstraint('paper_id', 'tag_id', name='uq_paper_tag'),
    )

    def __repr__(self):
        return f'<PaperTag paper_id={self.paper_id} tag_id={self.tag_id}>'
