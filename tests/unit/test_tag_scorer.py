"""
Unit tests for Tag Scorer service.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from ara_v2.services.scoring.tag_scorer import TagScorer, calculate_tag_score, update_tag_statistics
from ara_v2.models.paper import Paper
from ara_v2.models.tag import Tag
from ara_v2.models.paper_tag import PaperTag


class TestTagScorer:
    """Test suite for TagScorer class."""

    def test_calculate_tag_score_no_tags(self, app, db):
        """Test scoring a paper with no tags returns 0."""
        with app.app_context():
            # Create paper without tags
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            scorer = TagScorer()
            score = scorer.calculate_tag_score(paper.id)

            assert score == 0.0

    def test_calculate_tag_score_single_tag(self, app, db):
        """Test scoring with a single tag."""
        with app.app_context():
            # Create tag
            tag = Tag(
                name="interpretability",
                frequency=100,
                first_seen=datetime.utcnow() - timedelta(days=365),
                last_seen=datetime.utcnow() - timedelta(days=30),
                growth_rate=Decimal("8.33")  # 100/12 months
            )
            db.session.add(tag)

            # Create paper
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            # Associate tag with paper
            paper_tag = PaperTag(
                paper_id=paper.id,
                tag_id=tag.id
            )
            db.session.add(paper_tag)
            db.session.commit()

            scorer = TagScorer()
            score = scorer.calculate_tag_score(paper.id)

            # Score should be > 0 and <= 100
            assert 0 < score <= 100

    def test_calculate_tag_score_multiple_tags(self, app, db):
        """Test scoring with multiple tags."""
        with app.app_context():
            # Create multiple tags with different characteristics
            tags = [
                Tag(
                    name="alignment",
                    frequency=150,
                    first_seen=datetime.utcnow() - timedelta(days=365),
                    last_seen=datetime.utcnow() - timedelta(days=10),
                    growth_rate=Decimal("12.5")
                ),
                Tag(
                    name="rlhf",
                    frequency=80,
                    first_seen=datetime.utcnow() - timedelta(days=180),
                    last_seen=datetime.utcnow() - timedelta(days=5),
                    growth_rate=Decimal("13.33")
                ),
                Tag(
                    name="safety",
                    frequency=200,
                    first_seen=datetime.utcnow() - timedelta(days=730),
                    last_seen=datetime.utcnow() - timedelta(days=60),
                    growth_rate=Decimal("8.22")
                ),
            ]
            for tag in tags:
                db.session.add(tag)

            # Create paper
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            # Associate all tags with paper
            for tag in tags:
                paper_tag = PaperTag(
                    paper_id=paper.id,
                    tag_id=tag.id
                )
                db.session.add(paper_tag)
            db.session.commit()

            scorer = TagScorer()
            score = scorer.calculate_tag_score(paper.id)

            # Multiple tags should give higher score
            assert 0 < score <= 100

    def test_tag_weight_calculation_with_high_frequency(self, app, db):
        """Test that high-frequency tags get higher weights."""
        with app.app_context():
            high_freq_tag = Tag(
                name="popular_tag",
                frequency=500,
                first_seen=datetime.utcnow() - timedelta(days=365),
                last_seen=datetime.utcnow() - timedelta(days=10),
                growth_rate=Decimal("41.67")
            )
            db.session.add(high_freq_tag)
            db.session.commit()

            scorer = TagScorer()
            weight = scorer._calculate_tag_weight(high_freq_tag)

            # High frequency should result in high weight
            assert weight > 500  # At least the base frequency

    def test_tag_weight_calculation_with_high_growth(self, app, db):
        """Test that fast-growing tags get bonus weight."""
        with app.app_context():
            growing_tag = Tag(
                name="trending_tag",
                frequency=50,
                first_seen=datetime.utcnow() - timedelta(days=60),
                last_seen=datetime.utcnow() - timedelta(days=1),
                growth_rate=Decimal("25.0")  # Very high growth rate
            )
            db.session.add(growing_tag)
            db.session.commit()

            scorer = TagScorer()
            weight = scorer._calculate_tag_weight(growing_tag)

            # Growth bonus should apply (1.0 + max(0, 25.0 * 2)) = 51.0
            expected_min_weight = 50 * 51.0 * 0.9  # freq * growth_bonus * min_recency
            assert weight > expected_min_weight

    def test_tag_weight_recency_decay(self, app, db):
        """Test that old tags get lower weight due to recency decay."""
        with app.app_context():
            old_tag = Tag(
                name="old_tag",
                frequency=100,
                first_seen=datetime.utcnow() - timedelta(days=730),
                last_seen=datetime.utcnow() - timedelta(days=365),  # Last seen 1 year ago
                growth_rate=Decimal("4.11")
            )
            db.session.add(old_tag)

            recent_tag = Tag(
                name="recent_tag",
                frequency=100,
                first_seen=datetime.utcnow() - timedelta(days=60),
                last_seen=datetime.utcnow() - timedelta(days=5),
                growth_rate=Decimal("50.0")
            )
            db.session.add(recent_tag)
            db.session.commit()

            scorer = TagScorer()
            old_weight = scorer._calculate_tag_weight(old_tag)
            recent_weight = scorer._calculate_tag_weight(recent_tag)

            # Recent tag should have higher weight due to recency
            assert recent_weight > old_weight

    def test_months_between(self, app):
        """Test months calculation."""
        with app.app_context():
            scorer = TagScorer()

            start = datetime(2024, 1, 1)
            end = datetime(2024, 7, 1)

            months = scorer._months_between(start, end)

            # Should be approximately 6 months
            assert 5.5 < months < 6.5

    def test_update_tag_statistics_new_tag(self, app, db):
        """Test updating statistics for a newly created tag."""
        with app.app_context():
            tag = Tag(
                name="new_tag",
                frequency=1
            )
            db.session.add(tag)
            db.session.commit()

            # Update statistics
            scorer = TagScorer()
            scorer.update_tag_statistics(tag.id)

            # Refresh tag from database
            db.session.refresh(tag)

            # first_seen and last_seen should be set
            assert tag.first_seen is not None
            assert tag.last_seen is not None
            assert tag.growth_rate is not None
            assert tag.growth_rate > 0

    def test_update_tag_statistics_existing_tag(self, app, db):
        """Test updating statistics for an existing tag."""
        with app.app_context():
            old_time = datetime.utcnow() - timedelta(days=365)
            tag = Tag(
                name="existing_tag",
                frequency=120,
                first_seen=old_time,
                last_seen=old_time,
                growth_rate=Decimal("0.0")
            )
            db.session.add(tag)
            db.session.commit()

            original_last_seen = tag.last_seen

            # Update statistics
            scorer = TagScorer()
            scorer.update_tag_statistics(tag.id)

            # Refresh tag from database
            db.session.refresh(tag)

            # last_seen should be updated
            assert tag.last_seen > original_last_seen
            # growth_rate should be calculated (freq / months since first_seen)
            assert tag.growth_rate > 0

    def test_cache_invalidation(self, app, db):
        """Test that cache can be invalidated."""
        with app.app_context():
            scorer = TagScorer()

            # Set some cache values
            scorer._max_weight_cache = 100.0
            scorer._cache_timestamp = datetime.utcnow()

            # Invalidate cache
            scorer.invalidate_cache()

            assert scorer._max_weight_cache is None
            assert scorer._cache_timestamp is None

    def test_max_weight_caching(self, app, db):
        """Test that max weight is cached properly."""
        with app.app_context():
            # Create some tags
            for i in range(10):
                tag = Tag(
                    name=f"tag_{i}",
                    frequency=100 + i * 10,
                    first_seen=datetime.utcnow() - timedelta(days=365),
                    last_seen=datetime.utcnow() - timedelta(days=30),
                    growth_rate=Decimal("8.33")
                )
                db.session.add(tag)
            db.session.commit()

            scorer = TagScorer()

            # First call should calculate and cache
            max_weight_1 = scorer._get_max_tag_weight()
            timestamp_1 = scorer._cache_timestamp

            # Second call should use cache
            max_weight_2 = scorer._get_max_tag_weight()
            timestamp_2 = scorer._cache_timestamp

            assert max_weight_1 == max_weight_2
            assert timestamp_1 == timestamp_2

    def test_convenience_function_calculate_tag_score(self, app, db):
        """Test the convenience function for calculating tag score."""
        with app.app_context():
            # Create tag and paper
            tag = Tag(
                name="test_tag",
                frequency=100,
                first_seen=datetime.utcnow() - timedelta(days=365),
                last_seen=datetime.utcnow() - timedelta(days=30),
                growth_rate=Decimal("8.33")
            )
            db.session.add(tag)

            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            paper_tag = PaperTag(
                paper_id=paper.id,
                tag_id=tag.id
            )
            db.session.add(paper_tag)
            db.session.commit()

            # Use convenience function
            score = calculate_tag_score(paper.id)

            assert isinstance(score, float)
            assert 0 <= score <= 100

    def test_convenience_function_update_tag_statistics(self, app, db):
        """Test the convenience function for updating tag statistics."""
        with app.app_context():
            tag = Tag(
                name="test_tag",
                frequency=50
            )
            db.session.add(tag)
            db.session.commit()

            # Use convenience function
            update_tag_statistics(tag.id)

            # Refresh tag
            db.session.refresh(tag)

            assert tag.first_seen is not None
            assert tag.last_seen is not None
            assert tag.growth_rate is not None

    def test_score_with_no_last_seen(self, app, db):
        """Test scoring when tag has no last_seen timestamp."""
        with app.app_context():
            tag = Tag(
                name="tag_no_timestamp",
                frequency=100,
                first_seen=datetime.utcnow(),
                last_seen=None,  # No last_seen
                growth_rate=Decimal("100.0")
            )
            db.session.add(tag)

            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            paper_tag = PaperTag(
                paper_id=paper.id,
                tag_id=tag.id
            )
            db.session.add(paper_tag)
            db.session.commit()

            scorer = TagScorer()
            score = scorer.calculate_tag_score(paper.id)

            # Should handle None last_seen gracefully
            assert 0 < score <= 100

    def test_score_normalized_to_100(self, app, db):
        """Test that scores are capped at 100."""
        with app.app_context():
            # Create many high-value tags
            for i in range(20):
                tag = Tag(
                    name=f"high_value_tag_{i}",
                    frequency=1000,
                    first_seen=datetime.utcnow() - timedelta(days=60),
                    last_seen=datetime.utcnow() - timedelta(days=1),
                    growth_rate=Decimal("500.0")  # Very high growth
                )
                db.session.add(tag)

            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            # Add all tags to paper
            tags = Tag.query.all()
            for tag in tags:
                paper_tag = PaperTag(
                    paper_id=paper.id,
                    tag_id=tag.id
                )
                db.session.add(paper_tag)
            db.session.commit()

            scorer = TagScorer()
            score = scorer.calculate_tag_score(paper.id)

            # Even with many high-value tags, score should be capped at 100
            assert score == 100.0

    def test_score_nonexistent_paper(self, app, db):
        """Test scoring a paper that doesn't exist."""
        with app.app_context():
            scorer = TagScorer()
            score = scorer.calculate_tag_score(99999)

            assert score == 0.0

    def test_update_nonexistent_tag(self, app, db):
        """Test updating statistics for a tag that doesn't exist."""
        with app.app_context():
            scorer = TagScorer()
            # Should not raise an exception
            scorer.update_tag_statistics(99999)
