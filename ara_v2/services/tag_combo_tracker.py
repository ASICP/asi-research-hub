"""
Tag Combo Tracker for ARA v2.
Tracks tag combinations to detect novel research area intersections.
"""

from typing import List, Set, Tuple
from datetime import datetime
from flask import current_app
from sqlalchemy import func
from ara_v2.utils.database import db
from ara_v2.models.tag import Tag, TagCombo
from ara_v2.models.paper import Paper
from ara_v2.models.paper_tag import PaperTag


class TagComboTracker:
    """
    Track and detect novel tag combinations.

    A tag combination is considered "novel" if it appears in <= 3 papers.
    This helps identify papers at the intersection of multiple research areas.
    """

    # Threshold for considering a combo "novel"
    NOVEL_THRESHOLD = 3

    def track_paper_tag_combinations(self, paper_id: int) -> dict:
        """
        Track all 2-tag combinations for a paper.

        Args:
            paper_id: ID of the paper

        Returns:
            dict: {
                'combos_tracked': int,
                'novel_combos': int,
                'new_combos': int
            }
        """
        paper = db.session.query(Paper).get(paper_id)
        if not paper:
            current_app.logger.error(f"Paper {paper_id} not found for combo tracking")
            return {'combos_tracked': 0, 'novel_combos': 0, 'new_combos': 0}

        # Get all tag IDs for this paper
        tag_ids = [pt.tag_id for pt in paper.tags]

        if len(tag_ids) < 2:
            current_app.logger.debug(f"Paper {paper_id} has < 2 tags, no combos to track")
            return {'combos_tracked': 0, 'novel_combos': 0, 'new_combos': 0}

        # Generate all 2-tag combinations
        combinations = self._generate_tag_pairs(tag_ids)

        stats = {
            'combos_tracked': 0,
            'novel_combos': 0,
            'new_combos': 0
        }

        # Track each combination
        for combo_tag_ids in combinations:
            is_new, is_novel = self._track_tag_combo(combo_tag_ids, paper_id)

            stats['combos_tracked'] += 1
            if is_new:
                stats['new_combos'] += 1
            if is_novel:
                stats['novel_combos'] += 1

        # Update PaperTag is_novel_combo flags
        if stats['novel_combos'] > 0:
            self._update_paper_tag_novel_flags(paper_id, combinations)

        current_app.logger.info(
            f"Tracked {stats['combos_tracked']} combos for paper {paper_id}: "
            f"{stats['new_combos']} new, {stats['novel_combos']} novel"
        )

        return stats

    def _generate_tag_pairs(self, tag_ids: List[int]) -> List[List[int]]:
        """
        Generate all unique 2-tag combinations.

        Args:
            tag_ids: List of tag IDs

        Returns:
            list: List of sorted tag ID pairs
        """
        pairs = []

        for i in range(len(tag_ids)):
            for j in range(i + 1, len(tag_ids)):
                # Sort the pair (required by database constraint)
                pair = sorted([tag_ids[i], tag_ids[j]])
                pairs.append(pair)

        return pairs

    def _track_tag_combo(
        self,
        tag_ids: List[int],
        paper_id: int
    ) -> Tuple[bool, bool]:
        """
        Track a single tag combination.

        Args:
            tag_ids: Sorted list of 2 tag IDs
            paper_id: ID of the paper with this combo

        Returns:
            tuple: (is_new, is_novel)
        """
        # Check if combo exists
        existing_combo = (
            db.session.query(TagCombo)
            .filter(TagCombo.tag_ids == tag_ids)
            .first()
        )

        if existing_combo:
            # Increment frequency
            existing_combo.frequency += 1

            # Check if still novel (frequency <= threshold)
            is_novel = existing_combo.frequency <= self.NOVEL_THRESHOLD

            current_app.logger.debug(
                f"Updated combo {tag_ids}: freq={existing_combo.frequency}, "
                f"novel={is_novel}"
            )

            return False, is_novel

        else:
            # Create new combo
            new_combo = TagCombo(
                tag_ids=tag_ids,
                frequency=1,
                first_paper_id=paper_id,
                is_novel=True  # New combos are always novel
            )
            db.session.add(new_combo)
            db.session.flush()

            current_app.logger.info(
                f"Created new tag combo {tag_ids} from paper {paper_id}"
            )

            return True, True

    def _update_paper_tag_novel_flags(
        self,
        paper_id: int,
        combinations: List[List[int]]
    ):
        """
        Update is_novel_combo flags for PaperTag entries.

        Args:
            paper_id: ID of the paper
            combinations: List of tag ID pairs for this paper
        """
        # Get all paper_tags for this paper
        paper_tags = (
            db.session.query(PaperTag)
            .filter(PaperTag.paper_id == paper_id)
            .all()
        )

        # For each paper_tag, check if it's part of any novel combo
        for pt in paper_tags:
            is_in_novel_combo = False

            # Check all combinations that include this tag
            for combo_tag_ids in combinations:
                if pt.tag_id in combo_tag_ids:
                    # Check if this combo is novel
                    combo = (
                        db.session.query(TagCombo)
                        .filter(TagCombo.tag_ids == combo_tag_ids)
                        .first()
                    )

                    if combo and combo.frequency <= self.NOVEL_THRESHOLD:
                        is_in_novel_combo = True
                        break

            pt.is_novel_combo = is_in_novel_combo

    def get_novel_combinations(
        self,
        limit: int = 50,
        min_frequency: int = 1
    ) -> List[dict]:
        """
        Get novel tag combinations.

        Args:
            limit: Maximum number of combos to return
            min_frequency: Minimum frequency (default 1)

        Returns:
            list: List of novel combo dictionaries
        """
        novel_combos = (
            db.session.query(TagCombo)
            .filter(
                TagCombo.frequency <= self.NOVEL_THRESHOLD,
                TagCombo.frequency >= min_frequency
            )
            .order_by(TagCombo.created_at.desc())
            .limit(limit)
            .all()
        )

        results = []
        for combo in novel_combos:
            # Get tag names
            tags = (
                db.session.query(Tag)
                .filter(Tag.id.in_(combo.tag_ids))
                .all()
            )
            tag_names = [t.name for t in tags]

            results.append({
                'tag_ids': combo.tag_ids,
                'tag_names': tag_names,
                'frequency': combo.frequency,
                'first_paper_id': combo.first_paper_id,
                'created_at': combo.created_at.isoformat() if combo.created_at else None
            })

        return results

    def get_popular_combinations(
        self,
        limit: int = 50,
        min_frequency: int = 5
    ) -> List[dict]:
        """
        Get popular tag combinations.

        Args:
            limit: Maximum number of combos to return
            min_frequency: Minimum frequency

        Returns:
            list: List of popular combo dictionaries
        """
        popular_combos = (
            db.session.query(TagCombo)
            .filter(TagCombo.frequency >= min_frequency)
            .order_by(TagCombo.frequency.desc())
            .limit(limit)
            .all()
        )

        results = []
        for combo in popular_combos:
            # Get tag names
            tags = (
                db.session.query(Tag)
                .filter(Tag.id.in_(combo.tag_ids))
                .all()
            )
            tag_names = [t.name for t in tags]

            results.append({
                'tag_ids': combo.tag_ids,
                'tag_names': tag_names,
                'frequency': combo.frequency,
                'first_paper_id': combo.first_paper_id,
                'is_novel': combo.frequency <= self.NOVEL_THRESHOLD
            })

        return results

    def is_novel_combination(self, tag_ids: List[int]) -> bool:
        """
        Check if a tag combination is novel.

        Args:
            tag_ids: List of tag IDs (will be sorted)

        Returns:
            bool: True if novel (frequency <= threshold)
        """
        # Sort tag IDs
        sorted_ids = sorted(tag_ids)

        # Check frequency
        combo = (
            db.session.query(TagCombo)
            .filter(TagCombo.tag_ids == sorted_ids)
            .first()
        )

        if not combo:
            return True  # New combination is novel

        return combo.frequency <= self.NOVEL_THRESHOLD

    def get_paper_novel_combos(self, paper_id: int) -> List[dict]:
        """
        Get all novel tag combinations for a paper.

        Args:
            paper_id: ID of the paper

        Returns:
            list: List of novel combo dictionaries
        """
        paper = db.session.query(Paper).get(paper_id)
        if not paper:
            return []

        tag_ids = [pt.tag_id for pt in paper.tags]
        if len(tag_ids) < 2:
            return []

        combinations = self._generate_tag_pairs(tag_ids)
        novel_combos = []

        for combo_tag_ids in combinations:
            if self.is_novel_combination(combo_tag_ids):
                # Get tag names
                tags = (
                    db.session.query(Tag)
                    .filter(Tag.id.in_(combo_tag_ids))
                    .all()
                )
                tag_names = [t.name for t in tags]

                # Get combo info
                combo = (
                    db.session.query(TagCombo)
                    .filter(TagCombo.tag_ids == combo_tag_ids)
                    .first()
                )

                novel_combos.append({
                    'tag_ids': combo_tag_ids,
                    'tag_names': tag_names,
                    'frequency': combo.frequency if combo else 1
                })

        return novel_combos


# Convenience functions
def track_paper_tag_combinations(paper_id: int) -> dict:
    """
    Convenience function to track tag combinations for a paper.

    Args:
        paper_id: ID of the paper

    Returns:
        dict: Tracking statistics
    """
    tracker = TagComboTracker()
    return tracker.track_paper_tag_combinations(paper_id)


def is_novel_combination(tag_ids: List[int]) -> bool:
    """
    Convenience function to check if a tag combination is novel.

    Args:
        tag_ids: List of tag IDs

    Returns:
        bool: True if novel
    """
    tracker = TagComboTracker()
    return tracker.is_novel_combination(tag_ids)


def get_novel_combinations(limit: int = 50) -> List[dict]:
    """
    Convenience function to get novel tag combinations.

    Args:
        limit: Maximum number to return

    Returns:
        list: Novel combinations
    """
    tracker = TagComboTracker()
    return tracker.get_novel_combinations(limit)
