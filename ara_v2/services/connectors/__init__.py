"""
External API connectors for research paper sources.
"""

from .semantic_scholar import SemanticScholarConnector
from .arxiv import ArxivConnector
from .crossref import CrossRefConnector
from .serpapi_google_scholar import SerpAPIGoogleScholarConnector

__all__ = [
    'SemanticScholarConnector',
    'ArxivConnector',
    'CrossRefConnector',
    'SerpAPIGoogleScholarConnector'
]
