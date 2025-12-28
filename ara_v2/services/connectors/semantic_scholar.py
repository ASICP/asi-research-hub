"""
Semantic Scholar API connector.
Provides access to academic papers, citations, and metadata.
API Docs: https://api.semanticscholar.org/
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from flask import current_app


class SemanticScholarConnector:
    """
    Connector for Semantic Scholar Academic Graph API.

    Free API with generous rate limits (100 requests/5 minutes for search,
    10 requests/second for paper details).
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    SEARCH_TIMEOUT = 30  # seconds
    DETAIL_TIMEOUT = 10  # seconds

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Scholar connector.

        Args:
            api_key: Optional API key for higher rate limits (not required)
        """
        self.api_key = api_key
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'User-Agent': 'ARA-v2-Research-Discovery-Engine/2.0',
        })

        # Add API key if provided (not required but gives better rate limits)
        if api_key:
            self.session.headers.update({
                'x-api-key': api_key
            })

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        year: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for papers by keyword.

        Args:
            query: Search query string
            limit: Maximum number of results (default: 10, max: 100)
            offset: Offset for pagination (default: 0)
            year: Filter by publication year (e.g., "2023" or "2020-2023")
            fields: List of fields to return (defaults to common fields)

        Returns:
            dict: {
                'total': int,
                'offset': int,
                'papers': List[dict]
            }

        Raises:
            Exception: If API request fails
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        # Default fields to retrieve
        if fields is None:
            fields = [
                'paperId',
                'externalIds',
                'title',
                'abstract',
                'year',
                'authors',
                'venue',
                'citationCount',
                'influentialCitationCount',
                'publicationDate',
                'publicationTypes',
                'fieldsOfStudy',
                'url'
            ]

        params = {
            'query': query.strip(),
            'limit': min(limit, 100),  # API max is 100
            'offset': offset,
            'fields': ','.join(fields)
        }

        # Add year filter if provided
        if year:
            params['year'] = year

        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                timeout=self.SEARCH_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            return {
                'total': data.get('total', 0),
                'offset': data.get('offset', 0),
                'papers': [self._normalize_paper(p) for p in data.get('data', [])]
            }

        except requests.exceptions.Timeout:
            current_app.logger.error(f"Semantic Scholar search timeout: {query}")
            raise Exception("Search request timed out")
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Semantic Scholar search error: {e}")
            raise Exception(f"Search request failed: {str(e)}")

    def get_paper(
        self,
        paper_id: str,
        fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper.

        Args:
            paper_id: Semantic Scholar paper ID, DOI, ArXiv ID, or other external ID
            fields: List of fields to return (defaults to comprehensive set)

        Returns:
            dict: Normalized paper data or None if not found

        Raises:
            Exception: If API request fails
        """
        if not paper_id:
            raise ValueError("Paper ID cannot be empty")

        # Default fields for detailed view
        if fields is None:
            fields = [
                'paperId',
                'externalIds',
                'title',
                'abstract',
                'year',
                'authors',
                'venue',
                'citationCount',
                'influentialCitationCount',
                'publicationDate',
                'publicationTypes',
                'fieldsOfStudy',
                'url',
                'citations',
                'references',
                's2FieldsOfStudy'
            ]

        params = {
            'fields': ','.join(fields)
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params=params,
                timeout=self.DETAIL_TIMEOUT
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            return self._normalize_paper(data)

        except requests.exceptions.Timeout:
            current_app.logger.error(f"Semantic Scholar get_paper timeout: {paper_id}")
            raise Exception("Get paper request timed out")
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Semantic Scholar get_paper error: {e}")
            raise Exception(f"Get paper request failed: {str(e)}")

    def get_paper_citations(
        self,
        paper_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper.

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of citations (default: 100, max: 1000)
            offset: Offset for pagination

        Returns:
            list: List of citing papers
        """
        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': 'paperId,title,year,authors,citationCount'
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}/citations",
                params=params,
                timeout=self.DETAIL_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            return [
                self._normalize_paper(item.get('citingPaper', {}))
                for item in data.get('data', [])
            ]

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Get citations error: {e}")
            return []

    def get_paper_references(
        self,
        paper_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper.

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of references (default: 100, max: 1000)
            offset: Offset for pagination

        Returns:
            list: List of referenced papers
        """
        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': 'paperId,title,year,authors,citationCount'
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}/references",
                params=params,
                timeout=self.DETAIL_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            return [
                self._normalize_paper(item.get('citedPaper', {}))
                for item in data.get('data', [])
            ]

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Get references error: {e}")
            return []

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Semantic Scholar paper data to common format.

        Args:
            raw_paper: Raw paper data from API

        Returns:
            dict: Normalized paper data matching our Paper model
        """
        external_ids = raw_paper.get('externalIds', {}) or {}

        # Extract authors
        authors = []
        for author in raw_paper.get('authors', []):
            if isinstance(author, dict):
                authors.append(author.get('name', ''))
            elif isinstance(author, str):
                authors.append(author)

        # Parse publication date
        pub_date = raw_paper.get('publicationDate')
        published_date = None
        if pub_date:
            try:
                published_date = datetime.strptime(pub_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        # Get year
        year = raw_paper.get('year')
        if not year and published_date:
            year = published_date.year

        # Extract fields of study (for tag assignment)
        fields_of_study = raw_paper.get('fieldsOfStudy', []) or []
        s2_fields = raw_paper.get('s2FieldsOfStudy', []) or []

        # Combine all field information
        all_fields = []
        all_fields.extend([f for f in fields_of_study if f])
        all_fields.extend([
            f.get('category') if isinstance(f, dict) else f
            for f in s2_fields if f
        ])

        import uuid
        # Generate consistent source_id from paperId, or create from title+authors if missing
        source_id = raw_paper.get('paperId', '')
        if not source_id or source_id.strip() == '':
            id_seed = f"{raw_paper.get('title', 'unknown')}_{','.join(authors)}"
            source_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id_seed))[:16]
        
        return {
            'source': 'semantic_scholar',
            'source_id': source_id,
            'doi': external_ids.get('DOI'),
            'arxiv_id': external_ids.get('ArXiv'),
            'title': raw_paper.get('title', '').strip(),
            'abstract': raw_paper.get('abstract', '').strip() if raw_paper.get('abstract') else None,
            'authors': authors,
            'year': year,
            'published_date': published_date,
            'venue': raw_paper.get('venue', '').strip() if raw_paper.get('venue') else None,
            'citation_count': raw_paper.get('citationCount', 0) or 0,
            'influential_citation_count': raw_paper.get('influentialCitationCount', 0) or 0,
            'fields_of_study': all_fields,
            'publication_types': raw_paper.get('publicationTypes', []) or [],
            'url': raw_paper.get('url', ''),
            'external_ids': external_ids,
            'raw_data': {
                'fieldsOfStudy': all_fields, # Explicitly put in raw_data for tagger
                **raw_paper
            }  # Store full response for reference
        }

    def search_ai_safety_papers(
        self,
        limit: int = 50,
        year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to search for AI safety and alignment papers.

        Args:
            limit: Maximum number of results
            year: Filter by publication year

        Returns:
            dict: Search results
        """
        # Comprehensive AI safety search query
        query = (
            '(AI safety OR artificial intelligence safety OR AI alignment OR '
            'value alignment OR machine learning safety OR neural network safety OR '
            'interpretability OR explainability OR adversarial examples OR '
            'robustness OR AI governance OR AI policy OR AI ethics OR '
            'beneficial AI OR AI risk OR existential risk OR '
            'mechanistic interpretability OR RLHF OR reinforcement learning human feedback)'
        )

        return self.search_papers(query, limit=limit, year=year)
