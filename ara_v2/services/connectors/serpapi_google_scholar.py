"""
SerpAPI Google Scholar connector.
Provides access to Google Scholar via SerpAPI's managed service.
Handles proxy rotation, anti-scraping, and IP management automatically.
API Docs: https://serpapi.com/google-scholar-api
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from flask import current_app


class SerpAPIGoogleScholarConnector:
    """
    Connector for Google Scholar via SerpAPI.

    SerpAPI handles all anti-scraping measures, proxy rotation, and CAPTCHA
    solving automatically. Requires API key from https://serpapi.com/
    """

    BASE_URL = "https://serpapi.com/search"
    TIMEOUT = 30  # seconds

    def __init__(self, api_key: str):
        """
        Initialize SerpAPI Google Scholar connector.

        Args:
            api_key: SerpAPI API key (required) - get from https://serpapi.com/

        Raises:
            ValueError: If api_key is not provided
        """
        if not api_key or not api_key.strip():
            raise ValueError("SerpAPI API key is required. Get one at https://serpapi.com/")

        self.api_key = api_key
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'User-Agent': 'ARA-v2-Research-Discovery-Engine/2.0',
        })

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        start: int = 0,
        year_low: Optional[int] = None,
        year_high: Optional[int] = None,
        sort_by: str = "relevance"
    ) -> Dict[str, Any]:
        """
        Search Google Scholar for papers.

        Args:
            query: Search query string
            limit: Maximum number of results (default: 10, max: 20 per request)
            start: Starting position for pagination (default: 0)
            year_low: Filter papers from this year onwards
            year_high: Filter papers up to this year
            sort_by: Sort order - 'relevance' or 'date' (default: 'relevance')

        Returns:
            dict: {
                'total': int (estimated),
                'papers': List[dict],
                'next_start': int (for pagination)
            }

        Raises:
            Exception: If API request fails
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        # Limit to max 20 per request (SerpAPI Google Scholar limit)
        limit = min(limit, 20)

        # Build query parameters
        params = {
            'engine': 'google_scholar',
            'q': query,
            'api_key': self.api_key,
            'num': limit,
            'start': start,
        }

        # Add year range filter if provided
        if year_low or year_high:
            year_filter = ""
            if year_low:
                year_filter = f"{year_low}"
            if year_high:
                if year_filter:
                    year_filter += f"-{year_high}"
                else:
                    year_filter = f"-{year_high}"
            params['as_ylo'] = year_low if year_low else ""
            params['as_yhi'] = year_high if year_high else ""

        # Sort order
        if sort_by == 'date':
            params['scisbd'] = 1  # Sort by date (newest first)

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            # Parse response
            papers = []
            organic_results = data.get('organic_results', [])

            for result in organic_results:
                paper = self._parse_paper(result)
                if paper:
                    papers.append(paper)

            # Estimate total results
            search_info = data.get('search_information', {})
            total = search_info.get('total_results', len(papers))

            # Calculate next pagination start
            next_start = start + len(papers) if len(papers) == limit else None

            return {
                'total': total,
                'papers': papers,
                'next_start': next_start,
                'search_metadata': {
                    'status': data.get('search_metadata', {}).get('status'),
                    'query': query,
                    'total_time': data.get('search_metadata', {}).get('total_time_taken')
                }
            }

        except requests.exceptions.Timeout:
            raise Exception(f"SerpAPI request timed out after {self.TIMEOUT} seconds")
        except requests.exceptions.RequestException as e:
            raise Exception(f"SerpAPI request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error parsing SerpAPI response: {str(e)}")

    def _parse_paper(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single paper from SerpAPI Google Scholar result.

        Args:
            result: Raw result from SerpAPI organic_results

        Returns:
            Normalized paper dictionary or None if parsing fails
        """
        try:
            # Extract publication info
            pub_info = result.get('publication_info', {})

            # Extract authors
            authors = []
            if 'authors' in pub_info:
                for author in pub_info['authors']:
                    if isinstance(author, dict):
                        authors.append(author.get('name', ''))
                    else:
                        authors.append(str(author))

            # Extract year
            year = None
            summary = pub_info.get('summary', '')
            if summary:
                # Try to extract year from summary (e.g., "A Smith - 2023 - Nature")
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', summary)
                if year_match:
                    year = int(year_match.group(0))

            # Extract citation count
            inline_links = result.get('inline_links', {})
            cited_by = inline_links.get('cited_by', {})
            citation_count = cited_by.get('total', 0)

            # Build normalized paper object
            paper = {
                'title': result.get('title', 'N/A'),
                'authors': ', '.join(authors) if authors else 'Unknown',
                'year': year if year else None,
                'abstract': result.get('snippet', ''),
                'url': result.get('link', ''),
                'source': 'Google Scholar',
                'source_id': result.get('result_id', ''),
                'citation_count': citation_count,
                'pdf_url': result.get('resources', [{}])[0].get('link') if result.get('resources') else None,
                'related_pages_link': result.get('inline_links', {}).get('related_pages_link'),
                'versions': result.get('inline_links', {}).get('versions', {}).get('total', 0),
                'raw_data': result  # Keep original for debugging
            }

            return paper

        except Exception as e:
            current_app.logger.warning(f"Failed to parse SerpAPI paper result: {e}")
            return None

    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper.

        Note: SerpAPI Google Scholar doesn't have a direct "get by ID" endpoint.
        This method searches for the paper by title/ID and returns the first result.

        Args:
            paper_id: Paper identifier (cluster ID or title)

        Returns:
            Paper details dictionary or None if not found
        """
        try:
            result = self.search_papers(query=paper_id, limit=1)
            if result['papers']:
                return result['papers'][0]
            return None
        except Exception as e:
            current_app.logger.error(f"Failed to get paper details for {paper_id}: {e}")
            return None

    def get_author_papers(self, author_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for papers by a specific author.

        Args:
            author_name: Author's name
            limit: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        query = f'author:"{author_name}"'
        result = self.search_papers(query=query, limit=limit)
        return result['papers']

    def search_by_citation(self, citing_paper_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find papers that cite a specific paper.

        Args:
            citing_paper_id: Cluster ID of the paper to find citations for
            limit: Maximum number of results

        Returns:
            List of citing papers
        """
        # Use SerpAPI's cited_by parameter
        params = {
            'engine': 'google_scholar',
            'cites': citing_paper_id,
            'api_key': self.api_key,
            'num': min(limit, 20)
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for result in data.get('organic_results', []):
                paper = self._parse_paper(result)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            current_app.logger.error(f"Failed to get citing papers: {e}")
            return []
