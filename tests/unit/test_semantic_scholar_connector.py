"""
Unit tests for Semantic Scholar API connector.
"""

import pytest
from unittest.mock import Mock, patch
from ara_v2.services.connectors.semantic_scholar import SemanticScholarConnector


class TestSemanticScholarConnector:
    """Test Semantic Scholar connector initialization and basic setup."""

    def test_init_without_api_key(self):
        """Test connector initialization without API key."""
        connector = SemanticScholarConnector()

        assert connector.api_key is None
        assert 'x-api-key' not in connector.session.headers

    def test_init_with_api_key(self):
        """Test connector initialization with API key."""
        api_key = "test-api-key-123"
        connector = SemanticScholarConnector(api_key=api_key)

        assert connector.api_key == api_key
        assert connector.session.headers['x-api-key'] == api_key

    def test_user_agent_set(self):
        """Test that user agent is set correctly."""
        connector = SemanticScholarConnector()

        assert 'User-Agent' in connector.session.headers
        assert 'ARA-v2' in connector.session.headers['User-Agent']


class TestSearchPapers:
    """Test paper search functionality."""

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_search_papers_success(self, mock_get):
        """Test successful paper search."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'total': 2,
            'offset': 0,
            'data': [
                {
                    'paperId': 'abc123',
                    'title': 'Test Paper 1',
                    'abstract': 'Abstract 1',
                    'year': 2024,
                    'authors': [{'name': 'Author One'}],
                    'citationCount': 10
                },
                {
                    'paperId': 'def456',
                    'title': 'Test Paper 2',
                    'abstract': 'Abstract 2',
                    'year': 2023,
                    'authors': [{'name': 'Author Two'}],
                    'citationCount': 5
                }
            ]
        }
        mock_get.return_value = mock_response

        connector = SemanticScholarConnector()
        result = connector.search_papers('AI safety', limit=10)

        assert result['total'] == 2
        assert len(result['papers']) == 2
        assert result['papers'][0]['source'] == 'semantic_scholar'
        assert result['papers'][0]['title'] == 'Test Paper 1'
        assert result['papers'][1]['title'] == 'Test Paper 2'

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_search_papers_with_year_filter(self, mock_get):
        """Test paper search with year filter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'total': 1,
            'offset': 0,
            'data': []
        }
        mock_get.return_value = mock_response

        connector = SemanticScholarConnector()
        connector.search_papers('AI safety', limit=10, year='2024')

        # Verify year parameter was passed
        call_args = mock_get.call_args
        assert 'year' in call_args[1]['params']
        assert call_args[1]['params']['year'] == '2024'

    def test_search_papers_empty_query(self):
        """Test that empty query raises error."""
        connector = SemanticScholarConnector()

        with pytest.raises(ValueError) as exc_info:
            connector.search_papers('')

        assert 'cannot be empty' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_search_papers_timeout(self, mock_get):
        """Test handling of request timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        connector = SemanticScholarConnector()

        with pytest.raises(Exception) as exc_info:
            connector.search_papers('AI safety')

        assert 'timed out' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_search_papers_limit_respected(self, mock_get):
        """Test that limit parameter is respected."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'total': 0, 'offset': 0, 'data': []}
        mock_get.return_value = mock_response

        connector = SemanticScholarConnector()
        connector.search_papers('test', limit=150)  # Above API max

        # Should cap at 100 (API max)
        call_args = mock_get.call_args
        assert call_args[1]['params']['limit'] == 100


class TestGetPaper:
    """Test getting individual paper details."""

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_get_paper_success(self, mock_get):
        """Test successful paper retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'paperId': 'abc123',
            'title': 'Test Paper',
            'abstract': 'Test abstract',
            'year': 2024,
            'authors': [{'name': 'Author One'}],
            'citationCount': 42
        }
        mock_get.return_value = mock_response

        connector = SemanticScholarConnector()
        paper = connector.get_paper('abc123')

        assert paper is not None
        assert paper['title'] == 'Test Paper'
        assert paper['source'] == 'semantic_scholar'
        assert paper['citation_count'] == 42

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_get_paper_not_found(self, mock_get):
        """Test handling of paper not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        connector = SemanticScholarConnector()
        paper = connector.get_paper('nonexistent')

        assert paper is None

    def test_get_paper_empty_id(self):
        """Test that empty paper ID raises error."""
        connector = SemanticScholarConnector()

        with pytest.raises(ValueError) as exc_info:
            connector.get_paper('')

        assert 'cannot be empty' in str(exc_info.value).lower()


