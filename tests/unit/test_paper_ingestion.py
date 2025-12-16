"""
Unit tests for Paper Ingestion service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, date
from ara_v2.services.paper_ingestion import PaperIngestionService


class TestPaperIngestionInitialization:
    """Test PaperIngestionService initialization."""

    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_init(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger):
        """Test service initialization."""
        service = PaperIngestionService()

        assert service is not None
        assert mock_s2.called
        assert mock_arxiv.called
        assert mock_crossref.called
        assert mock_tagger.called


class TestSearchAndIngest:
    """Test multi-source search and ingestion."""

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService.ingest_paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._deduplicate_papers')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_search_and_ingest_all_sources(
        self, mock_s2_class, mock_arxiv_class, mock_crossref_class, mock_tagger_class,
        mock_dedup, mock_ingest, mock_db, mock_app
    ):
        """Test searching and ingesting from all sources."""
        # Setup mocks
        mock_s2 = Mock()
        mock_s2.search_papers.return_value = {
            'total': 2,
            'papers': [{'title': 'S2 Paper 1'}, {'title': 'S2 Paper 2'}]
        }
        mock_s2_class.return_value = mock_s2

        mock_arxiv = Mock()
        mock_arxiv.search_papers.return_value = {
            'total': 1,
            'papers': [{'title': 'ArXiv Paper 1'}]
        }
        mock_arxiv_class.return_value = mock_arxiv

        mock_crossref = Mock()
        mock_crossref.search_papers.return_value = {
            'total': 1,
            'papers': [{'title': 'CrossRef Paper 1'}]
        }
        mock_crossref_class.return_value = mock_crossref

        mock_dedup.return_value = [
            {'title': 'S2 Paper 1'},
            {'title': 'ArXiv Paper 1'},
            {'title': 'CrossRef Paper 1'}
        ]

        mock_paper1 = Mock()
        mock_paper2 = Mock()
        mock_paper3 = Mock()
        mock_ingest.side_effect = [
            (mock_paper1, True),
            (mock_paper2, True),
            (mock_paper3, False)  # Duplicate
        ]

        # Execute
        service = PaperIngestionService()
        result = service.search_and_ingest('AI safety', max_results_per_source=20)

        # Verify
        assert result['total_fetched'] == 4
        assert result['total_ingested'] == 3
        assert result['new_papers'] == 2
        assert result['duplicates_found'] == 1
        assert len(result['papers']) == 3

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService.ingest_paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._deduplicate_papers')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_search_and_ingest_single_source(
        self, mock_s2_class, mock_arxiv_class, mock_crossref_class, mock_tagger_class,
        mock_dedup, mock_ingest, mock_db, mock_app
    ):
        """Test searching from single source only."""
        mock_s2 = Mock()
        mock_s2.search_papers.return_value = {
            'papers': [{'title': 'Test Paper'}]
        }
        mock_s2_class.return_value = mock_s2
        mock_arxiv_class.return_value = Mock()
        mock_crossref_class.return_value = Mock()

        mock_dedup.return_value = [{'title': 'Test Paper'}]
        mock_ingest.return_value = (Mock(), True)

        service = PaperIngestionService()
        result = service.search_and_ingest('test', sources=['semantic_scholar'])

        # Only S2 should be called
        assert mock_s2.search_papers.called
        assert result['fetch_stats']['semantic_scholar'] == 1

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_search_and_ingest_handles_errors(
        self, mock_s2_class, mock_arxiv_class, mock_crossref_class, mock_tagger_class,
        mock_db, mock_app
    ):
        """Test error handling during search."""
        mock_s2 = Mock()
        mock_s2.search_papers.side_effect = Exception("API Error")
        mock_s2_class.return_value = mock_s2
        mock_arxiv_class.return_value = Mock()
        mock_crossref_class.return_value = Mock()

        service = PaperIngestionService()
        result = service.search_and_ingest('test', sources=['semantic_scholar'])

        # Should handle error gracefully
        assert result['fetch_stats']['semantic_scholar'] == 0
        assert result['total_fetched'] == 0

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService.ingest_paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._deduplicate_papers')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_search_and_ingest_commit_failure(
        self, mock_s2_class, mock_arxiv_class, mock_crossref_class, mock_tagger_class,
        mock_dedup, mock_ingest, mock_db, mock_app
    ):
        """Test handling of commit failure."""
        mock_s2_class.return_value = Mock()
        mock_s2_class.return_value.search_papers.return_value = {'papers': []}
        mock_arxiv_class.return_value = Mock()
        mock_crossref_class.return_value = Mock()

        mock_dedup.return_value = []
        mock_db.session.commit.side_effect = Exception("DB Error")

        service = PaperIngestionService()

        with pytest.raises(Exception):
            service.search_and_ingest('test')

        assert mock_db.session.rollback.called


class TestIngestPaper:
    """Test single paper ingestion."""

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._find_existing_paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._assign_tags_to_paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_ingest_new_paper(
        self, mock_s2, mock_arxiv, mock_crossref, mock_tagger,
        mock_assign_tags, mock_find, mock_paper_class, mock_db, mock_app
    ):
        """Test ingesting a new paper."""
        mock_find.return_value = None  # No existing paper

        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.title = "Test Paper"
        mock_paper_class.return_value = mock_paper

        paper_data = {
            'source': 'arxiv',
            'source_id': '2103.00020',
            'title': 'Test Paper',
            'abstract': 'Test abstract',
            'authors': ['Author One'],
            'year': 2024
        }

        service = PaperIngestionService()
        result_paper, is_new = service.ingest_paper(paper_data, assign_tags=True)

        assert is_new is True
        assert result_paper == mock_paper
        assert mock_db.session.add.called
        assert mock_db.session.flush.called
        assert mock_assign_tags.called

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._update_paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._find_existing_paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_ingest_existing_paper(
        self, mock_s2, mock_arxiv, mock_crossref, mock_tagger,
        mock_find, mock_update, mock_app
    ):
        """Test ingesting an existing paper (update)."""
        mock_existing = Mock()
        mock_existing.id = 1
        mock_find.return_value = mock_existing
        mock_update.return_value = True

        paper_data = {'title': 'Existing Paper'}

        service = PaperIngestionService()
        result_paper, is_new = service.ingest_paper(paper_data)

        assert is_new is False
        assert result_paper == mock_existing
        assert mock_update.called

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._find_existing_paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_ingest_paper_without_tags(
        self, mock_s2, mock_arxiv, mock_crossref, mock_tagger,
        mock_find, mock_paper_class, mock_db, mock_app
    ):
        """Test ingesting paper without automatic tag assignment."""
        mock_find.return_value = None
        mock_paper = Mock()
        mock_paper_class.return_value = mock_paper

        service = PaperIngestionService()
        # Mock _assign_tags_to_paper to verify it's not called
        with patch.object(service, '_assign_tags_to_paper') as mock_assign:
            result_paper, is_new = service.ingest_paper({'title': 'Test'}, assign_tags=False)

            assert not mock_assign.called

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService._find_existing_paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_ingest_paper_error_handling(
        self, mock_s2, mock_arxiv, mock_crossref, mock_tagger,
        mock_find, mock_paper_class, mock_db, mock_app
    ):
        """Test error handling during paper creation."""
        mock_find.return_value = None
        mock_paper_class.side_effect = Exception("Creation error")

        service = PaperIngestionService()
        result_paper, is_new = service.ingest_paper({'title': 'Test'})

        assert result_paper is None
        assert is_new is False
        assert mock_db.session.rollback.called


class TestFindExistingPaper:
    """Test finding existing papers."""

    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_find_by_doi(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_paper):
        """Test finding paper by DOI."""
        mock_existing = Mock()
        mock_paper.query.filter_by.return_value.first.return_value = mock_existing

        service = PaperIngestionService()
        paper_data = {'doi': '10.1000/test'}
        result = service._find_existing_paper(paper_data)

        assert result == mock_existing
        mock_paper.query.filter_by.assert_called_with(doi='10.1000/test', deleted_at=None)

    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_find_by_arxiv_id(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_paper):
        """Test finding paper by ArXiv ID when no DOI."""
        # DOI query returns None, ArXiv query returns paper
        mock_existing = Mock()
        mock_paper.query.filter_by.return_value.first.side_effect = [None, mock_existing]

        service = PaperIngestionService()
        paper_data = {'arxiv_id': '2103.00020'}
        result = service._find_existing_paper(paper_data)

        assert result == mock_existing

    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_find_by_source_id(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_paper):
        """Test finding paper by source and source_id."""
        mock_existing = Mock()
        # DOI and ArXiv return None, source+source_id returns paper
        mock_paper.query.filter_by.return_value.first.side_effect = [None, None, mock_existing]

        service = PaperIngestionService()
        paper_data = {'source': 'semantic_scholar', 'source_id': 'abc123'}
        result = service._find_existing_paper(paper_data)

        assert result == mock_existing

    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_find_by_title(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_db, mock_paper):
        """Test finding paper by title matching."""
        mock_existing = Mock()
        # All ID-based queries return None
        mock_paper.query.filter_by.return_value.first.return_value = None
        # Title query returns paper
        mock_paper.query.filter.return_value.first.return_value = mock_existing

        service = PaperIngestionService()
        paper_data = {'title': 'A Very Long and Specific Paper Title'}
        result = service._find_existing_paper(paper_data)

        assert result == mock_existing

    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_find_no_match(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_paper):
        """Test when no existing paper is found."""
        mock_paper.query.filter_by.return_value.first.return_value = None
        mock_paper.query.filter.return_value.first.return_value = None

        service = PaperIngestionService()
        paper_data = {'title': 'New Paper'}
        result = service._find_existing_paper(paper_data)

        assert result is None

    @patch('ara_v2.services.paper_ingestion.Paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_find_short_title_not_matched(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_paper):
        """Test that short titles (<= 20 chars) are not matched by title."""
        mock_paper.query.filter_by.return_value.first.return_value = None

        service = PaperIngestionService()
        paper_data = {'title': 'Short Title'}  # Only 11 chars
        result = service._find_existing_paper(paper_data)

        # Should not attempt title matching
        assert not mock_paper.query.filter.called


class TestUpdatePaper:
    """Test updating existing papers."""

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_update_citation_count(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test updating citation count if higher."""
        mock_paper = Mock()
        mock_paper.citation_count = 10

        service = PaperIngestionService()
        paper_data = {'citation_count': 15}
        updated = service._update_paper(mock_paper, paper_data)

        assert updated is True
        assert mock_paper.citation_count == 15

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_update_citation_count_not_lower(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test that citation count is not updated if lower."""
        mock_paper = Mock()
        mock_paper.citation_count = 20

        service = PaperIngestionService()
        paper_data = {'citation_count': 15}
        updated = service._update_paper(mock_paper, paper_data)

        assert updated is False
        assert mock_paper.citation_count == 20

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_update_fill_missing_fields(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test filling in missing fields."""
        mock_paper = Mock()
        mock_paper.doi = None
        mock_paper.arxiv_id = None
        mock_paper.abstract = None
        mock_paper.venue = None
        mock_paper.citation_count = 5

        service = PaperIngestionService()
        paper_data = {
            'doi': '10.1000/new',
            'arxiv_id': '2103.00020',
            'abstract': 'New abstract',
            'venue': 'ICML 2024',
            'citation_count': 3  # Lower, should not update
        }
        updated = service._update_paper(mock_paper, paper_data)

        assert updated is True
        assert mock_paper.doi == '10.1000/new'
        assert mock_paper.arxiv_id == '2103.00020'
        assert mock_paper.abstract == 'New abstract'
        assert mock_paper.venue == 'ICML 2024'
        assert mock_paper.citation_count == 5  # Unchanged

    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_update_no_changes(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger):
        """Test when no updates are needed."""
        mock_paper = Mock()
        mock_paper.doi = '10.1000/existing'
        mock_paper.arxiv_id = '2103.00020'
        mock_paper.abstract = 'Existing'
        mock_paper.venue = 'ICML 2024'
        mock_paper.citation_count = 10

        service = PaperIngestionService()
        paper_data = {'citation_count': 5}  # Lower
        updated = service._update_paper(mock_paper, paper_data)

        assert updated is False


class TestDeduplicatePapers:
    """Test cross-source deduplication."""

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_deduplicate_by_doi(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test deduplication by DOI."""
        papers = [
            {'doi': '10.1000/test', 'title': 'Paper 1'},
            {'doi': '10.1000/test', 'title': 'Paper 1 Again'},  # Duplicate
            {'doi': '10.1000/other', 'title': 'Paper 2'}
        ]

        service = PaperIngestionService()
        result = service._deduplicate_papers(papers)

        assert len(result) == 2
        assert result[0]['doi'] == '10.1000/test'
        assert result[1]['doi'] == '10.1000/other'

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_deduplicate_by_arxiv_id(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test deduplication by ArXiv ID."""
        papers = [
            {'arxiv_id': '2103.00020', 'title': 'ArXiv Paper'},
            {'arxiv_id': '2103.00020', 'title': 'Same ArXiv Paper'},  # Duplicate
            {'arxiv_id': '2103.00021', 'title': 'Different Paper'}
        ]

        service = PaperIngestionService()
        result = service._deduplicate_papers(papers)

        assert len(result) == 2

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_deduplicate_by_title(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test deduplication by title for long titles."""
        papers = [
            {'title': 'A Very Long and Unique Paper Title About AI Safety'},
            {'title': 'A Very Long and Unique Paper Title About AI Safety'},  # Duplicate
            {'title': 'Different Long Paper Title About Something Else'}
        ]

        service = PaperIngestionService()
        result = service._deduplicate_papers(papers)

        assert len(result) == 2

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_deduplicate_short_titles_not_matched(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test that short titles are not deduplicated by title."""
        papers = [
            {'title': 'Short Title'},
            {'title': 'Short Title'}  # Same but too short to deduplicate
        ]

        service = PaperIngestionService()
        result = service._deduplicate_papers(papers)

        # Should keep both since title is too short
        assert len(result) == 2

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_deduplicate_mixed_identifiers(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app):
        """Test deduplication with mixed identifiers."""
        papers = [
            {'doi': '10.1000/test', 'title': 'Paper with DOI'},
            {'arxiv_id': '2103.00020', 'title': 'Paper with ArXiv'},
            {'doi': '10.1000/test', 'arxiv_id': '2103.00020', 'title': 'Paper with both'}
        ]

        service = PaperIngestionService()
        result = service._deduplicate_papers(papers)

        # DOI takes priority, so third paper is duplicate of first
        assert len(result) == 2


class TestAssignTagsToPaper:
    """Test tag assignment to papers."""

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.datetime')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.PaperTag')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_assign_tags_to_paper(
        self, mock_s2, mock_arxiv, mock_crossref, mock_tagger_class,
        mock_paper_tag_class, mock_db, mock_datetime, mock_app
    ):
        """Test assigning tags to a paper."""
        mock_tagger = Mock()
        mock_tag1 = Mock()
        mock_tag1.id = 1
        mock_tag1.name = 'interpretability'
        mock_tag2 = Mock()
        mock_tag2.id = 2
        mock_tag2.name = 'alignment'

        mock_tagger.assign_and_save_tags.return_value = [
            (mock_tag1, 0.8),
            (mock_tag2, 0.6)
        ]
        mock_tagger_class.return_value = mock_tagger

        mock_paper = Mock()
        mock_paper.id = 1

        mock_db.session.query.return_value.filter_by.return_value.count.return_value = 5

        service = PaperIngestionService()
        service._assign_tags_to_paper(mock_paper)

        # Verify PaperTag relationships were created
        assert mock_paper_tag_class.call_count == 2
        assert mock_db.session.add.call_count == 2

        # Verify tag statistics were updated
        assert mock_tag1.paper_count == 5
        assert mock_tag2.paper_count == 5

    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_assign_tags_no_tags_found(self, mock_s2, mock_arxiv, mock_crossref, mock_tagger_class):
        """Test when no tags are assigned."""
        mock_tagger = Mock()
        mock_tagger.assign_and_save_tags.return_value = []
        mock_tagger_class.return_value = mock_tagger

        mock_paper = Mock()

        service = PaperIngestionService()
        service._assign_tags_to_paper(mock_paper)

        # Should return early without creating relationships
        # No assertions needed, just verify no errors


class TestBuildCitationNetwork:
    """Test citation network building."""

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.Citation')
    @patch('ara_v2.services.paper_ingestion.PaperIngestionService.ingest_paper')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_build_citation_network(
        self, mock_s2_class, mock_arxiv, mock_crossref, mock_tagger,
        mock_ingest, mock_citation_class, mock_db, mock_app
    ):
        """Test building citation network."""
        mock_s2 = Mock()
        mock_s2.get_paper_citations.return_value = [
            {'title': 'Citing Paper 1'},
            {'title': 'Citing Paper 2'}
        ]
        mock_s2.get_paper_references.return_value = [
            {'title': 'Referenced Paper 1'}
        ]
        mock_s2_class.return_value = mock_s2

        mock_citing1 = Mock()
        mock_citing1.id = 10
        mock_citing2 = Mock()
        mock_citing2.id = 11
        mock_referenced = Mock()
        mock_referenced.id = 12

        mock_ingest.side_effect = [
            (mock_citing1, True),
            (mock_citing2, True),
            (mock_referenced, True)
        ]

        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.source = 'semantic_scholar'
        mock_paper.source_id = 'abc123'

        service = PaperIngestionService()
        stats = service.build_citation_network(mock_paper, max_citations=50, max_references=50)

        assert stats['citations_added'] == 2
        assert stats['references_added'] == 1
        assert mock_citation_class.call_count == 3

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_build_citation_network_non_s2_paper(
        self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_app
    ):
        """Test that citation network is skipped for non-S2 papers."""
        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.source = 'arxiv'
        mock_paper.source_id = '2103.00020'

        service = PaperIngestionService()
        stats = service.build_citation_network(mock_paper)

        assert stats['citations_added'] == 0
        assert stats['references_added'] == 0

    @patch('ara_v2.services.paper_ingestion.current_app')
    @patch('ara_v2.services.paper_ingestion.db')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_build_citation_network_error_handling(
        self, mock_s2_class, mock_arxiv, mock_crossref, mock_tagger, mock_db, mock_app
    ):
        """Test error handling during citation network building."""
        mock_s2 = Mock()
        mock_s2.get_paper_citations.side_effect = Exception("API Error")
        mock_s2_class.return_value = mock_s2

        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.source = 'semantic_scholar'
        mock_paper.source_id = 'abc123'

        service = PaperIngestionService()
        stats = service.build_citation_network(mock_paper)

        # Should handle error gracefully
        assert mock_db.session.rollback.called


class TestSearchAISafetyPapers:
    """Test AI safety convenience method."""

    @patch('ara_v2.services.paper_ingestion.PaperIngestionService.search_and_ingest')
    @patch('ara_v2.services.paper_ingestion.TagAssigner')
    @patch('ara_v2.services.paper_ingestion.CrossRefConnector')
    @patch('ara_v2.services.paper_ingestion.ArxivConnector')
    @patch('ara_v2.services.paper_ingestion.SemanticScholarConnector')
    def test_search_ai_safety_papers(
        self, mock_s2, mock_arxiv, mock_crossref, mock_tagger, mock_search
    ):
        """Test AI safety paper search convenience method."""
        mock_search.return_value = {
            'total_fetched': 100,
            'total_ingested': 85,
            'papers': []
        }

        service = PaperIngestionService()
        result = service.search_ai_safety_papers(max_results=50)

        # Verify search_and_ingest was called with AI safety query
        assert mock_search.called
        call_args = mock_search.call_args
        query = call_args[1]['query']
        assert 'ai safety' in query.lower()
        assert 'alignment' in query.lower()
        assert call_args[1]['max_results_per_source'] == 50
        assert call_args[1]['assign_tags'] is True
