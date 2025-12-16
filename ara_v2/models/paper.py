"""
Paper model for ARA v2.
Stores research papers with metadata and scores.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, CheckConstraint, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from ara_v2.utils.database import db


class Paper(db.Model):
    """Research paper with metadata and Holmes scores."""

    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True)

    # Paper metadata
    title = Column(Text, nullable=False)
    authors = Column(Text)
    abstract = Column(Text)
    year = Column(Integer)

    # Source information
    source = Column(
        String(50),
        nullable=False,
        index=True
    )
    source_id = Column(String(255))
    pdf_url = Column(Text)

    # Scores (NULL until calculated)
    tag_score = Column(DECIMAL(5, 2))
    citation_score = Column(DECIMAL(5, 2))
    novelty_score = Column(DECIMAL(5, 2))
    holmes_score = Column(DECIMAL(5, 2))

    # Diamond flag (top 0-2% novelty)
    is_diamond = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    scored_at = Column(DateTime)
    deleted_at = Column(DateTime)  # Soft delete support

    # Relationships
    tags = relationship('PaperTag', back_populates='paper', cascade='all, delete-orphan')
    bookmarks = relationship('Bookmark', back_populates='paper', cascade='all, delete-orphan')
    citations_as_citing = relationship(
        'Citation',
        foreign_keys='Citation.citing_paper_id',
        back_populates='citing_paper',
        cascade='all, delete-orphan'
    )
    citations_as_cited = relationship(
        'Citation',
        foreign_keys='Citation.cited_paper_id',
        back_populates='cited_paper',
        cascade='all, delete-orphan'
    )
    novelty_evaluations = relationship('NoveltyEval', back_populates='paper', cascade='all, delete-orphan')
    activities = relationship('UserActivity', back_populates='paper')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "source IN ('google_scholar', 'crossref', 'semantic_scholar', 'arxiv', 'internal')",
            name='check_paper_source'
        ),
        UniqueConstraint('source', 'source_id', name='uq_paper_source_id'),
    )

    def __repr__(self):
        return f'<Paper {self.id}: {self.title[:50]}...>'

    def to_dict(self, include_tags=False, include_scores=True):
        """Convert paper to dictionary (for API responses)."""
        data = {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'year': self.year,
            'source': self.source,
            'source_id': self.source_id,
            'pdf_url': self.pdf_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_scores:
            data['scores'] = {
                'tag_score': float(self.tag_score) if self.tag_score else None,
                'citation_score': float(self.citation_score) if self.citation_score else None,
                'novelty_score': float(self.novelty_score) if self.novelty_score else None,
                'holmes_score': float(self.holmes_score) if self.holmes_score else None,
            }
            data['is_diamond'] = self.is_diamond
            data['scored_at'] = self.scored_at.isoformat() if self.scored_at else None

        if include_tags:
            data['tags'] = [pt.tag.name for pt in self.tags]

        return data

    def is_scored(self):
        """Check if paper has been scored."""
        return self.scored_at is not None

    def is_deleted(self):
        """Check if paper is soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self):
        """Soft delete the paper."""
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted paper."""
        self.deleted_at = None
