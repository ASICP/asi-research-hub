"""
Unit tests for Tag Combo Tracker service.
"""

import pytest
from ara_v2.services.tag_combo_tracker import (
    TagComboTracker,
    track_paper_tag_combinations,
    is_novel_combination,
    get_novel_combinations
)
from ara_v2.models.paper import Paper
from ara_v2.models.tag import Tag, TagCombo
from ara_v2.models.paper_tag import PaperTag


class TestTagComboTracker:
    """Test suite for TagComboTracker class."""

    def test_track_paper_with_no_tags(self, app, db):
        """Test tracking a paper with no tags."""
        with app.app_context():
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            tracker = TagComboTracker()
            stats = tracker.track_paper_tag_combinations(paper.id)

            assert stats['combos_tracked'] == 0
            assert stats['novel_combos'] == 0
            assert stats['new_combos'] == 0

    def test_track_paper_with_single_tag(self, app, db):
        """Test tracking a paper with only one tag (no combos possible)."""
        with app.app_context():
            tag = Tag(name="alignment", frequency=0)
            db.session.add(tag)

            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            paper_tag = PaperTag(paper_id=paper.id, tag_id=tag.id)
            db.session.add(paper_tag)
            db.session.commit()

            tracker = TagComboTracker()
            stats = tracker.track_paper_tag_combinations(paper.id)

            assert stats['combos_tracked'] == 0

    def test_track_new_combo(self, app, db):
        """Test tracking a brand new tag combination."""
        with app.app_context():
            # Create tags
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])

            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            # Add both tags to paper
            pt1 = PaperTag(paper_id=paper.id, tag_id=tag1.id)
            pt2 = PaperTag(paper_id=paper.id, tag_id=tag2.id)
            db.session.add_all([pt1, pt2])
            db.session.commit()

            tracker = TagComboTracker()
            stats = tracker.track_paper_tag_combinations(paper.id)

            assert stats['combos_tracked'] == 1  # 1 pair
            assert stats['new_combos'] == 1  # Brand new
            assert stats['novel_combos'] == 1  # Novel (freq=1)

            # Check combo was created in database
            combo = db.session.query(TagCombo).filter(
                TagCombo.tag_ids == sorted([tag1.id, tag2.id])
            ).first()

            assert combo is not None
            assert combo.frequency == 1
            assert combo.is_novel is True
            assert combo.first_paper_id == paper.id

    def test_track_existing_combo(self, app, db):
        """Test tracking a combination that already exists."""
        with app.app_context():
            # Create tags
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])
            db.session.commit()

            # Create existing combo
            existing_combo = TagCombo(
                tag_ids=sorted([tag1.id, tag2.id]),
                frequency=2,
                first_paper_id=999,
                is_novel=True
            )
            db.session.add(existing_combo)
            db.session.commit()

            # Create new paper with same combo
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            pt1 = PaperTag(paper_id=paper.id, tag_id=tag1.id)
            pt2 = PaperTag(paper_id=paper.id, tag_id=tag2.id)
            db.session.add_all([pt1, pt2])
            db.session.commit()

            tracker = TagComboTracker()
            stats = tracker.track_paper_tag_combinations(paper.id)

            assert stats['combos_tracked'] == 1
            assert stats['new_combos'] == 0  # Not new
            assert stats['novel_combos'] == 1  # Still novel (freq=3 after update)

            # Check frequency was incremented
            db.session.refresh(existing_combo)
            assert existing_combo.frequency == 3

    def test_combo_becomes_not_novel(self, app, db):
        """Test that combo stops being novel after threshold."""
        with app.app_context():
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])
            db.session.commit()

            # Create combo at threshold
            combo = TagCombo(
                tag_ids=sorted([tag1.id, tag2.id]),
                frequency=3,  # At threshold
                first_paper_id=999,
                is_novel=True
            )
            db.session.add(combo)
            db.session.commit()

            # Add another paper with this combo
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            pt1 = PaperTag(paper_id=paper.id, tag_id=tag1.id)
            pt2 = PaperTag(paper_id=paper.id, tag_id=tag2.id)
            db.session.add_all([pt1, pt2])
            db.session.commit()

            tracker = TagComboTracker()
            stats = tracker.track_paper_tag_combinations(paper.id)

            assert stats['novel_combos'] == 0  # Not novel anymore (freq=4)

            db.session.refresh(combo)
            assert combo.frequency == 4

    def test_generate_tag_pairs(self, app):
        """Test generating all 2-tag combinations."""
        with app.app_context():
            tracker = TagComboTracker()

            # 3 tags should produce 3 pairs
            tag_ids = [1, 2, 3]
            pairs = tracker._generate_tag_pairs(tag_ids)

            assert len(pairs) == 3
            assert sorted(pairs) == [[1, 2], [1, 3], [2, 3]]

            # 4 tags should produce 6 pairs
            tag_ids = [1, 2, 3, 4]
            pairs = tracker._generate_tag_pairs(tag_ids)

            assert len(pairs) == 6

    def test_pairs_are_sorted(self, app):
        """Test that tag pairs are always sorted (for DB constraint)."""
        with app.app_context():
            tracker = TagComboTracker()

            tag_ids = [5, 2, 8, 1]
            pairs = tracker._generate_tag_pairs(tag_ids)

            # All pairs should be sorted
            for pair in pairs:
                assert pair == sorted(pair)

    def test_update_paper_tag_novel_flags(self, app, db):
        """Test updating is_novel_combo flags on PaperTags."""
        with app.app_context():
            # Create tags
            tags = [
                Tag(name="tag1", frequency=0),
                Tag(name="tag2", frequency=0),
                Tag(name="tag3", frequency=0)
            ]
            db.session.add_all(tags)
            db.session.commit()

            # Create paper with 3 tags
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            paper_tags = [
                PaperTag(paper_id=paper.id, tag_id=tags[0].id),
                PaperTag(paper_id=paper.id, tag_id=tags[1].id),
                PaperTag(paper_id=paper.id, tag_id=tags[2].id)
            ]
            db.session.add_all(paper_tags)
            db.session.commit()

            # Track combinations
            tracker = TagComboTracker()
            tracker.track_paper_tag_combinations(paper.id)

            # All paper_tags should be marked as part of novel combo
            for pt in paper_tags:
                db.session.refresh(pt)
                assert pt.is_novel_combo is True

    def test_get_novel_combinations(self, app, db):
        """Test retrieving novel combinations."""
        with app.app_context():
            # Create tags
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            tag3 = Tag(name="safety", frequency=0)
            db.session.add_all([tag1, tag2, tag3])
            db.session.commit()

            # Create some combos
            combo1 = TagCombo(
                tag_ids=[tag1.id, tag2.id],
                frequency=2,  # Novel
                first_paper_id=1,
                is_novel=True
            )
            combo2 = TagCombo(
                tag_ids=[tag2.id, tag3.id],
                frequency=5,  # Not novel
                first_paper_id=2,
                is_novel=False
            )
            db.session.add_all([combo1, combo2])
            db.session.commit()

            tracker = TagComboTracker()
            novel = tracker.get_novel_combinations(limit=10)

            # Should only return combo1
            assert len(novel) == 1
            assert set(novel[0]['tag_names']) == {'alignment', 'interpretability'}
            assert novel[0]['frequency'] == 2

    def test_get_popular_combinations(self, app, db):
        """Test retrieving popular combinations."""
        with app.app_context():
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])
            db.session.commit()

            combo = TagCombo(
                tag_ids=[tag1.id, tag2.id],
                frequency=10,
                first_paper_id=1,
                is_novel=False
            )
            db.session.add(combo)
            db.session.commit()

            tracker = TagComboTracker()
            popular = tracker.get_popular_combinations(limit=10, min_frequency=5)

            assert len(popular) == 1
            assert set(popular[0]['tag_names']) == {'alignment', 'interpretability'}
            assert popular[0]['frequency'] == 10
            assert popular[0]['is_novel'] is False

    def test_is_novel_combination(self, app, db):
        """Test checking if a combination is novel."""
        with app.app_context():
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])
            db.session.commit()

            tracker = TagComboTracker()

            # New combination is novel
            assert tracker.is_novel_combination([tag1.id, tag2.id]) is True

            # Create combo below threshold
            combo = TagCombo(
                tag_ids=sorted([tag1.id, tag2.id]),
                frequency=2,
                first_paper_id=1,
                is_novel=True
            )
            db.session.add(combo)
            db.session.commit()

            # Still novel
            assert tracker.is_novel_combination([tag1.id, tag2.id]) is True

            # Update frequency above threshold
            combo.frequency = 4
            db.session.commit()

            # Not novel anymore
            assert tracker.is_novel_combination([tag1.id, tag2.id]) is False

    def test_get_paper_novel_combos(self, app, db):
        """Test getting novel combos for a specific paper."""
        with app.app_context():
            # Create tags
            tags = [
                Tag(name="tag1", frequency=0),
                Tag(name="tag2", frequency=0),
                Tag(name="tag3", frequency=0)
            ]
            db.session.add_all(tags)
            db.session.commit()

            # Create paper with 3 tags
            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            paper_tags = [
                PaperTag(paper_id=paper.id, tag_id=tags[0].id),
                PaperTag(paper_id=paper.id, tag_id=tags[1].id),
                PaperTag(paper_id=paper.id, tag_id=tags[2].id)
            ]
            db.session.add_all(paper_tags)
            db.session.commit()

            # Track combinations
            tracker = TagComboTracker()
            tracker.track_paper_tag_combinations(paper.id)

            # Get novel combos for this paper
            novel_combos = tracker.get_paper_novel_combos(paper.id)

            # Should have 3 combos (all novel since freq=1)
            assert len(novel_combos) == 3

    def test_convenience_function_track(self, app, db):
        """Test convenience function for tracking."""
        with app.app_context():
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])

            paper = Paper(
                title="Test Paper",
                source="arxiv",
                source_id="2401.00001"
            )
            db.session.add(paper)
            db.session.commit()

            pt1 = PaperTag(paper_id=paper.id, tag_id=tag1.id)
            pt2 = PaperTag(paper_id=paper.id, tag_id=tag2.id)
            db.session.add_all([pt1, pt2])
            db.session.commit()

            # Use convenience function
            stats = track_paper_tag_combinations(paper.id)

            assert stats['combos_tracked'] == 1
            assert stats['new_combos'] == 1

    def test_convenience_function_is_novel(self, app, db):
        """Test convenience function for is_novel."""
        with app.app_context():
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])
            db.session.commit()

            # New combo is novel
            assert is_novel_combination([tag1.id, tag2.id]) is True

    def test_convenience_function_get_novel(self, app, db):
        """Test convenience function for getting novel combos."""
        with app.app_context():
            tag1 = Tag(name="alignment", frequency=0)
            tag2 = Tag(name="interpretability", frequency=0)
            db.session.add_all([tag1, tag2])
            db.session.commit()

            combo = TagCombo(
                tag_ids=[tag1.id, tag2.id],
                frequency=1,
                first_paper_id=1,
                is_novel=True
            )
            db.session.add(combo)
            db.session.commit()

            # Use convenience function
            novel = get_novel_combinations(limit=10)

            assert len(novel) == 1

    def test_nonexistent_paper(self, app, db):
        """Test tracking for a paper that doesn't exist."""
        with app.app_context():
            tracker = TagComboTracker()
            stats = tracker.track_paper_tag_combinations(99999)

            assert stats['combos_tracked'] == 0
