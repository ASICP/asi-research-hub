"""
Tag endpoints for ARA v2.
Handles tag retrieval and statistics.
"""

from flask import Blueprint, request, jsonify, current_app
from ara_v2.models.tag import Tag, PaperTag, TagCombo
from ara_v2.models.paper import Paper
from ara_v2.middleware.auth import optional_auth
from ara_v2.utils.database import db
from ara_v2.utils.errors import NotFoundError
from sqlalchemy import func, desc

tags_bp = Blueprint('tags', __name__)


@tags_bp.route('/', methods=['GET'])
@optional_auth
def list_tags():
    """
    Get all tags with statistics.

    Query parameters:
        - category: Filter by category (optional)
        - min_papers: Minimum paper count (optional)
        - sort: Sort by (name, papers, recent) (default: papers)
        - limit: Maximum number of tags to return (default: all)

    Returns:
        {
            "total": int,
            "tags": List[dict]
        }
    """
    try:
        # Filters
        category = request.args.get('category')
        min_papers = request.args.get('min_papers', type=int, default=0)
        sort_by = request.args.get('sort', 'papers')
        limit = request.args.get('limit', type=int)

        # Build query
        query = Tag.query

        # Filter by category
        if category:
            query = query.filter(Tag.category == category)

        # Filter by minimum papers
        if min_papers > 0:
            query = query.filter(Tag.paper_count >= min_papers)

        # Sorting
        if sort_by == 'name':
            query = query.order_by(Tag.name.asc())
        elif sort_by == 'recent':
            query = query.order_by(Tag.last_used.desc().nullslast())
        else:  # papers (default)
            query = query.order_by(Tag.paper_count.desc())

        # Apply limit
        if limit:
            query = query.limit(limit)

        tags = query.all()

        return jsonify({
            'total': len(tags),
            'tags': [tag.to_dict() for tag in tags]
        }), 200

    except Exception as e:
        current_app.logger.error(f"List tags error: {e}")
        raise


@tags_bp.route('/<string:tag_slug>', methods=['GET'])
@optional_auth
def get_tag(tag_slug):
    """
    Get detailed information about a specific tag.

    Path parameters:
        - tag_slug: Tag slug

    Returns:
        {
            "id": int,
            "name": str,
            "slug": str,
            "category": str,
            "paper_count": int,
            "description": str,
            "related_tags": List[dict],
            "recent_papers": List[dict]
        }
    """
    try:
        tag = Tag.query.filter_by(slug=tag_slug).first()

        if not tag:
            raise NotFoundError(f'Tag "{tag_slug}" not found')

        tag_data = tag.to_dict()

        # Get related tags (tags that frequently appear together)
        related_tags = db.session.query(
            Tag,
            func.count(PaperTag.paper_id).label('co_occurrence')
        ).join(
            PaperTag, PaperTag.tag_id == Tag.id
        ).filter(
            PaperTag.paper_id.in_(
                db.session.query(PaperTag.paper_id).filter(PaperTag.tag_id == tag.id)
            ),
            Tag.id != tag.id
        ).group_by(Tag.id).order_by(
            desc('co_occurrence')
        ).limit(10).all()

        tag_data['related_tags'] = [
            {
                'id': related_tag.id,
                'name': related_tag.name,
                'slug': related_tag.slug,
                'co_occurrence_count': count
            }
            for related_tag, count in related_tags
        ]

        # Get recent papers with this tag
        recent_papers = db.session.query(Paper).join(PaperTag).filter(
            PaperTag.tag_id == tag.id,
            Paper.deleted_at == None
        ).order_by(
            Paper.published_date.desc().nullslast()
        ).limit(10).all()

        tag_data['recent_papers'] = [
            {
                'id': paper.id,
                'title': paper.title,
                'year': paper.year,
                'authors': paper.authors,
                'citation_count': paper.citation_count
            }
            for paper in recent_papers
        ]

        return jsonify(tag_data), 200

    except NotFoundError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Get tag error: {e}")
        raise


