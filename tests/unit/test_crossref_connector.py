"""
Unit tests for CrossRef API connector.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date
from ara_v2.services.connectors.crossref import CrossRefConnector


class TestCrossRefConnector:
    """Test CrossRef connector initialization."""

    def test_init_without_mailto(self):
        """Test connector initialization without mailto email."""
        connector = CrossRefConnector()

        assert connector.mailto_email is None
        assert connector.BASE_URL == "https://api.crossref.org"
        assert 'User-Agent' in connector.session.headers
        assert 'ARA-v2' in connector.session.headers['User-Agent']
        assert 'mailto' not in connector.session.headers['User-Agent']

    def test_init_with_mailto(self):
        """Test connector initialization with mailto email."""
        email = "contact@example.com"
        connector = CrossRefConnector(mailto_email=email)

        assert connector.mailto_email == email
        assert 'User-Agent' in connector.session.headers
        assert f'mailto:{email}' in connector.session.headers['User-Agent']

    def test_user_agent_set(self):
        """Test that user agent is set correctly."""
        connector = CrossRefConnector()

        assert 'User-Agent' in connector.session.headers
        assert 'ARA-v2' in connector.session.headers['User-Agent']


class TestSearchPapers:
    """Test paper search functionality."""

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_papers_success(self, mock_get):
        """Test successful paper search."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ok',
            'message': {
                'total-results': 2,
                'items': [
                    {
                        'DOI': '10.1000/test1',
                        'title': ['Test Paper 1'],
                        'abstract': 'Abstract 1',
                        'author': [{'given': 'John', 'family': 'Doe'}],
                        'published': {'date-parts': [[2024, 3, 15]]},
                        'is-referenced-by-count': 10
                    },
                    {
                        'DOI': '10.1000/test2',
                        'title': ['Test Paper 2'],
                        'author': [{'given': 'Jane', 'family': 'Smith'}],
                        'published': {'date-parts': [[2024, 2, 10]]},
                        'is-referenced-by-count': 5
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        connector = CrossRefConnector()
        result = connector.search_papers('machine learning', rows=10)

        assert result['total'] == 2
        assert len(result['papers']) == 2
        assert result['papers'][0]['source'] == 'crossref'
        assert result['papers'][0]['doi'] == '10.1000/test1'
        assert result['papers'][0]['title'] == 'Test Paper 1'
        assert result['papers'][1]['title'] == 'Test Paper 2'

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_papers_with_filters(self, mock_get):
        """Test paper search with filter parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'total-results': 0,
                'items': []
            }
        }
        mock_get.return_value = mock_response

        connector = CrossRefConnector()
        filters = {
            'type': 'journal-article',
            'has-abstract': 'true',
            'from-pub-date': '2020'
        }
        result = connector.search_papers('AI safety', rows=20, filter_params=filters)

        # Verify filters were applied
        call_args = mock_get.call_args
        assert 'filter' in call_args[1]['params']
        filter_str = call_args[1]['params']['filter']
        assert 'type:journal-article' in filter_str
        assert 'has-abstract:true' in filter_str
        assert 'from-pub-date:2020' in filter_str

    def test_search_papers_empty_query(self):
        """Test that empty query raises error."""
        connector = CrossRefConnector()

        with pytest.raises(ValueError) as exc_info:
            connector.search_papers('')

        assert 'cannot be empty' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_papers_limit_capped(self, mock_get):
        """Test that rows parameter is capped at API maximum."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {'total-results': 0, 'items': []}
        }
        mock_get.return_value = mock_response

        connector = CrossRefConnector()
        connector.search_papers('test', rows=2000)  # Above API max of 1000

        # Should cap at 1000
        call_args = mock_get.call_args
        assert call_args[1]['params']['rows'] == 1000

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_papers_timeout(self, mock_get):
        """Test handling of request timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        connector = CrossRefConnector()

        with pytest.raises(Exception) as exc_info:
            connector.search_papers('test')

        assert 'timed out' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_papers_request_exception(self, mock_get):
        """Test handling of general request exception."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        connector = CrossRefConnector()

        with pytest.raises(Exception) as exc_info:
            connector.search_papers('test')

        assert 'failed' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_papers_with_sorting(self, mock_get):
        """Test search with sorting parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {'total-results': 0, 'items': []}
        }
        mock_get.return_value = mock_response

        connector = CrossRefConnector()
        connector.search_papers('test', sort='updated')

        call_args = mock_get.call_args
        assert call_args[1]['params']['sort'] == 'updated'


class TestGetPaperByDOI:
    """Test getting individual paper by DOI."""

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_get_paper_success(self, mock_get):
        """Test successful paper retrieval by DOI."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'DOI': '10.1000/test',
                'title': ['Test Paper'],
                'abstract': 'Test abstract',
                'author': [{'given': 'John', 'family': 'Doe'}],
                'published': {'date-parts': [[2024, 3, 15]]},
                'is-referenced-by-count': 42
            }
        }
        mock_get.return_value = mock_response

        connector = CrossRefConnector()
        paper = connector.get_paper_by_doi('10.1000/test')

        assert paper is not None
        assert paper['doi'] == '10.1000/test'
        assert paper['title'] == 'Test Paper'
        assert paper['source'] == 'crossref'
        assert paper['citation_count'] == 42

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_get_paper_not_found(self, mock_get):
        """Test handling of paper not found (404)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        connector = CrossRefConnector()
        paper = connector.get_paper_by_doi('10.9999/nonexistent')

        assert paper is None

    def test_get_paper_empty_doi(self):
        """Test that empty DOI raises error."""
        connector = CrossRefConnector()

        with pytest.raises(ValueError) as exc_info:
            connector.get_paper_by_doi('')

        assert 'cannot be empty' in str(exc_info.value).lower()

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_get_paper_cleans_doi_url(self, mock_get):
        """Test that DOI URL prefixes are cleaned."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'DOI': '10.1000/test',
                'title': ['Test'],
                'published': {'date-parts': [[2024]]}
            }
        }
        mock_get.return_value = mock_response

        connector = CrossRefConnector()

        # Test with HTTPS DOI URL
        paper = connector.get_paper_by_doi('https://doi.org/10.1000/test')
        call_args = mock_get.call_args[0][0]
        assert call_args.endswith('/10.1000/test')

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_get_paper_timeout(self, mock_get):
        """Test handling of timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        connector = CrossRefConnector()

        with pytest.raises(Exception) as exc_info:
            connector.get_paper_by_doi('10.1000/test')

        assert 'timed out' in str(exc_info.value).lower()


class TestSearchByTitle:
    """Test title-based search."""

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_by_title_success(self, mock_get):
        """Test successful title search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'total-results': 1,
                'items': [
                    {
                        'DOI': '10.1000/test',
                        'title': ['Attention Is All You Need'],
                        'author': [{'given': 'Ashish', 'family': 'Vaswani'}],
                        'published': {'date-parts': [[2017, 6, 12]]}
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        connector = CrossRefConnector()
        result = connector.search_by_title('Attention Is All You Need', rows=10)

        assert result['total'] == 1
        assert len(result['papers']) == 1
        assert result['papers'][0]['title'] == 'Attention Is All You Need'

        # Verify bibliographic query was used
        call_args = mock_get.call_args
        assert 'query.bibliographic' in call_args[1]['params']

    @patch('ara_v2.services.connectors.crossref.requests.Session.get')
    def test_search_by_title_error(self, mock_get):
        """Test handling of title search error."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Error")

        connector = CrossRefConnector()

        with pytest.raises(Exception) as exc_info:
            connector.search_by_title('Test Title')

        assert 'failed' in str(exc_info.value).lower()


class TestAISafetySearch:
    """Test AI safety convenience method."""

    @patch('ara_v2.services.connectors.crossref.CrossRefConnector.search_papers')
    def test_search_ai_safety_papers(self, mock_search):
        """Test AI safety paper search."""
        mock_search.return_value = {'total': 10, 'papers': []}

        connector = CrossRefConnector()
        result = connector.search_ai_safety_papers(rows=50)

        # Verify search_papers was called
        assert mock_search.called

        # Verify comprehensive query was used
        call_args = mock_search.call_args[0]
        query = call_args[0]
        assert 'ai safety' in query.lower()
        assert 'alignment' in query.lower()
        assert 'interpretability' in query.lower()

        # Verify has-abstract filter was added
        filter_params = mock_search.call_args[0][3]
        assert filter_params['has-abstract'] == 'true'

    @patch('ara_v2.services.connectors.crossref.CrossRefConnector.search_papers')
    def test_search_ai_safety_with_year_filters(self, mock_search):
        """Test AI safety search with year filters."""
        mock_search.return_value = {'total': 5, 'papers': []}

        connector = CrossRefConnector()
        result = connector.search_ai_safety_papers(
            rows=30,
            offset=10,
            year_from=2020,
            year_to=2024
        )

        # Verify year filters were added
        filter_params = mock_search.call_args[0][3]
        assert filter_params['from-pub-date'] == '2020'
        assert filter_params['until-pub-date'] == '2024'


class TestNormalizePaper:
    """Test paper data normalization."""

    def test_normalize_paper_complete_data(self):
        """Test normalization with complete paper data."""
        item = {
            'DOI': '10.1000/test',
            'title': ['Test Paper: A Comprehensive Study'],
            'abstract': 'This is a test abstract with important information.',
            'author': [
                {'given': 'John', 'family': 'Doe'},
                {'given': 'Jane', 'family': 'Smith'}
            ],
            'published': {'date-parts': [[2024, 3, 15]]},
            'container-title': ['Nature Machine Intelligence'],
            'publisher': 'Springer Nature',
            'is-referenced-by-count': 42,
            'reference-count': 35,
            'type': 'journal-article',
            'subject': ['Computer Science', 'Artificial Intelligence'],
            'URL': 'https://example.com/paper',
            'ISSN': ['1234-5678'],
            'ISBN': ['978-0-123456-78-9']
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert normalized['source'] == 'crossref'
        assert normalized['source_id'] == '10.1000/test'
        assert normalized['doi'] == '10.1000/test'
        assert normalized['title'] == 'Test Paper: A Comprehensive Study'
        assert normalized['abstract'] == 'This is a test abstract with important information.'
        assert len(normalized['authors']) == 2
        assert normalized['authors'][0] == 'John Doe'
        assert normalized['authors'][1] == 'Jane Smith'
        assert normalized['year'] == 2024
        assert normalized['published_date'] == date(2024, 3, 15)
        assert 'Nature Machine Intelligence' in normalized['venue']
        assert normalized['publisher'] == 'Springer Nature'
        assert normalized['citation_count'] == 42
        assert normalized['reference_count'] == 35
        assert normalized['type'] == 'journal-article'
        assert len(normalized['subjects']) == 2
        assert normalized['url'] == 'https://example.com/paper'

    def test_normalize_paper_minimal_data(self):
        """Test normalization with minimal paper data."""
        item = {
            'DOI': '10.1000/minimal',
            'title': ['Minimal Paper']
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert normalized['doi'] == '10.1000/minimal'
        assert normalized['title'] == 'Minimal Paper'
        assert normalized['abstract'] is None
        assert normalized['authors'] == []
        assert normalized['year'] is None
        assert normalized['published_date'] is None
        assert normalized['citation_count'] == 0
        assert normalized['subjects'] == []

    def test_normalize_paper_date_parsing_full(self):
        """Test full date parsing (year, month, day)."""
        item = {
            'DOI': '10.1000/test',
            'title': ['Test'],
            'published': {'date-parts': [[2024, 3, 15]]}
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert normalized['published_date'] == date(2024, 3, 15)
        assert normalized['year'] == 2024

    def test_normalize_paper_date_parsing_year_month(self):
        """Test date parsing with year and month only."""
        item = {
            'DOI': '10.1000/test',
            'title': ['Test'],
            'published': {'date-parts': [[2024, 3]]}
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert normalized['published_date'] == date(2024, 3, 1)
        assert normalized['year'] == 2024

    def test_normalize_paper_date_parsing_year_only(self):
        """Test date parsing with year only."""
        item = {
            'DOI': '10.1000/test',
            'title': ['Test'],
            'published': {'date-parts': [[2024]]}
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert normalized['published_date'] == date(2024, 1, 1)
        assert normalized['year'] == 2024

    def test_normalize_paper_fallback_dates(self):
        """Test fallback to published-print or published-online."""
        item_print = {
            'DOI': '10.1000/test',
            'title': ['Test'],
            'published-print': {'date-parts': [[2024, 5, 20]]}
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item_print)
        assert normalized['published_date'] == date(2024, 5, 20)

    def test_normalize_paper_author_name_formats(self):
        """Test various author name formats."""
        item = {
            'DOI': '10.1000/test',
            'title': ['Test'],
            'author': [
                {'given': 'John', 'family': 'Doe'},  # Full name
                {'family': 'Smith'},  # Family only
                {'given': 'Alice'}  # Given only (should be skipped)
            ]
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert len(normalized['authors']) == 2
        assert 'John Doe' in normalized['authors']
        assert 'Smith' in normalized['authors']

    def test_normalize_paper_venue_construction(self):
        """Test venue construction from container and publisher."""
        item1 = {
            'DOI': '10.1000/test',
            'title': ['Test'],
            'container-title': ['Nature'],
            'publisher': 'Springer'
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item1)
        assert normalized['venue'] == 'Nature - Springer'

    def test_normalize_paper_doi_url_generation(self):
        """Test URL generation when not provided."""
        item = {
            'DOI': '10.1000/test',
            'title': ['Test']
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert normalized['url'] == 'https://doi.org/10.1000/test'

    def test_normalize_paper_empty_title_list(self):
        """Test handling of empty title list."""
        item = {
            'DOI': '10.1000/test',
            'title': []
        }

        connector = CrossRefConnector()
        normalized = connector._normalize_paper(item)

        assert normalized['title'] == ''


class TestBuildFilter:
    """Test filter builder helper."""

    def test_build_filter_single_parameter(self):
        """Test building filter with single parameter."""
        filters = CrossRefConnector.build_filter(work_type='journal-article')

        assert filters == {'type': 'journal-article'}

    def test_build_filter_multiple_parameters(self):
        """Test building filter with multiple parameters."""
        filters = CrossRefConnector.build_filter(
            work_type='journal-article',
            has_abstract=True,
            has_references=True,
            year_from=2020,
            year_to=2024
        )

        assert filters['type'] == 'journal-article'
        assert filters['has-abstract'] == 'true'
        assert filters['has-references'] == 'true'
        assert filters['from-pub-date'] == '2020'
        assert filters['until-pub-date'] == '2024'

    def test_build_filter_all_parameters(self):
        """Test building filter with all parameters."""
        filters = CrossRefConnector.build_filter(
            work_type='proceedings-article',
            has_abstract=True,
            has_references=True,
            has_full_text=True,
            year_from=2015,
            year_to=2025
        )

        assert len(filters) == 6
        assert filters['type'] == 'proceedings-article'
        assert filters['has-abstract'] == 'true'
        assert filters['has-references'] == 'true'
        assert filters['has-full-text'] == 'true'
        assert filters['from-pub-date'] == '2015'
        assert filters['until-pub-date'] == '2025'

    def test_build_filter_empty_returns_empty(self):
        """Test that no parameters returns empty dict."""
        filters = CrossRefConnector.build_filter()

        assert filters == {}

    def test_build_filter_false_booleans_excluded(self):
        """Test that False boolean parameters are excluded."""
        filters = CrossRefConnector.build_filter(
            has_abstract=False,
            has_references=False,
            has_full_text=False
        )

        assert filters == {}
