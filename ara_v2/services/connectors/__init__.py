"""
External API connectors for research paper sources.
"""

from .semantic_scholar import SemanticScholarConnector
from .arxiv import ArxivConnector
from .crossref import CrossRefConnector

__all__ = [
    'SemanticScholarConnector',
    'ArxivConnector',
    'CrossRefConnector'
]
