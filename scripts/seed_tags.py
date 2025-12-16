"""
Seed initial tags for ARA v2.
Loads the valid tags from Appendix B of the technical specification.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ara_v2.app import create_app
from ara_v2.models.tag import Tag
from ara_v2.utils.database import db

# Valid tags from Appendix B of the technical specification
VALID_TAGS = [
    # Technical Safety
    'interpretability',
    'mechanistic_interpretability',
    'robustness',
    'adversarial_robustness',
    'alignment',
    'reward_modeling',
    'rlhf',
    'constitutional_ai',
    'scalable_oversight',

    # Governance
    'governance',
    'policy',
    'regulation',
    'ethics',
    'safety_standards',

    # Capabilities
    'scaling',
    'emergent_capabilities',
    'reasoning',
    'multimodal',
    'agents',

    # Evaluation
    'benchmarks',
    'evaluation',
    'red_teaming',
    'auditing',

    # Theory
    'theoretical_alignment',
    'decision_theory',
    'game_theory',
    'formal_verification',

    # Applications
    'healthcare',
    'education',
    'finance',
    'autonomous_systems',

    # Meta
    'survey',
    'foundational',
    'position_paper',

    # Additional common tags
    'ai_safety',
    'machine_learning',
    'deep_learning',
    'neural_networks',
    'transformers',
    'llm',
    'generative_ai',
]


def seed_tags():
    """Seed initial tags into the database."""

    app = create_app()

    with app.app_context():
        print("Seeding initial tags...")

        # Check if tags already exist
        existing_count = Tag.query.count()
        if existing_count > 0:
            print(f"Found {existing_count} existing tags.")
            response = input("Do you want to add new tags anyway? (y/n): ")
            if response.lower() != 'y':
                print("Skipping tag seeding.")
                return

        # Create tags
        added_count = 0
        skipped_count = 0

        for tag_name in VALID_TAGS:
            # Check if tag already exists
            existing_tag = Tag.query.filter_by(name=tag_name).first()

            if existing_tag:
                print(f"  ⏭ Skipping '{tag_name}' (already exists)")
                skipped_count += 1
                continue

            # Create new tag
            tag = Tag(
                name=tag_name,
                frequency=0,
                first_seen=None,
                last_seen=None,
                growth_rate=0.0,
                created_at=datetime.utcnow()
            )
            db.session.add(tag)
            added_count += 1
            print(f"  ✓ Added '{tag_name}'")

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully seeded {added_count} tags")
            if skipped_count > 0:
                print(f"   Skipped {skipped_count} existing tags")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error seeding tags: {e}")
            raise


if __name__ == '__main__':
    seed_tags()
