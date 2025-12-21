"""
Paper model for ARA v2.
Stores research papers with metadata matching the production database schema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
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
    source = Column(String(50), nullable=False, index=True)

    # Identifiers
    doi = Column(String(255))
    arxiv_id = Column(String(100))

    # Content storage
    pdf_path = Column(String(255))
    pdf_text = Column(Text)  # Full-text searchable PDF content

    # Metadata
    citation_count = Column(Integer, default=0)
    asip_funded = Column(Boolean, default=False)
    added_by = Column(String(255))
    tags = Column(Text)  # JSON array of tag strings
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'pdf_path': self.pdf_path,
            'citation_count': self.citation_count,
            'asip_funded': self.asip_funded,
            'tags': tags_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
