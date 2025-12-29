"""
Metrics endpoints for ARA v2.
"""

from flask import Blueprint, jsonify, current_app
from sqlalchemy import desc
from ara_v2.models.paper import Paper
from ara_v2.models.tag import Tag, TagCombo
from ara_v2.utils.database import db
from ara_v2.services.novelty_scorer import NoveltyScorer

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_metrics():
    """
    Get metrics for the dashboard:
    1. Top tags by frequency (with data for pie chart)
    2. Top cited papers (with data for pie chart)
    3. Novel ideas (scored papers >= 60 points)
    """
    try:
        # 1. Top Research Paper Tags
        top_tags = Tag.query.order_by(desc(Tag.frequency)).limit(10).all()
        tags_data = [{
            'name': t.name,
            'frequency': t.frequency,
            'growth_rate': float(t.growth_rate) if t.growth_rate else 0
        } for t in top_tags]

        # 2. Most Cited Papers
        candidate_papers = Paper.query.filter(Paper.citation_count > 0).order_by(desc(Paper.citation_count)).limit(20).all()

        seen_titles = set()
        cited_data = []
        for p in candidate_papers:
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

            if len(cited_data) >= 10:
                break

        # 3. Novel Ideas - Score all recent papers
        recent_papers = Paper.query.filter(
            Paper.created_at >= db.func.now() - db.text("INTERVAL '90 days'")
        ).all()

        scored_papers = []
        for paper in recent_papers:
            total_score, breakdown = NoveltyScorer.score_paper(paper)

            scored_papers.append({
                    'id': paper.id,
                    'title': paper.title,
                    'score': total_score,
                    'breakdown': breakdown,
                    'source': paper.source,
                    'year': paper.year,
                    'created_at': paper.created_at.isoformat() if paper.created_at else None
                })

        # Sort by score descending and take top 8
        scored_papers.sort(key=lambda x: x['score'], reverse=True)
        scored_papers = scored_papers[:8]  # Limit to top 8 most novel papers

        return jsonify({
            'top_tags': tags_data,
            'top_cited_papers': cited_data,
            'novel_ideas': scored_papers
        }), 200

    except Exception as e:
        current_app.logger.error(f"Metrics dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

