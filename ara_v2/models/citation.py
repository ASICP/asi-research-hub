"""
Citation model for ARA v2.
Tracks citation relationships between papers.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ara_v2.utils.database import db


class Citation(db.Model):
    """Citation relationship between papers."""

    __tablename__ = 'citations'

    id = Column(Integer, primary_key=True)
    citing_paper_id = Column(
        Integer,
        ForeignKey('papers.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    cited_paper_id = Column(
        Integer,
        ForeignKey('papers.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    source = Column(String(50))  # Where citation data came from
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    citing_paper = relationship('Paper', foreign_keys=[citing_paper_id], back_populates='citations_as_citing')
    cited_paper = relationship('Paper', foreign_keys=[cited_paper_id], back_populates='citations_as_cited')

    # Constraints
    __table_args__ = (
        UniqueConstraint('citing_paper_id', 'cited_paper_id', name='uq_citation'),
    )

    def __repr__(self):
        return f'<Citation {self.citing_paper_id} -> {self.cited_paper_id}>'

    def to_dict(self):
        """Convert citation to dictionary."""
        return {
            'id': self.id,
            'citing_paper_id': self.citing_paper_id,
            'cited_paper_id': self.cited_paper_id,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
