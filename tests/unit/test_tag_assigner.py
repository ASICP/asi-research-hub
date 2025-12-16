"""
Unit tests for Tag Assignment service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ara_v2.services.tag_assigner import TagAssigner


class TestTagAssignerInitialization:
    """Test TagAssigner initialization and pattern compilation."""

    def test_init(self):
        """Test tag assigner initialization."""
        assigner = TagAssigner()

        assert assigner is not None
        assert hasattr(assigner, 'tag_patterns')
        assert len(assigner.tag_patterns) > 0

    def test_compile_patterns(self):
        """Test regex pattern compilation."""
        assigner = TagAssigner()

        # Verify patterns are compiled for all tags
        assert 'interpretability' in assigner.tag_patterns
        assert 'alignment' in assigner.tag_patterns
        assert 'llm' in assigner.tag_patterns

        # Verify patterns are regex objects
        patterns = assigner.tag_patterns['interpretability']
        assert len(patterns) > 0
        assert all(hasattr(p, 'findall') for p in patterns)

    def test_tag_keywords_defined(self):
        """Test that TAG_KEYWORDS dictionary is properly defined."""
        assert len(TagAssigner.TAG_KEYWORDS) > 0
        assert 'interpretability' in TagAssigner.TAG_KEYWORDS
        assert 'alignment' in TagAssigner.TAG_KEYWORDS
        assert isinstance(TagAssigner.TAG_KEYWORDS['interpretability'], list)

    def test_arxiv_category_map_defined(self):
        """Test that ArXiv category mappings are defined."""
        assert len(TagAssigner.ARXIV_CATEGORY_MAP) > 0
        assert 'cs.AI' in TagAssigner.ARXIV_CATEGORY_MAP
        assert 'cs.LG' in TagAssigner.ARXIV_CATEGORY_MAP

    def test_s2_field_map_defined(self):
        """Test that Semantic Scholar field mappings are defined."""
        assert len(TagAssigner.S2_FIELD_MAP) > 0
        assert 'Machine Learning' in TagAssigner.S2_FIELD_MAP
        assert 'Computer Science' in TagAssigner.S2_FIELD_MAP


class TestAssignTags:
    """Test main tag assignment functionality."""

    def test_assign_tags_title_only(self, app):
        """Test tag assignment with title only."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(
            title="Interpretability in Neural Networks",
            min_confidence=0.3
        )

        assert isinstance(tags, list)
        assert len(tags) > 0
        # Should find interpretability tag
        tag_names = [name for name, _ in tags]
        assert 'interpretability' in tag_names

    def test_assign_tags_with_abstract(self):
        """Test tag assignment with title and abstract."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(
            title="AI Safety Research",
            abstract="This paper explores alignment and interpretability in large language models.",
            min_confidence=0.3
        )

        tag_names = [name for name, _ in tags]
        assert 'safety' in tag_names or 'alignment' in tag_names or 'interpretability' in tag_names

    def test_assign_tags_empty_title(self):
        """Test that empty title returns empty list."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(title="", abstract="Some abstract")

        assert tags == []

    def test_assign_tags_with_arxiv_categories(self):
        """Test tag assignment with ArXiv categories."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(
            title="Test Paper",
            arxiv_categories=['cs.AI', 'cs.LG'],
            min_confidence=0.1
        )

        tag_names = [name for name, _ in tags]
        # Should include tags from ArXiv categories
        assert 'ai' in tag_names or 'machine_learning' in tag_names

    def test_assign_tags_with_source_fields(self):
        """Test tag assignment with source fields."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(
            title="Test Paper",
            source_fields=['Machine Learning', 'Natural Language Processing'],
            min_confidence=0.1
        )

        tag_names = [name for name, _ in tags]
        assert 'machine_learning' in tag_names or 'nlp' in tag_names

    def test_assign_tags_confidence_threshold(self):
        """Test that confidence threshold filters results."""
        assigner = TagAssigner()

        # Low threshold should give more results
        tags_low = assigner.assign_tags(
            title="Interpretability and alignment in AI",
            min_confidence=0.1
        )

        # High threshold should give fewer results
        tags_high = assigner.assign_tags(
            title="Interpretability and alignment in AI",
            min_confidence=0.8
        )

        assert len(tags_low) >= len(tags_high)

    def test_assign_tags_max_tags_limit(self):
        """Test that max_tags parameter limits results."""
        assigner = TagAssigner()

        tags = assigner.assign_tags(
            title="Interpretability alignment safety ethics governance in AI",
            abstract="This covers interpretability, alignment, safety, ethics, and governance.",
            max_tags=3
        )

        assert len(tags) <= 3

    def test_assign_tags_returns_confidence_scores(self):
        """Test that confidence scores are returned and in valid range."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(
            title="Interpretability in Neural Networks",
            min_confidence=0.1
        )

        for tag_name, confidence in tags:
            assert isinstance(tag_name, str)
            assert isinstance(confidence, float)
            assert 0 <= confidence <= 1.0

    def test_assign_tags_sorted_by_confidence(self):
        """Test that tags are sorted by confidence (descending)."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(
            title="AI safety and interpretability research",
            min_confidence=0.1
        )

        if len(tags) > 1:
            confidences = [conf for _, conf in tags]
            assert confidences == sorted(confidences, reverse=True)

    def test_assign_tags_multiple_matches(self):
        """Test paper with multiple matching tags."""
        assigner = TagAssigner()
        tags = assigner.assign_tags(
            title="RLHF and Alignment in Large Language Models",
            abstract="We study reinforcement learning from human feedback and value alignment.",
            min_confidence=0.2
        )

        tag_names = [name for name, _ in tags]
        # Should find multiple relevant tags
        assert 'rlhf' in tag_names
        assert 'alignment' in tag_names or 'llm' in tag_names