class TestGetCitationsAndReferences:
    """Test citation and reference retrieval."""

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_get_paper_citations(self, mock_get):
        """Test getting papers that cite a paper."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'citingPaper': {
                        'paperId': 'cite1',
                        'title': 'Citing Paper 1',
                        'year': 2024
                    }
                },
                {
                    'citingPaper': {
                        'paperId': 'cite2',
                        'title': 'Citing Paper 2',
                        'year': 2024
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        connector = SemanticScholarConnector()
        citations = connector.get_paper_citations('abc123', limit=50)

        assert len(citations) == 2
        assert citations[0]['title'] == 'Citing Paper 1'
        assert citations[1]['title'] == 'Citing Paper 2'

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_get_paper_references(self, mock_get):
        """Test getting papers referenced by a paper."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'citedPaper': {
                        'paperId': 'ref1',
                        'title': 'Referenced Paper 1',
                        'year': 2023
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        connector = SemanticScholarConnector()
        references = connector.get_paper_references('abc123', limit=50)

        assert len(references) == 1
        assert references[0]['title'] == 'Referenced Paper 1'

    @patch('ara_v2.services.connectors.semantic_scholar.requests.Session.get')
    def test_get_citations_error_returns_empty(self, mock_get):
        """Test that citation errors return empty list."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException()

        connector = SemanticScholarConnector()
        citations = connector.get_paper_citations('abc123')

        assert citations == []


class TestNormalizePaper:
    """Test paper data normalization."""

    def test_normalize_paper_complete_data(self):
        """Test normalization with complete paper data."""
        raw_paper = {
            'paperId': 'abc123',
            'externalIds': {
                'DOI': '10.1000/test',
                'ArXiv': '2103.00020'
            },
            'title': 'Test Paper',
            'abstract': 'Test abstract',
            'authors': [
                {'name': 'Author One'},
                {'name': 'Author Two'}
            ],
            'year': 2024,
            'venue': 'Test Conference',
            'citationCount': 42,
            'influentialCitationCount': 10,
            'fieldsOfStudy': ['Computer Science', 'AI'],
            'url': 'https://example.com'
        }

        connector = SemanticScholarConnector()
        normalized = connector._normalize_paper(raw_paper)

        assert normalized['source'] == 'semantic_scholar'
        assert normalized['source_id'] == 'abc123'
        assert normalized['doi'] == '10.1000/test'
        assert normalized['arxiv_id'] == '2103.00020'
        assert normalized['title'] == 'Test Paper'
        assert len(normalized['authors']) == 2
        assert normalized['year'] == 2024
        assert normalized['citation_count'] == 42

    def test_normalize_paper_missing_fields(self):
        """Test normalization with missing optional fields."""
        raw_paper = {
            'paperId': 'abc123',
            'title': 'Minimal Paper'
        }

        connector = SemanticScholarConnector()
        normalized = connector._normalize_paper(raw_paper)

        assert normalized['source_id'] == 'abc123'
        assert normalized['title'] == 'Minimal Paper'
        assert normalized['doi'] is None
        assert normalized['abstract'] is None
        assert normalized['authors'] == []
        assert normalized['citation_count'] == 0

    def test_normalize_paper_date_parsing(self):
        """Test publication date parsing."""
        raw_paper = {
            'paperId': 'abc123',
            'title': 'Test Paper',
            'publicationDate': '2024-03-15'
        }

        connector = SemanticScholarConnector()
        normalized = connector._normalize_paper(raw_paper)

        assert normalized['published_date'] is not None
        assert normalized['published_date'].year == 2024
        assert normalized['published_date'].month == 3
        assert normalized['published_date'].day == 15


class TestAISafetySearch:
    """Test AI safety convenience method."""

    @patch('ara_v2.services.connectors.semantic_scholar.SemanticScholarConnector.search_papers')
    def test_search_ai_safety_papers(self, mock_search):
        """Test AI safety paper search."""
        mock_search.return_value = {
            'total': 10,
            'papers': []
        }

        connector = SemanticScholarConnector()
        result = connector.search_ai_safety_papers(limit=50)

        # Verify search_papers was called
        assert mock_search.called

        # Verify comprehensive query was used
        call_args = mock_search.call_args[0]
        query = call_args[0]
        assert 'ai safety' in query.lower()
        assert 'alignment' in query.lower()
        assert 'interpretability' in query.lower()
