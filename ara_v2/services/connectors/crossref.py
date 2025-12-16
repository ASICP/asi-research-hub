"""
CrossRef API connector.
Provides access to DOI metadata, citations, and publication information.
API Docs: https://api.crossref.org/
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from flask import current_app


class CrossRefConnector:
    """
    Connector for CrossRef REST API.

    Free API with no authentication required.
    Polite usage recommended: add email to get better service.
    Rate limit: 50 requests/second (polite users get priority).
    """

    BASE_URL = "https://api.crossref.org"
    TIMEOUT = 30  # seconds

    def __init__(self, mailto_email: Optional[str] = None):
        """
        Initialize CrossRef connector.

        Args:
            mailto_email: Contact email for polite API usage (gets priority in queue)
        """
        self.mailto_email = mailto_email
        self.session = requests.Session()

        # Set user agent (required for polite usage)
        user_agent = 'ARA-v2-Research-Discovery-Engine/2.0'
        if mailto_email:
            user_agent += f' (mailto:{mailto_email})'

        self.session.headers.update({
            'User-Agent': user_agent
        })

    def search_papers(
        self,
        query: str,
        rows: int = 10,
        offset: int = 0,
        filter_params: Optional[Dict[str, str]] = None,
        sort: str = 'relevance'
    ) -> Dict[str, Any]:
        """
        Search for works by query.

        Args:
            query: Search query string
            rows: Number of results per page (max: 1000)
            offset: Offset for pagination
            filter_params: Dictionary of filters (e.g., {'type': 'journal-article'})
            sort: Sort order ('relevance', 'score', 'updated', 'deposited', etc.)

        Returns:
            dict: {
                'total': int,
                'papers': List[dict]
            }

        Example filters:
            - {'type': 'journal-article'}
            - {'from-pub-date': '2020', 'until-pub-date': '2023'}
            - {'has-abstract': 'true'}
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        params = {
            'query': query.strip(),
            'rows': min(rows, 1000),  # API max is 1000
            'offset': offset,
            'sort': sort
        }

        # Add filters if provided
        if filter_params:
            filter_str = ','.join([f'{k}:{v}' for k, v in filter_params.items()])
            params['filter'] = filter_str

        try:
            response = self.session.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=self.TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            message = data.get('message', {})
            total_results = message.get('total-results', 0)
            items = message.get('items', [])

            return {
                'total': total_results,
                'papers': [self._normalize_paper(item) for item in items]
            }

        except requests.exceptions.Timeout:
            current_app.logger.error(f"CrossRef search timeout: {query}")
            raise Exception("Search request timed out")
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"CrossRef search error: {e}")
            raise Exception(f"Search request failed: {str(e)}")

    def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a paper by DOI.

        Args:
            doi: Digital Object Identifier (e.g., '10.1000/xyz123')

        Returns:
            dict: Normalized paper data or None if not found
        """
        if not doi:
            raise ValueError("DOI cannot be empty")

        # Clean DOI (remove any URL prefix)
        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').strip()

        try:
            response = self.session.get(
                f"{self.BASE_URL}/works/{clean_doi}",
                timeout=self.TIMEOUT
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            return self._normalize_paper(data.get('message', {}))

        except requests.exceptions.Timeout:
            current_app.logger.error(f"CrossRef get_paper timeout: {doi}")
            raise Exception("Get paper request timed out")
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"CrossRef get_paper error: {e}")
            raise Exception(f"Get paper request failed: {str(e)}")

    def search_by_title(
        self,
        title: str,
        rows: int = 10
    ) -> Dict[str, Any]:
        """
        Search for papers by title.

        Args:
            title: Paper title
            rows: Number of results

        Returns:
            dict: Search results
        """
        # Use bibliographic query for better title matching
        params = {
            'query.bibliographic': title.strip(),
            'rows': rows
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=self.TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            message = data.get('message', {})
            items = message.get('items', [])

            return {
                'total': message.get('total-results', 0),
                'papers': [self._normalize_paper(item) for item in items]
            }

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"CrossRef title search error: {e}")
            raise Exception(f"Title search failed: {str(e)}")

    def search_ai_safety_papers(
        self,
        rows: int = 50,
        offset: int = 0,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to search for AI safety and alignment papers.

        Args:
            rows: Number of results
            offset: Offset for pagination
            year_from: Filter from this year
            year_to: Filter until this year

        Returns:
            dict: Search results
        """
        query = (
            'AI safety OR artificial intelligence safety OR AI alignment OR '
            'interpretability OR explainability OR adversarial robustness OR '
            'machine learning safety OR AI ethics OR beneficial AI'
        )

        filters = {}
        if year_from:
            filters['from-pub-date'] = str(year_from)
        if year_to:
            filters['until-pub-date'] = str(year_to)

        # Prefer works with abstracts
        filters['has-abstract'] = 'true'

        return self.search_papers(query, rows, offset, filters)

    def _normalize_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize CrossRef work to common format.

        Args:
            item: CrossRef work item

        Returns:
            dict: Normalized paper data matching our Paper model
        """
        # Extract DOI
        doi = item.get('DOI', '')

        # Extract title (usually a list with one element)
        title_list = item.get('title', [])
        title = title_list[0] if title_list else ''

        # Extract abstract if available
        abstract = item.get('abstract')

        # Extract authors
        authors = []
        for author in item.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)

        # Parse publication date
        pub_date = item.get('published', {}) or item.get('published-print', {}) or item.get('published-online', {})
        date_parts = pub_date.get('date-parts', [[]])[0]

        year = None
        published_date = None

        if date_parts:
            year = date_parts[0] if len(date_parts) > 0 else None

            # Try to construct full date
            try:
                if len(date_parts) >= 3:
                    published_date = datetime(date_parts[0], date_parts[1], date_parts[2]).date()
                elif len(date_parts) >= 2:
                    published_date = datetime(date_parts[0], date_parts[1], 1).date()
                elif len(date_parts) >= 1:
                    published_date = datetime(date_parts[0], 1, 1).date()
            except (ValueError, TypeError):
                pass

        # Extract venue information
        venue_parts = []
        container_title = item.get('container-title', [])
        if container_title:
            venue_parts.append(container_title[0])

        publisher = item.get('publisher')
        if publisher and publisher not in venue_parts:
            venue_parts.append(publisher)

        venue = ' - '.join(venue_parts) if venue_parts else None

        # Extract citation count if available (CrossRef doesn't always provide this)
        citation_count = item.get('is-referenced-by-count', 0) or 0

        # Extract subjects/fields
        subjects = item.get('subject', []) or []

        # Get URL
        url = item.get('URL', f'https://doi.org/{doi}' if doi else '')

        # Extract article type
        article_type = item.get('type', '')

        # Get reference count
        reference_count = item.get('reference-count', 0)

        return {
            'source': 'crossref',
            'source_id': doi,
            'doi': doi,
            'title': title.strip() if title else '',
            'abstract': abstract.strip() if abstract else None,
            'authors': authors,
            'year': year,
            'published_date': published_date,
            'venue': venue,
            'publisher': item.get('publisher'),
            'citation_count': citation_count,
            'reference_count': reference_count,
            'type': article_type,
            'subjects': subjects,
            'fields_of_study': subjects,  # Use subjects as fields
            'url': url,
            'issn': item.get('ISSN', []),
            'isbn': item.get('ISBN', []),
            'raw_data': item  # Store full response for reference
        }

    @staticmethod
    def build_filter(
        work_type: Optional[str] = None,
        has_abstract: bool = False,
        has_references: bool = False,
        has_full_text: bool = False,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Helper to build filter parameters for CrossRef API.

        Args:
            work_type: Type of work (e.g., 'journal-article', 'proceedings-article')
            has_abstract: Only works with abstracts
            has_references: Only works with references
            has_full_text: Only works with full text links
            year_from: From publication year
            year_to: Until publication year

        Returns:
            dict: Filter parameters

        Example types:
            - journal-article
            - proceedings-article
            - book-chapter
            - posted-content (preprints)
        """
        filters = {}

        if work_type:
            filters['type'] = work_type
        if has_abstract:
            filters['has-abstract'] = 'true'
        if has_references:
            filters['has-references'] = 'true'
        if has_full_text:
            filters['has-full-text'] = 'true'
        if year_from:
            filters['from-pub-date'] = str(year_from)
        if year_to:
            filters['until-pub-date'] = str(year_to)

        return filters