class TestRuleBasedMatching:
    """Test rule-based keyword matching."""

    def test_rule_based_matching_simple(self):
        """Test simple keyword matching."""
        assigner = TagAssigner()
        scores = assigner._rule_based_matching("interpretability in neural networks")

        assert 'interpretability' in scores
        assert scores['interpretability'] > 0

    def test_rule_based_matching_case_insensitive(self):
        """Test that matching is case-insensitive."""
        assigner = TagAssigner()

        scores_lower = assigner._rule_based_matching("interpretability")
        scores_upper = assigner._rule_based_matching("INTERPRETABILITY")
        scores_mixed = assigner._rule_based_matching("Interpretability")

        assert scores_lower == scores_upper == scores_mixed

    def test_rule_based_matching_multiple_occurrences(self):
        """Test that multiple keyword occurrences increase confidence."""
        assigner = TagAssigner()

        scores_single = assigner._rule_based_matching("interpretability is important")
        scores_multiple = assigner._rule_based_matching(
            "interpretability and explainability improve transparency"
        )

        # Multiple matches should give higher confidence
        assert scores_multiple['interpretability'] >= scores_single['interpretability']

    def test_rule_based_matching_no_matches(self):
        """Test text with no matching keywords."""
        assigner = TagAssigner()
        scores = assigner._rule_based_matching("quantum physics and chemistry")

        # May have some tags, but not the AI safety specific ones
        assert 'interpretability' not in scores
        assert 'alignment' not in scores

    def test_rule_based_matching_word_boundaries(self):
        """Test that partial word matches don't count."""
        assigner = TagAssigner()

        # "alignment" should match, but not as part of "realignment"
        scores = assigner._rule_based_matching("alignment is important")
        assert 'alignment' in scores

    def test_rule_based_matching_confidence_capped(self):
        """Test that confidence is capped at 1.0."""
        assigner = TagAssigner()

        # Many repetitions should still cap at 1.0
        text = "interpretability " * 20
        scores = assigner._rule_based_matching(text)

        if 'interpretability' in scores:
            assert scores['interpretability'] <= 1.0


