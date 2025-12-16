"""
Unit tests for ArXiv API connector.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ara_v2.services.connectors.arxiv import ArxivConnector


class TestArxivConnector:
    """Test ArXiv connector initialization."""

    def test_init(self):
        """Test connector initialization."""
        connector = ArxivConnector()

        assert connector is not None
        assert connector.BASE_URL == "http://export.arxiv.org/api/query"

    def test_ai_safety_categories_defined(self):
        """Test that AI safety categories are defined."""
        assert len(ArxivConnector.AI_SAFETY_CATEGORIES) > 0
        assert 'cs.AI' in ArxivConnector.AI_SAFETY_CATEGORIES
        assert 'cs.LG' in ArxivConnector.AI_SAFETY_CATEGORIES


class TestSearchPapers:
    """Test paper search functionality."""

    @patch('ara_v2.services.connectors.arxiv.feedparser.parse')
    def test_search_papers_success(self, mock_parse):
        """Test successful paper search."""
        # Mock feedparser response
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {
            'opensearch_totalresults': '2',
            'opensearch_startindex': '0'
        }
        mock_feed.entries = [
            {
                'id': 'http://arxiv.org/abs/2103.00020',
                'title': 'Test Paper 1',
                'summary': 'Abstract 1',
                'published': '2024-03-15T00:00:00Z',
                'authors': [{'name': 'Author One'}],
                'tags': [{'term': 'cs.AI'}],
                'links': []
            },
            {
                'id': 'http://arxiv.org/abs/2103.00021',
                'title': 'Test Paper 2',
                'summary': 'Abstract 2',
                'published': '2024-03-16T00:00:00Z',
                'authors': [{'name': 'Author Two'}],
                'tags': [{'term': 'cs.LG'}],
                'links': []
            }
        ]
        mock_parse.return_value = mock_feed

        connector = ArxivConnector()
        result = connector.search_papers('machine learning', max_results=10)

        assert result['total'] == 2
        assert result['start'] == 0
        assert len(result['papers']) == 2
        assert result['papers'][0]['source'] == 'arxiv'
        assert result['papers'][0]['title'] == 'Test Paper 1'

    def test_search_papers_empty_query(self):
        """Test that empty query raises error."""
        connector = ArxivConnector()

        with pytest.raises(ValueError) as exc_info:
            connector.search_papers('')

        assert 'cannot be empty' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.arxiv.feedparser.parse')
    def test_search_papers_limit_capped(self, mock_parse):
        """Test that max_results is capped at 100."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {'opensearch_totalresults': '0', 'opensearch_startindex': '0'}
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        connector = ArxivConnector()
        result = connector.search_papers('test', max_results=200)

        # Check that URL contains max_results=100 (capped)
        call_args = mock_parse.call_args[0][0]
        assert 'max_results=100' in call_args

    @patch('ara_v2.services.connectors.arxiv.feedparser.parse')
    def test_search_papers_with_sorting(self, mock_parse):
        """Test search with sorting parameters."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {'opensearch_totalresults': '0', 'opensearch_startindex': '0'}
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        connector = ArxivConnector()
        connector.search_papers('test', sort_by='submittedDate', sort_order='descending')

        call_args = mock_parse.call_args[0][0]
        assert 'sortBy=submittedDate' in call_args
        assert 'sortOrder=descending' in call_args

    @patch('ara_v2.services.connectors.arxiv.feedparser.parse')
    def test_search_papers_feed_error(self, mock_parse):
        """Test handling of feed parsing error."""
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("Parse error")
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        connector = ArxivConnector()

        with pytest.raises(Exception) as exc_info:
            connector.search_papers('test')

        assert 'parse' in str(exc_info.value).lower()


class TestGetPaper:
    """Test getting individual paper by ArXiv ID."""

    @patch('ara_v2.services.connectors.arxiv.feedparser.parse')
    def test_get_paper_success(self, mock_parse):
        """Test successful paper retrieval by ArXiv ID."""
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                'id': 'http://arxiv.org/abs/2103.00020',
                'title': 'Test Paper',
                'summary': 'Test abstract',
                'published': '2024-03-15T00:00:00Z',
                'authors': [{'name': 'Author One'}],
                'tags': [{'term': 'cs.AI'}],
                'links': []
            }
        ]
        mock_parse.return_value = mock_feed

        connector = ArxivConnector()
        paper = connector.get_paper('2103.00020')

        assert paper is not None
        assert paper['arxiv_id'] == '2103.00020'
        assert paper['title'] == 'Test Paper'

    @patch('ara_v2.services.connectors.arxiv.feedparser.parse')
    def test_get_paper_not_found(self, mock_parse):
        """Test handling of paper not found."""
        mock_feed = MagicMock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        connector = ArxivConnector()
        paper = connector.get_paper('9999.99999')

        assert paper is None

    def test_get_paper_empty_id(self):
        """Test that empty ArXiv ID raises error."""
        connector = ArxivConnector()

        with pytest.raises(ValueError) as exc_info:
            connector.get_paper('')

        assert 'cannot be empty' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.arxiv.feedparser.parse')
    def test_get_paper_strips_arxiv_prefix(self, mock_parse):
        """Test that 'arXiv:' prefix is stripped from ID."""
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                'id': 'http://arxiv.org/abs/2103.00020',
                'title': 'Test',
                'summary': '',
                'published': '2024-03-15T00:00:00Z',
                'authors': [],
                'tags': [],
                'links': []
            }
        ]
        mock_parse.return_value = mock_feed

        connector = ArxivConnector()
        paper = connector.get_paper('arXiv:2103.00020')

        # Should call with cleaned ID
        call_args = mock_parse.call_args[0][0]
        assert 'id_list=2103.00020' in call_args


class TestSearchByCategory:
    """Test category-based search."""

    @patch('ara_v2.services.connectors.arxiv.ArxivConnector.search_papers')
    def test_search_by_category(self, mock_search):
        """Test search by ArXiv category."""
        mock_search.return_value = {'total': 0, 'papers': []}

        connector = ArxivConnector()
        result = connector.search_by_category('cs.AI', max_results=20)

        # Verify search_papers was called with category query
        assert mock_search.called
        call_args = mock_search.call_args
        assert 'cat:cs.AI' in call_args[0][0]


class TestAISafetySearch:
    """Test AI safety convenience method."""

    @patch('ara_v2.services.connectors.arxiv.ArxivConnector.search_papers')
    def test_search_ai_safety_papers(self, mock_search):
        """Test AI safety paper search."""
        mock_search.return_value = {'total': 0, 'papers': []}

        connector = ArxivConnector()
        result = connector.search_ai_safety_papers(max_results=50)

        assert mock_search.called
        call_args = mock_search.call_args[0]
        query = call_args[0]

        # Verify comprehensive query
        assert 'interpretability' in query.lower()
        assert 'alignment' in query.lower()

        # Verify category filtering
        assert 'cat:' in query


class TestNormalizePaper:
    """Test paper data normalization."""

    def test_normalize_paper_complete_data(self):
        """Test normalization with complete paper data."""
        entry = {
            'id': 'http://arxiv.org/abs/2103.00020',
            'title': 'Test Paper',
            'summary': 'Test abstract',
            'published': '2024-03-15T00:00:00Z',
            'updated': '2024-03-16T00:00:00Z',
            'authors': [
                {'name': 'Author One'},
                {'name': 'Author Two'}
            ],
            'tags': [
                {'term': 'cs.AI'},
                {'term': 'cs.LG'}
            ],
            'arxiv_primary_category': {'term': 'cs.AI'},
            'arxiv_doi': '10.1000/test',
            'arxiv_journal_ref': 'Test Journal 2024',
            'arxiv_comment': 'Accepted at Test Conference',
            'links': [
                {'href': 'http://arxiv.org/pdf/2103.00020', 'type': 'application/pdf'}
            ]
        }

        connector = ArxivConnector()
        normalized = connector._normalize_paper(entry)

        assert normalized['source'] == 'arxiv'
        assert normalized['arxiv_id'] == '2103.00020'
        assert normalized['doi'] == '10.1000/test'
        assert normalized['title'] == 'Test Paper'
        assert len(normalized['authors']) == 2
        assert normalized['year'] == 2024
        assert normalized['primary_category'] == 'cs.AI'
        assert len(normalized['categories']) == 2
        assert normalized['pdf_url'] == 'http://arxiv.org/pdf/2103.00020'

    def test_normalize_paper_minimal_data(self):
        """Test normalization with minimal paper data."""
        entry = {
            'id': 'http://arxiv.org/abs/2103.00020',
            'title': 'Minimal Paper',
            'summary': '',
            'published': '2024-01-01T00:00:00Z',
            'authors': [],
            'tags': [],
            'links': []
        }

        connector = ArxivConnector()
        normalized = connector._normalize_paper(entry)

        assert normalized['arxiv_id'] == '2103.00020'
        assert normalized['title'] == 'Minimal Paper'
        assert normalized['authors'] == []
        assert normalized['categories'] == []
        assert normalized['citation_count'] == 0  # ArXiv doesn't provide this

    def test_normalize_paper_date_parsing(self):
        """Test publication date parsing."""
        entry = {
            'id': 'http://arxiv.org/abs/2103.00020',
            'title': 'Test',
            'summary': '',
            'published': '2024-03-15T12:30:45Z',
            'authors': [],
            'tags': [],
            'links': []
        }

        connector = ArxivConnector()
        normalized = connector._normalize_paper(entry)

        assert normalized['published_date'] is not None
        assert normalized['published_date'].year == 2024
        assert normalized['published_date'].month == 3
        assert normalized['published_date'].day == 15

    def test_normalize_paper_extracts_arxiv_id_from_url(self):
        """Test ArXiv ID extraction from various URL formats."""
        test_cases = [
            'http://arxiv.org/abs/2103.00020',
            'https://arxiv.org/abs/2103.00020v1',
            'http://arxiv.org/abs/2103.00020'
        ]

        connector = ArxivConnector()

        for url in test_cases:
            entry = {
                'id': url,
                'title': 'Test',
                'summary': '',
                'published': '2024-01-01T00:00:00Z',
                'authors': [],
                'tags': [],
                'links': []
            }
            normalized = connector._normalize_paper(entry)
            assert '2103.00020' in normalized['arxiv_id']


class TestBuildQuery:
    """Test query builder helper."""

    def test_build_query_single_field(self):
        """Test building query with single field."""
        query = ArxivConnector.build_query(title='interpretability')

        assert query == 'ti:interpretability'

    def test_build_query_multiple_fields(self):
        """Test building query with multiple fields."""
        query = ArxivConnector.build_query(
            title='interpretability',
            author='bengio',
            category='cs.AI'
        )

        assert 'ti:interpretability' in query
        assert 'au:bengio' in query
        assert 'cat:cs.AI' in query
        assert ' AND ' in query

    def test_build_query_all_fields(self):
        """Test building query with all field types."""
        query = ArxivConnector.build_query(
            title='test',
            author='smith',
            abstract='machine learning',
            category='cs.LG',
            all_fields='AI'
        )

        assert 'ti:test' in query
        assert 'au:smith' in query
        assert 'abs:machine learning' in query
        assert 'cat:cs.LG' in query
        assert 'all:AI' in query

    def test_build_query_empty_returns_empty(self):
        """Test that no parameters returns empty string."""
        query = ArxivConnector.build_query()

        assert query == ''
