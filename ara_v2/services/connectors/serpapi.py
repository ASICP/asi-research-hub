"""
SerpAPI connector for Google Scholar.
Provides access to Google Scholar search results via SerpAPI.
API Docs: https://serpapi.com/docs
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from flask import current_app
import os


class SerpapiConnector:
    """
    Connector for SerpAPI Google Scholar integration.
    
    Free tier includes 100 searches per month.
    Requires SERPAPI_API_KEY environment variable.
    """

    BASE_URL = "https://serpapi.com/search"
    TIMEOUT = 15  # seconds

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpAPI connector.

        Args:
            api_key: SerpAPI API key (defaults to SERPAPI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable not set")
        
        self.session = requests.Session()

    def search_papers(
        self,
        query: str,
        max_results: int = 10,
        year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search Google Scholar via SerpAPI.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            year: Filter by publication year (optional, e.g., "2023" or "2020-2023")

        Returns:
            dict: {
                'total': int (approximate),
                'papers': List[dict]
            }

        Raises:
            Exception: If API request fails
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        try:
            params = {
                'q': query.strip(),
                'engine': 'google_scholar',
                'api_key': self.api_key,
                'num': min(max_results, 20),  # SerpAPI returns up to 20 per request
                'hl': 'en',
            }

            # Add year filter if provided
            if year:
                params['as_ylo'] = year  # Year low filter for Google Scholar

            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Check for errors
            if data.get('error'):
                error_msg = data.get('error', 'Unknown error')
                current_app.logger.error(f"SerpAPI error: {error_msg}")
                raise Exception(f"SerpAPI search failed: {error_msg}")

            # Extract organic results
            organic_results = data.get('organic_results', [])
            papers = [self._normalize_paper(result) for result in organic_results]

            return {
                'total': data.get('search_metadata', {}).get('google_scholar_results', 0),
                'papers': papers
            }

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"SerpAPI request failed: {str(e)}")
            raise Exception(f"Failed to search Google Scholar via SerpAPI: {str(e)}")

    def _normalize_paper(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize SerpAPI result to standard paper format.

        Args:
            result: Raw result from SerpAPI

        Returns:
            dict: Normalized paper metadata
        """
        # Parse publication date
        year = None
        pub_date_str = result.get('publication_info', {}).get('summary', '')
        if pub_date_str and ' - ' in pub_date_str:
            try:
                year = int(pub_date_str.split(' - ')[-1])
            except (ValueError, IndexError):
                year = None

        # Extract DOI and ArXiv ID if present
        doi = None
        arxiv_id = None
        
        link = result.get('link', '')
        if 'arxiv' in link:
            arxiv_id = link.split('/abs/')[-1].split('v')[0] if '/abs/' in link else None
        
        # DOI might be in the link or title
        if 'doi.org' in link:
            doi = link.split('doi.org/')[-1] if 'doi.org/' in link else None

        return {
            'title': result.get('title', ''),
            'authors': self._extract_authors(result.get('publication_info', {})),
            'abstract': result.get('snippet', ''),
            'year': year,
            'url': link,
            'source': 'google_scholar',
            'arxiv_id': arxiv_id,
            'doi': doi,
            'citations': result.get('inline_links', {}).get('cited_by', {}).get('total', 0),
        }

    @staticmethod
    def _extract_authors(publication_info: Dict[str, Any]) -> str:
        """
        Extract author names from publication info.

        Args:
            publication_info: Publication information dict

        Returns:
            str: Comma-separated author names
        """
        summary = publication_info.get('summary', '')
        
        # Summary format: "Author1, Author2 - Journal, Year"
        if ' - ' in summary:
            authors_part = summary.split(' - ')[0].strip()
            return authors_part
        
        return ''