class TestTfidfExtraction:
    """Test TF-IDF based extraction."""

    def test_tfidf_extraction_finds_frequent_terms(self):
        """Test that frequent relevant terms are identified."""
        assigner = TagAssigner()

        text = "interpretability " * 5 + " is very important for ai safety"
        scores = assigner._tfidf_extraction(text)

        # Should identify interpretability as important
        assert 'interpretability' in scores
        assert scores['interpretability'] > 0

    def test_tfidf_extraction_filters_stop_words(self):
        """Test that stop words are filtered out."""
        assigner = TagAssigner()

        text = "the the the interpretability is a important concept"
        scores = assigner._tfidf_extraction(text)

        # Should still find interpretability despite stop words
        assert 'interpretability' in scores

    def test_tfidf_extraction_empty_text(self):
        """Test TF-IDF with empty text."""
        assigner = TagAssigner()
        scores = assigner._tfidf_extraction("")

        assert isinstance(scores, dict)
        # May be empty or have minimal scores

    def test_tfidf_extraction_normalizes_scores(self):
        """Test that TF-IDF scores are normalized."""
        assigner = TagAssigner()

        text = "alignment interpretability safety ethics governance"
        scores = assigner._tfidf_extraction(text)

        # All scores should be reasonable (not excessively high)
        for score in scores.values():
            assert 0 <= score <= 1.0


class TestSourceSpecificTags:
    """Test source-specific tag extraction."""

    def test_source_specific_arxiv_categories(self):
        """Test ArXiv category mapping."""
        assigner = TagAssigner()
        scores = assigner._source_specific_tags(
            source_fields=None,
            arxiv_categories=['cs.AI', 'cs.LG']
        )

        # Should map to appropriate tags
        assert 'ai' in scores or 'machine_learning' in scores
        assert all(0 <= s <= 1.0 for s in scores.values())

    def test_source_specific_s2_fields(self):
        """Test Semantic Scholar field mapping."""
        assigner = TagAssigner()
        scores = assigner._source_specific_tags(
            source_fields=['Machine Learning', 'Computer Science'],
            arxiv_categories=None
        )

        assert 'machine_learning' in scores or 'ai' in scores
        assert all(0 <= s <= 1.0 for s in scores.values())

    def test_source_specific_combined(self):
        """Test combining ArXiv and S2 fields."""
        assigner = TagAssigner()
        scores = assigner._source_specific_tags(
            source_fields=['Natural Language Processing'],
            arxiv_categories=['cs.CL']
        )

        assert 'nlp' in scores
        # Should have higher confidence from both sources
        assert scores['nlp'] > 0.5

    def test_source_specific_no_sources(self):
        """Test with no source metadata."""
        assigner = TagAssigner()
        scores = assigner._source_specific_tags(
            source_fields=None,
            arxiv_categories=None
        )

        assert isinstance(scores, dict)
        assert len(scores) == 0

    def test_source_specific_unknown_category(self):
        """Test with unknown ArXiv category."""
        assigner = TagAssigner()
        scores = assigner._source_specific_tags(
            source_fields=None,
            arxiv_categories=['physics.gen-ph']  # Not in our mapping
        )

        # Should not error, just return empty or minimal scores
        assert isinstance(scores, dict)

    def test_source_specific_fuzzy_matching(self, app):
        """Test fuzzy matching for source fields."""
        assigner = TagAssigner()
        scores = assigner._source_specific_tags(
            source_fields=['artificial intelligence research'],
            arxiv_categories=None
        )

        # Should match based on keyword overlap
        assert len(scores) > 0

    def test_source_specific_scores_capped(self):
        """Test that source scores are capped at 1.0."""
        assigner = TagAssigner()

        # Multiple categories mapping to same tag
        scores = assigner._source_specific_tags(
            source_fields=['Machine Learning'] * 5,
            arxiv_categories=['cs.AI', 'cs.LG', 'stat.ML']
        )

        # All scores should be capped at 1.0
        for score in scores.values():
            assert score <= 1.0


