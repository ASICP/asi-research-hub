"""
Metrics endpoints for ARA v2.
"""

from flask import Blueprint, jsonify, current_app
from sqlalchemy import desc
from ara_v2.models.paper import Paper
from ara_v2.models.tag import Tag, TagCombo
from ara_v2.utils.database import db

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_metrics():
    """
    Get metrics for the dashboard:
    1. Top tags by frequency
    2. Top cited papers
    3. Novel/unique ideas (TagCombos)
    """
    try:
        # 1. Top Research Paper Tags (Frequency)
        top_tags = Tag.query.order_by(desc(Tag.frequency)).limit(10).all()
        tags_data = [{
            'name': t.name,
            'frequency': t.frequency,
            'growth_rate': float(t.growth_rate) if t.growth_rate else 0
        } for t in top_tags]

        # 2. Most Cited Papers
        # Fetch more candidates to allow for deduplication
        candidate_papers = Paper.query.filter(Paper.citation_count > 0).order_by(desc(Paper.citation_count)).limit(20).all()
        
        seen_titles = set()
        cited_data = []
        for p in candidate_papers:
            # Normalize title for dedup
            norm_title = p.title.lower().strip()
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)
            
            cited_data.append({
                'id': p.id,
                'title': p.title,
                'citations': p.citation_count,
                'year': p.year
            })
            
            if len(cited_data) >= 5:
                break

        # 3. Novel/Unique Ideas (TagCombos)
        # We look for combos with low frequency (rare) but marked as novel
        novel_combos = TagCombo.query.filter_by(is_novel=True).order_by(TagCombo.created_at.desc()).limit(10).all()

        # We need tag names for the combos
        combo_data = []
        for combo in novel_combos:
            # Skip if tag_ids is empty or None
            if not combo.tag_ids:
                continue

            # Fetch tag names
            combo_tags = Tag.query.filter(Tag.id.in_(combo.tag_ids)).all()

            # Skip if no tags found
            if not combo_tags:
                continue

            tag_names = [t.name for t in combo_tags]
            # Ensure score doesn't go below 10
            score = max(10, 100 - (combo.frequency * 10))

            combo_data.append({
                'tags': tag_names,
                'score': score
            })

        return jsonify({
            'top_tags': tags_data,
            'top_cited_papers': cited_data,
            'novel_ideas': combo_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"Metrics dashboard error: {e}")
        return jsonify({'error': str(e)}), 500
