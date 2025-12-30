"""
Paper model for ARA v2.
Stores research papers with metadata matching the production database schema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from ara_v2.utils.database import db


class Paper(db.Model):
    """Research paper with metadata from internal database."""

    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True)

    # Paper metadata
    title = Column(Text, nullable=False)
    authors = Column(Text)
    abstract = Column(Text)
    year = Column(Integer)
    venue = Column(Text)  # Journal, conference, or publication venue
    source = Column(String(50), nullable=False, index=True)

    # Identifiers
    doi = Column(String(255))
    arxiv_id = Column(String(100))
    source_id = Column(String(255))  # External ID (e.g., S2 ID, Google Scholar ID)

    # Content storage
    pdf_path = Column(String(255))
    pdf_text = Column(Text)  # Full-text searchable PDF content
    url = Column(String(500))  # External URL to paper (for public links)

    # Metadata
    citation_count = Column(Integer, default=0)
    asip_funded = Column(Boolean, default=False)
    added_by = Column(String(255))
    tags = Column(Text)  # JSON array of tag strings
    raw_data = Column(JSONB)  # Source-specific metadata (categories, fieldsOfStudy, subjects, etc.)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tags_relationship = db.relationship('PaperTag', back_populates='paper', lazy='dynamic')

    def __repr__(self):
        return f'<Paper {self.id}: {self.title[:50]}...>'

    def to_dict(self):
        """Convert paper to dictionary (for API responses)."""
        import json
        tags_list = []
        if self.tags:
            try:
                tags_list = json.loads(self.tags)
            except (json.JSONDecodeError, TypeError):
                tags_list = []
        
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'year': self.year,
            'source': self.source,
            'source_id': self.source_id,
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'pdf_path': self.pdf_path,
            'url': self.url,
            'citation_count': self.citation_count,
            'asip_funded': self.asip_funded,
            'tags': tags_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