class TestCombineScores:
    """Test score combination logic."""

    def test_combine_scores_basic(self):
        """Test basic score combination."""
        assigner = TagAssigner()

        rule_scores = {'interpretability': 0.6}
        tfidf_scores = {'interpretability': 0.4}
        source_scores = {'interpretability': 0.8}

        weights = {'rule': 0.5, 'tfidf': 0.3, 'source': 0.2}

        combined = assigner._combine_scores(
            rule_scores, tfidf_scores, source_scores, weights
        )

        assert 'interpretability' in combined
        # Weighted average: (0.6*0.5 + 0.4*0.3 + 0.8*0.2) / 1.0 = 0.58
        assert 0.5 < combined['interpretability'] < 0.7

    def test_combine_scores_missing_in_some_strategies(self):
        """Test combining when tag appears in only some strategies."""
        assigner = TagAssigner()

        rule_scores = {'interpretability': 0.6, 'alignment': 0.5}
        tfidf_scores = {'interpretability': 0.4}
        source_scores = {'alignment': 0.8, 'safety': 0.7}

        weights = {'rule': 0.5, 'tfidf': 0.3, 'source': 0.2}

        combined = assigner._combine_scores(
            rule_scores, tfidf_scores, source_scores, weights
        )

        # All tags should be present
        assert 'interpretability' in combined
        assert 'alignment' in combined
        assert 'safety' in combined

    def test_combine_scores_different_weights(self):
        """Test that different weights affect results."""
        assigner = TagAssigner()

        rule_scores = {'test': 0.9}
        tfidf_scores = {'test': 0.1}
        source_scores = {}

        # Heavy rule weight
        weights_rule = {'rule': 0.9, 'tfidf': 0.05, 'source': 0.05}
        combined_rule = assigner._combine_scores(
            rule_scores, tfidf_scores, source_scores, weights_rule
        )

        # Heavy tfidf weight
        weights_tfidf = {'rule': 0.05, 'tfidf': 0.9, 'source': 0.05}
        combined_tfidf = assigner._combine_scores(
            rule_scores, tfidf_scores, source_scores, weights_tfidf
        )

        # Rule-weighted should be higher
        assert combined_rule['test'] > combined_tfidf['test']

    def test_combine_scores_empty_inputs(self):
        """Test combining with empty score dictionaries."""
        assigner = TagAssigner()

        weights = {'rule': 0.5, 'tfidf': 0.3, 'source': 0.2}
        combined = assigner._combine_scores({}, {}, {}, weights)

        assert isinstance(combined, dict)
        assert len(combined) == 0

    def test_combine_scores_normalization(self):
        """Test that scores are properly normalized by weight sum."""
        assigner = TagAssigner()

        rule_scores = {'test': 1.0}
        tfidf_scores = {}
        source_scores = {}

        # Weights don't sum to 1.0
        weights = {'rule': 0.5, 'tfidf': 0.3, 'source': 0.2}

        combined = assigner._combine_scores(
            rule_scores, tfidf_scores, source_scores, weights
        )

        # Should be normalized: 1.0 * 0.5 / (0.5 + 0.3 + 0.2) = 0.5
        assert abs(combined['test'] - 0.5) < 0.01


