"""
Novelty Evaluation model for ARA v2.
Stores Claude API evaluations of paper novelty.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, CheckConstraint
from sqlalchemy.orm import relationship
from ara_v2.utils.database import db


class NoveltyEval(db.Model):
    """Claude API evaluation of paper novelty."""

    __tablename__ = 'novelty_evals'

    id = Column(Integer, primary_key=True)
    paper_id = Column(
        Integer,
        ForeignKey('papers.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Claude API interaction
    prompt_sent = Column(Text, nullable=False)
    claude_response = Column(Text)

    # Evaluation results
    novelty_verdict = Column(String(20))
    confidence = Column(DECIMAL(3, 2))

    # Cost tracking
    api_cost = Column(DECIMAL(8, 6))  # Track actual cost of API call

    # Timestamp
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    paper = relationship('Paper', back_populates='novelty_evaluations')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "novelty_verdict IN ('highly_novel', 'moderately_novel', 'incremental', 'derivative')",
            name='check_novelty_verdict'
        ),
    )

    def __repr__(self):
        return f'<NoveltyEval paper_id={self.paper_id} verdict={self.novelty_verdict}>'

    def to_dict(self):
        """Convert novelty evaluation to dictionary."""
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'novelty_verdict': self.novelty_verdict,
            'confidence': float(self.confidence) if self.confidence else None,
            'api_cost': float(self.api_cost) if self.api_cost else None,
            'evaluated_at': self.evaluated_at.isoformat() if self.evaluated_at else None,
        }
