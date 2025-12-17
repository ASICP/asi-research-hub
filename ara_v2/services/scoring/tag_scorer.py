"""
Tag Score calculation for ARA v2.
Measures how well a paper aligns with popular, active research areas based on its tags.
"""

import math
from datetime import datetime
from typing import Optional
from flask import current_app
from ara_v2.utils.database import db
from ara_v2.models.tag import Tag
from ara_v2.models.paper import Paper


class TagScorer:
    """
    Calculate Tag Score for papers based on tag relevance and popularity.

    Formula:
    TagScore = Σ(tag_weight_i) / max_possible_weight * 100

    Where tag_weight = frequency * recency_multiplier * growth_bonus
    """

    def __init__(self):
        """Initialize the tag scorer."""
        self._max_weight_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 3600  # Cache max weight for 1 hour

    def calculate_tag_score(self, paper_id: int) -> float:
        """
        Calculate Tag Score for a paper (0-100 scale).

        Args:
            paper_id: ID of the paper to score

        Returns:
            float: Tag score between 0 and 100
        """
        # Get paper with tags
        paper = db.session.query(Paper).get(paper_id)
        if not paper:
            current_app.logger.error(f"Paper {paper_id} not found for tag scoring")
            return 0.0

        # Get tags for this paper
        paper_tags = [pt.tag for pt in paper.tags]

        if not paper_tags:
            current_app.logger.info(f"Paper {paper_id} has no tags, score = 0")
            return 0.0

        # Calculate total weight
        total_weight = 0.0

        for tag in paper_tags:
            tag_weight = self._calculate_tag_weight(tag)
            total_weight += tag_weight

            current_app.logger.debug(
                f"Tag '{tag.name}' weight: {tag_weight:.4f} "
                f"(freq={tag.frequency}, growth={tag.growth_rate})"
            )

        # Normalize against maximum possible weight
        max_weight = self._get_max_tag_weight()

        if max_weight == 0:
            current_app.logger.warning("Max tag weight is 0, returning 0 score")
            return 0.0

        raw_score = (total_weight / max_weight) * 100

        # Cap at 100
        final_score = min(100.0, raw_score)

        current_app.logger.info(
            f"Paper {paper_id} tag score: {final_score:.2f} "
            f"(total_weight={total_weight:.2f}, max_weight={max_weight:.2f})"
        )

        return round(final_score, 2)

    def _calculate_tag_weight(self, tag: Tag) -> float:
        """
        Calculate weight for a single tag.

        Args:
            tag: Tag model instance

        Returns:
            float: Weight value
        """
        # Base weight = tag frequency
        base_weight = tag.frequency or 0

        # Recency multiplier: exponential decay from last_seen
        if tag.last_seen:
            months_since_active = self._months_between(tag.last_seen, datetime.utcnow())
            recency_multiplier = math.exp(-0.1 * months_since_active)
        else:
            # If last_seen is None, assume it's recent
            recency_multiplier = 1.0

        # Growth bonus: rapidly growing tags get boost
        growth_rate = tag.growth_rate or 0.0
        growth_bonus = 1.0 + max(0, float(growth_rate) * 2)

        tag_weight = base_weight * recency_multiplier * growth_bonus

        return tag_weight

    def _get_max_tag_weight(self) -> float:
        """
        Get theoretical maximum tag weight for normalization.

        This is cached to avoid expensive queries on every score calculation.

        Returns:
            float: Maximum possible tag weight
        """
        # Check cache
        now = datetime.utcnow()
        if (self._max_weight_cache is not None and
            self._cache_timestamp is not None):
            elapsed_seconds = (now - self._cache_timestamp).total_seconds()
            if elapsed_seconds < self._cache_ttl:
                return self._max_weight_cache

        # Calculate max weight from top tags
        # Strategy: Take average of top 8 tag weights (typical paper has 3-8 tags)
        top_tags = (
            db.session.query(Tag)
            .filter(Tag.frequency > 0)
            .order_by(Tag.frequency.desc())
            .limit(8)
            .all()
        )

        if not top_tags:
            current_app.logger.warning("No tags found in database for max weight calculation")
            return 1.0  # Avoid division by zero

        # Calculate weights for top tags
        weights = [self._calculate_tag_weight(tag) for tag in top_tags]
        max_weight = sum(weights)

        # Cache the result
        self._max_weight_cache = max_weight
        self._cache_timestamp = now

        current_app.logger.debug(f"Calculated max tag weight: {max_weight:.2f} (cached for {self._cache_ttl}s)")

        return max_weight

    def _months_between(self, start_date: datetime, end_date: datetime) -> float:
        """
        Calculate months between two dates.

        Args:
            start_date: Earlier date
            end_date: Later date

        Returns:
            float: Number of months (can be fractional)
        """
        delta = end_date - start_date
        months = delta.days / 30.44  # Average days per month
        return max(0, months)

    def update_tag_statistics(self, tag_id: int) -> None:
        """
        Update tag frequency and growth metrics.

        This should be called after new papers are tagged.

        Args:
            tag_id: ID of the tag to update
        """
        tag = db.session.query(Tag).get(tag_id)
        if not tag:
            current_app.logger.error(f"Tag {tag_id} not found for statistics update")
            return

        # Frequency is updated via triggers/relationships, but we update growth_rate here

        # Update last_seen
        tag.last_seen = datetime.utcnow()

        # Calculate growth rate (papers per month)
        if tag.first_seen:
            months_since_first = max(1, self._months_between(tag.first_seen, datetime.utcnow()))
            tag.growth_rate = tag.frequency / months_since_first
        else:
            # First time seeing this tag
            tag.first_seen = datetime.utcnow()
            tag.last_seen = datetime.utcnow()
            tag.growth_rate = tag.frequency  # Initial growth rate = frequency

        db.session.commit()

        current_app.logger.info(
            f"Updated tag '{tag.name}' stats: "
            f"freq={tag.frequency}, growth_rate={tag.growth_rate:.4f}"
        )

    def invalidate_cache(self) -> None:
        """Invalidate the max weight cache (e.g., after bulk tag updates)."""
        self._max_weight_cache = None
        self._cache_timestamp = None
        current_app.logger.debug("Tag scorer cache invalidated")


def calculate_tag_score(paper_id: int) -> float:
    """
    Convenience function to calculate tag score.

    Args:
        paper_id: ID of the paper to score

    Returns:
        float: Tag score between 0 and 100
    """
    scorer = TagScorer()
    return scorer.calculate_tag_score(paper_id)


def update_tag_statistics(tag_id: int) -> None:
    """
    Convenience function to update tag statistics.

    Args:
        tag_id: ID of the tag to update
    """
    scorer = TagScorer()
    scorer.update_tag_statistics(tag_id)