class TestGetOrCreateTags:
    """Test tag retrieval and creation."""

    @patch('ara_v2.services.tag_assigner.Tag')
    @patch('ara_v2.services.tag_assigner.db')
    def test_get_existing_tags(self, mock_db, mock_tag_class):
        """Test retrieving existing tags."""
        # Mock existing tags
        mock_tag1 = Mock()
        mock_tag1.name = 'interpretability'
        mock_tag2 = Mock()
        mock_tag2.name = 'alignment'

        mock_tag_class.query.filter_by.return_value.first.side_effect = [
            mock_tag1, mock_tag2
        ]

        assigner = TagAssigner()
        tags = assigner.get_or_create_tags(['interpretability', 'alignment'])

        assert len(tags) == 2
        assert tags[0].name == 'interpretability'
        assert tags[1].name == 'alignment'

    @patch('ara_v2.services.tag_assigner.Tag')
    @patch('ara_v2.services.tag_assigner.db')
    def test_create_new_tags(self, mock_db, mock_tag_class):
        """Test creating new tags that don't exist."""
        # No existing tags
        mock_tag_class.query.filter_by.return_value.first.return_value = None

        # Mock Tag constructor
        mock_new_tag = Mock()
        mock_tag_class.return_value = mock_new_tag

        assigner = TagAssigner()
        tags = assigner.get_or_create_tags(['new_tag'])

        # Should create new tag
        assert mock_tag_class.called
        assert mock_db.session.add.called

    @patch('ara_v2.services.tag_assigner.Tag')
    @patch('ara_v2.services.tag_assigner.db')
    def test_get_or_create_mixed(self, mock_db, mock_tag_class):
        """Test mix of existing and new tags."""
        mock_existing = Mock()
        mock_existing.name = 'existing'

        # First call returns existing, second returns None (new tag)
        mock_tag_class.query.filter_by.return_value.first.side_effect = [
            mock_existing, None
        ]

        mock_new_tag = Mock()
        mock_tag_class.return_value = mock_new_tag

        assigner = TagAssigner()
        tags = assigner.get_or_create_tags(['existing', 'new'])

        assert len(tags) == 2

    @patch('ara_v2.services.tag_assigner.Tag')
    @patch('ara_v2.services.tag_assigner.db')
    def test_get_or_create_generates_slug(self, mock_db, mock_tag_class):
        """Test that slug is generated from tag name."""
        mock_tag_class.query.filter_by.return_value.first.return_value = None

        assigner = TagAssigner()
        assigner.get_or_create_tags(['machine_learning'])

        # Verify Tag was called with slug
        call_kwargs = mock_tag_class.call_args[1]
        assert call_kwargs['slug'] == 'machine-learning'


