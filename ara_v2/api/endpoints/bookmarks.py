"""
Bookmark endpoints for ARA v2.
Handles user bookmarks with notes and tags.
"""

from flask import Blueprint, request, jsonify, current_app
from ara_v2.models.bookmark import Bookmark
from ara_v2.models.paper import Paper
from ara_v2.middleware.auth import require_auth, get_current_user_id
from ara_v2.utils.database import db
from ara_v2.utils.errors import ValidationError, NotFoundError, ConflictError
from ara_v2.utils.rate_limiter import limiter
from sqlalchemy import desc

bookmarks_bp = Blueprint('bookmarks', __name__)


@bookmarks_bp.route('/', methods=['GET'])
@require_auth
def list_bookmarks():
    """
    Get current user's bookmarks.

    Query parameters:
        - page: Page number (default: 1)
        - per_page: Results per page (default: 20, max: 100)
        - tag: Filter by bookmark tag (optional)
        - sort: Sort by (recent, title, year) (default: recent)

    Returns:
        {
            "total": int,
            "page": int,
            "per_page": int,
            "bookmarks": List[dict]
        }
    """
    try:
        user_id = get_current_user_id()

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        # Filters
        tag_filter = request.args.get('tag', '').strip()
        sort_by = request.args.get('sort', 'recent')

        # Build query
        query = db.session.query(Bookmark, Paper).join(
            Paper, Bookmark.paper_id == Paper.id
        ).filter(
            Bookmark.user_id == user_id,
            Paper.deleted_at == None
        )

        # Filter by tag if provided
        if tag_filter:
            query = query.filter(
                Bookmark.tags.contains([tag_filter])
            )

        # Sorting
        if sort_by == 'title':
            query = query.order_by(Paper.title.asc())
        elif sort_by == 'year':
            query = query.order_by(Paper.year.desc().nullslast())
        else:  # recent (default)
            query = query.order_by(Bookmark.created_at.desc())

        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        bookmarks_data = []
        for bookmark, paper in pagination.items:
            bookmark_dict = bookmark.to_dict()
            bookmark_dict['paper'] = paper.to_dict()
            bookmarks_data.append(bookmark_dict)

        return jsonify({
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'bookmarks': bookmarks_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"List bookmarks error: {e}")
        raise


@bookmarks_bp.route('/', methods=['POST'])
@require_auth
@limiter.limit("30 per minute")
def create_bookmark():
    """
    Add paper to user's bookmarks.

    Request body:
        {
            "paper_id": int,
            "notes": str,  # Optional
            "tags": List[str]  # Optional, user-defined tags
        }

    Returns:
        {
            "id": int,
            "paper_id": int,
            "notes": str,
            "tags": List[str],
            "created_at": str
        }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        paper_id = data.get('paper_id')
        if not paper_id:
            raise ValidationError('paper_id is required')

        # Check if paper exists
        paper = Paper.query.filter_by(id=paper_id, deleted_at=None).first()
        if not paper:
            raise NotFoundError(f'Paper {paper_id} not found')

        # Check if bookmark already exists
        existing = Bookmark.query.filter_by(
            user_id=user_id,
            paper_id=paper_id
        ).first()

        if existing:
            raise ConflictError('Paper already bookmarked')

        # Create bookmark
        notes = data.get('notes', '').strip()
        tags = data.get('tags', [])

        # Validate tags
        if tags and not isinstance(tags, list):
            raise ValidationError('tags must be a list of strings')

        # Limit tags
        if len(tags) > 10:
            raise ValidationError('Maximum 10 tags allowed')

        bookmark = Bookmark(
            user_id=user_id,
            paper_id=paper_id,
            notes=notes if notes else None,
            tags=tags
        )

        db.session.add(bookmark)
        db.session.commit()

        current_app.logger.info(
            f"User {user_id} bookmarked paper {paper_id}"
        )

        return jsonify(bookmark.to_dict()), 201

    except (ValidationError, NotFoundError, ConflictError) as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create bookmark error: {e}")
        raise


@bookmarks_bp.route('/<int:paper_id>', methods=['GET'])
@require_auth
def get_bookmark(paper_id):
    """
    Get a specific bookmark.

    Path parameters:
        - paper_id: Paper ID

    Returns:
        {
            "id": int,
            "paper_id": int,
            "notes": str,
            "tags": List[str],
            "created_at": str,
            "updated_at": str,
            "paper": dict
        }
    """
    try:
        user_id = get_current_user_id()

        bookmark = Bookmark.query.filter_by(
            user_id=user_id,
            paper_id=paper_id
        ).first()

        if not bookmark:
            raise NotFoundError(f'Bookmark for paper {paper_id} not found')

        # Get paper details
        paper = Paper.query.filter_by(id=paper_id, deleted_at=None).first()

        bookmark_dict = bookmark.to_dict()
        if paper:
            bookmark_dict['paper'] = paper.to_dict()

        return jsonify(bookmark_dict), 200

    except NotFoundError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Get bookmark error: {e}")
        raise


@bookmarks_bp.route('/<int:paper_id>', methods=['PATCH'])
@require_auth
@limiter.limit("60 per minute")
def update_bookmark(paper_id):
    """
    Update bookmark notes and tags.

    Path parameters:
        - paper_id: Paper ID

    Request body:
        {
            "notes": str,  # Optional
            "tags": List[str]  # Optional
        }

    Returns:
        {
            "id": int,
            "paper_id": int,
            "notes": str,
            "tags": List[str],
            "updated_at": str
        }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        bookmark = Bookmark.query.filter_by(
            user_id=user_id,
            paper_id=paper_id
        ).first()

        if not bookmark:
            raise NotFoundError(f'Bookmark for paper {paper_id} not found')

        # Update notes if provided
        if 'notes' in data:
            notes = data['notes']
            if notes is not None:
                notes = str(notes).strip()
                bookmark.notes = notes if notes else None
            else:
                bookmark.notes = None

        # Update tags if provided
        if 'tags' in data:
            tags = data['tags']
            if tags is not None:
                if not isinstance(tags, list):
                    raise ValidationError('tags must be a list of strings')

                if len(tags) > 10:
                    raise ValidationError('Maximum 10 tags allowed')

                bookmark.tags = tags
            else:
                bookmark.tags = []

        db.session.commit()

        current_app.logger.info(
            f"User {user_id} updated bookmark for paper {paper_id}"
        )

        return jsonify(bookmark.to_dict()), 200

    except (ValidationError, NotFoundError) as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update bookmark error: {e}")
        raise


@bookmarks_bp.route('/<int:paper_id>', methods=['DELETE'])
@require_auth
@limiter.limit("30 per minute")
def delete_bookmark(paper_id):
    """
    Remove bookmark.

    Path parameters:
        - paper_id: Paper ID

    Returns:
        {
            "message": "Bookmark deleted successfully"
        }
    """
    try:
        user_id = get_current_user_id()

        bookmark = Bookmark.query.filter_by(
            user_id=user_id,
            paper_id=paper_id
        ).first()

        if not bookmark:
            raise NotFoundError(f'Bookmark for paper {paper_id} not found')

        db.session.delete(bookmark)
        db.session.commit()

        current_app.logger.info(
            f"User {user_id} deleted bookmark for paper {paper_id}"
        )

        return jsonify({
            'message': 'Bookmark deleted successfully'
        }), 200

    except NotFoundError as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete bookmark error: {e}")
        raise


@bookmarks_bp.route('/stats', methods=['GET'])
@require_auth
def bookmark_stats():
    """
    Get bookmark statistics for current user.

    Returns:
        {
            "total_bookmarks": int,
            "most_used_tags": List[dict],
            "papers_by_year": dict
        }
    """
    try:
        user_id = get_current_user_id()

        # Total bookmarks
        total = Bookmark.query.filter_by(user_id=user_id).count()

        # Most used tags
        bookmarks = Bookmark.query.filter_by(user_id=user_id).all()
        tag_counts = {}
        for bookmark in bookmarks:
            for tag in bookmark.tags or []:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        most_used_tags = [
            {'tag': tag, 'count': count}
            for tag, count in sorted(
                tag_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]

        # Papers by year
        papers_by_year = db.session.query(
            Paper.year,
            db.func.count(Bookmark.id).label('count')
        ).join(
            Bookmark, Bookmark.paper_id == Paper.id
        ).filter(
            Bookmark.user_id == user_id,
            Paper.year != None
        ).group_by(
            Paper.year
        ).order_by(
            Paper.year.desc()
        ).all()

        year_distribution = {
            str(year): count for year, count in papers_by_year
        }

        return jsonify({
            'total_bookmarks': total,
            'most_used_tags': most_used_tags,
            'papers_by_year': year_distribution
        }), 200

    except Exception as e:
        current_app.logger.error(f"Bookmark stats error: {e}")
        raise


@bookmarks_bp.route('/check/<int:paper_id>', methods=['GET'])
@require_auth
def check_bookmark(paper_id):
    """
    Check if a paper is bookmarked by current user.

    Path parameters:
        - paper_id: Paper ID

    Returns:
        {
            "bookmarked": bool,
            "bookmark": dict  # If bookmarked
        }
    """
    try:
        user_id = get_current_user_id()

        bookmark = Bookmark.query.filter_by(
            user_id=user_id,
            paper_id=paper_id
        ).first()

        if bookmark:
            return jsonify({
                'bookmarked': True,
                'bookmark': bookmark.to_dict()
            }), 200
        else:
            return jsonify({
                'bookmarked': False
            }), 200

    except Exception as e:
        current_app.logger.error(f"Check bookmark error: {e}")
        raise