@tags_bp.route('/trending', methods=['GET'])
@optional_auth
def trending_tags():
    """
    Get trending/fastest-growing tags.

    Query parameters:
        - limit: Maximum number of tags (default: 10)

    Returns:
        {
            "tags": List[dict]
        }
    """
    try:
        limit = request.args.get('limit', 10, type=int)

        # Get tags that have been used recently and have good paper counts
        # Simple approach: recently used tags with decent paper counts
        tags = Tag.query.filter(
            Tag.paper_count > 0,
            Tag.last_used != None
        ).order_by(
            Tag.last_used.desc()
        ).limit(limit).all()

        return jsonify({
            'tags': [tag.to_dict() for tag in tags]
        }), 200

    except Exception as e:
        current_app.logger.error(f"Trending tags error: {e}")
        raise


@tags_bp.route('/combos', methods=['GET'])
@optional_auth
def tag_combos():
    """
    Get interesting tag combinations.

    Query parameters:
        - min_count: Minimum occurrence count (default: 2)
        - limit: Maximum number of combos (default: 20)

    Returns:
        {
            "combos": List[dict]
        }
    """
    try:
        min_count = request.args.get('min_count', 2, type=int)
        limit = request.args.get('limit', 20, type=int)

        # Get tag combos ordered by frequency
        combos = TagCombo.query.filter(
            TagCombo.count >= min_count
        ).order_by(
            TagCombo.count.desc()
        ).limit(limit).all()

        result = []
        for combo in combos:
            # Get tag names for the combo
            tags = db.session.query(Tag).filter(
                Tag.id.in_(combo.tag_ids)
            ).all()

            result.append({
                'id': combo.id,
                'tag_ids': combo.tag_ids,
                'tags': [
                    {
                        'id': tag.id,
                        'name': tag.name,
                        'slug': tag.slug
                    }
                    for tag in tags
                ],
                'count': combo.count,
                'first_seen': combo.first_seen.isoformat() if combo.first_seen else None,
                'last_seen': combo.last_seen.isoformat() if combo.last_seen else None
            })

        return jsonify({
            'total': len(result),
            'combos': result
        }), 200

    except Exception as e:
        current_app.logger.error(f"Tag combos error: {e}")
        raise


@tags_bp.route('/categories', methods=['GET'])
@optional_auth
def tag_categories():
    """
    Get all tag categories with counts.

    Returns:
        {
            "categories": List[dict]
        }
    """
    try:
        # Get unique categories with counts
        categories = db.session.query(
            Tag.category,
            func.count(Tag.id).label('tag_count'),
            func.sum(Tag.paper_count).label('total_papers')
        ).group_by(
            Tag.category
        ).order_by(
            desc('tag_count')
        ).all()

        return jsonify({
            'categories': [
                {
                    'name': category,
                    'tag_count': tag_count,
                    'paper_count': total_papers or 0
                }
                for category, tag_count, total_papers in categories
            ]
        }), 200

    except Exception as e:
        current_app.logger.error(f"Tag categories error: {e}")
        raise


@tags_bp.route('/search', methods=['GET'])
@optional_auth
def search_tags():
    """
    Search for tags by name or description.

    Query parameters:
        - q: Search query (required)
        - limit: Maximum number of results (default: 20)

    Returns:
        {
            "total": int,
            "tags": List[dict]
        }
    """
    try:
        query_str = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)

        if not query_str:
            return jsonify({
                'total': 0,
                'tags': []
            }), 200

        # Search in name and description
        search_pattern = f'%{query_str}%'
        tags = Tag.query.filter(
            db.or_(
                Tag.name.ilike(search_pattern),
                Tag.description.ilike(search_pattern)
            )
        ).order_by(
            Tag.paper_count.desc()
        ).limit(limit).all()

        return jsonify({
            'total': len(tags),
            'tags': [tag.to_dict() for tag in tags]
        }), 200

    except Exception as e:
        current_app.logger.error(f"Search tags error: {e}")
        raise