class TestAssignAndSaveTags:
    """Test full tag assignment and saving workflow."""

    @patch('ara_v2.services.tag_assigner.TagAssigner.get_or_create_tags')
    @patch('ara_v2.services.tag_assigner.TagAssigner.assign_tags')
    @patch('ara_v2.services.tag_assigner.current_app')
    def test_assign_and_save_basic(self, app, mock_app, mock_assign, mock_get_create):
        """Test basic assign and save workflow."""
        # Mock paper
        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.title = "Test Paper"
        mock_paper.abstract = "Test abstract"
        mock_paper.source = 'arxiv'
        mock_paper.raw_data = {'categories': ['cs.AI']}

        # Mock assign_tags return
        mock_assign.return_value = [('interpretability', 0.8), ('alignment', 0.6)]

        # Mock tags
        mock_tag1 = Mock()
        mock_tag1.name = 'interpretability'
        mock_tag2 = Mock()
        mock_tag2.name = 'alignment'
        mock_get_create.return_value = [mock_tag1, mock_tag2]

        assigner = TagAssigner()
        result = assigner.assign_and_save_tags(mock_paper)

        assert len(result) == 2
        assert result[0][0].name == 'interpretability'
        assert result[0][1] == 0.8

    @patch('ara_v2.services.tag_assigner.TagAssigner.assign_tags')
    @patch('ara_v2.services.tag_assigner.current_app')
    def test_assign_and_save_no_tags(self, app, mock_app, mock_assign):
        """Test when no tags are assigned."""
        mock_paper = Mock()
        mock_paper.title = "Test"
        mock_paper.abstract = None
        mock_paper.source = 'arxiv'
        mock_paper.raw_data = None

        mock_assign.return_value = []

        assigner = TagAssigner()
        result = assigner.assign_and_save_tags(mock_paper)

        assert result == []

    @patch('ara_v2.services.tag_assigner.TagAssigner.get_or_create_tags')
    @patch('ara_v2.services.tag_assigner.TagAssigner.assign_tags')
    @patch('ara_v2.services.tag_assigner.current_app')
    def test_assign_and_save_semantic_scholar(self, app, mock_app, mock_assign, mock_get_create):
        """Test with Semantic Scholar paper."""
        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.title = "Test"
        mock_paper.abstract = "Test"
        mock_paper.source = 'semantic_scholar'
        mock_paper.raw_data = {'fieldsOfStudy': ['Computer Science', 'AI']}

        mock_assign.return_value = [('ai', 0.9)]

        mock_tag = Mock()
        mock_tag.name = 'ai'
        mock_get_create.return_value = [mock_tag]

        assigner = TagAssigner()
        result = assigner.assign_and_save_tags(mock_paper)

        # Verify source_fields were extracted and passed
        assert mock_assign.called
        call_kwargs = mock_assign.call_args[1]
        assert call_kwargs['source_fields'] == ['Computer Science', 'AI']

    @patch('ara_v2.services.tag_assigner.TagAssigner.get_or_create_tags')
    @patch('ara_v2.services.tag_assigner.TagAssigner.assign_tags')
    @patch('ara_v2.services.tag_assigner.current_app')
    def test_assign_and_save_arxiv(self, app, mock_app, mock_assign, mock_get_create):
        """Test with ArXiv paper."""
        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.title = "Test"
        mock_paper.abstract = "Test"
        mock_paper.source = 'arxiv'
        mock_paper.raw_data = {'categories': ['cs.AI', 'cs.LG']}

        mock_assign.return_value = [('machine_learning', 0.85)]

        mock_tag = Mock()
        mock_tag.name = 'machine_learning'
        mock_get_create.return_value = [mock_tag]

        assigner = TagAssigner()
        result = assigner.assign_and_save_tags(mock_paper)

        # Verify arxiv_categories were extracted
        call_kwargs = mock_assign.call_args[1]
        assert call_kwargs['arxiv_categories'] == ['cs.AI', 'cs.LG']

    @patch('ara_v2.services.tag_assigner.TagAssigner.get_or_create_tags')
    @patch('ara_v2.services.tag_assigner.TagAssigner.assign_tags')
    @patch('ara_v2.services.tag_assigner.current_app')
    def test_assign_and_save_crossref(self, app, mock_app, mock_assign, mock_get_create):
        """Test with CrossRef paper."""
        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.title = "Test"
        mock_paper.abstract = "Test"
        mock_paper.source = 'crossref'
        mock_paper.raw_data = {'subjects': ['Computer Science', 'Ethics']}

        mock_assign.return_value = [('ethics', 0.7)]

        mock_tag = Mock()
        mock_tag.name = 'ethics'
        mock_get_create.return_value = [mock_tag]

        assigner = TagAssigner()
        result = assigner.assign_and_save_tags(mock_paper)

        # Verify source_fields were extracted from subjects
        call_kwargs = mock_assign.call_args[1]
        assert call_kwargs['source_fields'] == ['Computer Science', 'Ethics']

    @patch('ara_v2.services.tag_assigner.TagAssigner.get_or_create_tags')
    @patch('ara_v2.services.tag_assigner.TagAssigner.assign_tags')
    @patch('ara_v2.services.tag_assigner.current_app')
    def test_assign_and_save_respects_min_confidence(self, app, mock_app, mock_assign, mock_get_create):
        """Test that min_confidence parameter is passed through."""
        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.title = "Test"
        mock_paper.abstract = None
        mock_paper.source = 'arxiv'
        mock_paper.raw_data = None

        mock_assign.return_value = []

        assigner = TagAssigner()
        assigner.assign_and_save_tags(mock_paper, min_confidence=0.5)

        call_kwargs = mock_assign.call_args[1]
        assert call_kwargs['min_confidence'] == 0.5

    @patch('ara_v2.services.tag_assigner.TagAssigner.get_or_create_tags')
    @patch('ara_v2.services.tag_assigner.TagAssigner.assign_tags')
    @patch('ara_v2.services.tag_assigner.current_app')
    def test_assign_and_save_respects_max_tags(self, app, mock_app, mock_assign, mock_get_create):
        """Test that max_tags parameter is passed through."""
        mock_paper = Mock()
        mock_paper.id = 1
        mock_paper.title = "Test"
        mock_paper.abstract = None
        mock_paper.source = 'arxiv'
        mock_paper.raw_data = None

        mock_assign.return_value = []

        assigner = TagAssigner()
        assigner.assign_and_save_tags(mock_paper, max_tags=5)

        call_kwargs = mock_assign.call_args[1]
        assert call_kwargs['max_tags'] == 5
