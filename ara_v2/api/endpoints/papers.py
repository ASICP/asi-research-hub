"""
Paper endpoints for ARA v2.
Handles paper search, retrieval, and management.
"""

from flask import Blueprint, request, jsonify, current_app
from ara_v2.models.paper import Paper
from ara_v2.models.tag import Tag
from ara_v2.models.paper_tag import PaperTag
from ara_v2.models.citation import Citation
from ara_v2.middleware.auth import require_auth, optional_auth, get_current_user
from ara_v2.utils.database import db
from ara_v2.utils.errors import ValidationError, NotFoundError
from ara_v2.utils.rate_limiter import limiter
from ara_v2.services.paper_ingestion import PaperIngestionService
from sqlalchemy import func, or_, and_

papers_bp = Blueprint('papers', __name__)


@papers_bp.route('/search', methods=['POST'])
@optional_auth
@limiter.limit("30 per minute")
def search():
    """
    Search for papers across multiple sources.

    Request body:
        {
            "query": "AI safety",
            "sources": ["semantic_scholar", "arxiv", "crossref", "google_scholar"],  # Optional, defaults to all
            "max_results": 20,  # Optional, default: 20
            "ingest": true,  # Optional, whether to save to DB, default: false
            "assign_tags": true  # Optional, auto-assign tags, default: true
        }

    Available sources:
        - semantic_scholar: Free API, 200M+ papers
        - arxiv: Free API, STEM preprints
        - crossref: Free API, comprehensive metadata
        - google_scholar: SerpAPI required (SERPAPI_API_KEY), with arXiv fallback on timeout

    Returns:
        {
            "total_fetched": int,
            "total_ingested": int,  # If ingest=true
            "papers": List[dict],
            "warnings": List[dict]  # Optional, if any source failed
        }
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        query = data.get('query', '').strip()
        if not query:
            raise ValidationError('Query parameter is required')

        sources = data.get('sources', ['semantic_scholar', 'arxiv', 'crossref', 'google_scholar'])
        max_results = data.get('max_results', 20)
        ingest = data.get('ingest', False)
        assign_tags = data.get('assign_tags', True)

        # Validate max_results
        if max_results < 1 or max_results > 100:
            raise ValidationError('max_results must be between 1 and 100')

        # Initialize ingestion service
        ingestion_service = PaperIngestionService()

        if ingest:
            # Search and ingest papers
            result = ingestion_service.search_and_ingest(
                query=query,
                sources=sources,
                max_results_per_source=max_results,
                assign_tags=assign_tags
            )

            papers_data = [paper.to_dict() for paper in result['papers']]

            return jsonify({
                'total_fetched': result['total_fetched'],
                'total_ingested': result['total_ingested'],
                'new_papers': result['new_papers'],
                'duplicates_found': result['duplicates_found'],
                'fetch_stats': result['fetch_stats'],
                'papers': papers_data
            }), 200

        else:
            # Search only (don't save to database)
            all_papers = []
            warnings = []

            if 'semantic_scholar' in sources:
                try:
                    s2_result = ingestion_service.s2_connector.search_papers(
                        query, limit=max_results
                    )
                    all_papers.extend(s2_result['papers'])
                except Exception as e:
                    current_app.logger.error(f"Semantic Scholar search error: {e}")

            if 'arxiv' in sources:
                try:
                    arxiv_result = ingestion_service.arxiv_connector.search_papers(
                        query, max_results=max_results
                    )
                    all_papers.extend(arxiv_result['papers'])
                except Exception as e:
                    current_app.logger.error(f"ArXiv search error: {e}")

            if 'crossref' in sources:
                try:
                    crossref_result = ingestion_service.crossref_connector.search_papers(
                        query, rows=max_results
                    )
                    all_papers.extend(crossref_result['papers'])
                except Exception as e:
                    current_app.logger.error(f"CrossRef search error: {e}")

            if 'google_scholar' in sources:
                # Google Scholar via SerpAPI with arXiv fallback on any error
                if not ingestion_service.serpapi_connector:
                    warnings.append({
                        'source': 'google_scholar',
                        'message': 'Google Scholar search skipped - SerpAPI key not configured. Get API key from https://serpapi.com/'
                    })
                else:
                    try:
                        current_app.logger.info(f"Searching Google Scholar via SerpAPI for: {query}")
                        scholar_result = ingestion_service.serpapi_connector.search_papers(
                            query, limit=max_results
                        )
                        all_papers.extend(scholar_result['papers'])
                        current_app.logger.info(f"✓ Google Scholar returned {len(scholar_result['papers'])} papers")
                    except Exception as scholar_error:
                        error_msg = str(scholar_error).lower()

                        # Fall back to arXiv for any Google Scholar error
                        current_app.logger.warning(f"⚠️ Google Scholar search failed: {scholar_error}")
                        current_app.logger.info(f"→ Falling back to arXiv for query: {query}")

                        try:
                            # Fallback to arXiv
                            arxiv_fallback_result = ingestion_service.arxiv_connector.search_papers(
                                query, max_results=max_results
                            )
                            all_papers.extend(arxiv_fallback_result['papers'])
                            current_app.logger.info(f"✓ arXiv fallback returned {len(arxiv_fallback_result['papers'])} papers")

                            # Customize warning message based on error type
                            if 'timeout' in error_msg or 'timed out' in error_msg:
                                fallback_reason = 'Google Scholar timed out'
                            elif 'not found' in error_msg:
                                fallback_reason = 'Google Scholar returned no results'
                            else:
                                fallback_reason = 'Google Scholar unavailable'

                            warnings.append({
                                'source': 'google_scholar',
                                'message': f'{fallback_reason} - showing results from arXiv instead'
                            })
                        except Exception as arxiv_error:
                            current_app.logger.error(f"arXiv fallback also failed: {arxiv_error}")
                            warnings.append({
                                'source': 'google_scholar',
                                'message': f'Google Scholar failed and arXiv fallback also failed: {str(arxiv_error)}'
                            })

            # Deduplicate
            deduplicated = ingestion_service._deduplicate_papers(all_papers)

            response_data = {
                'total_fetched': len(deduplicated),
                'papers': deduplicated
            }

            if warnings:
                response_data['warnings'] = warnings

            return jsonify(response_data), 200

    except ValidationError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Search error: {e}")
        raise


@papers_bp.route('', methods=['GET'])
@optional_auth
def list_papers():
    """
    List papers from database with filtering and pagination.

    Query parameters:
        - page: Page number (default: 1)
        - per_page: Results per page (default: 20, max: 100)
        - tag: Filter by tag name
        - year: Filter by year
        - source: Filter by source (semantic_scholar, arxiv, crossref)
        - sort: Sort by (recent, citations, relevance) (default: recent)
        - q: Search query (title, abstract)

    Returns:
        {
            "total": int,
            "page": int,
            "per_page": int,
            "papers": List[dict]
        }
    """
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        # Filters
        tag_name = request.args.get('tag')
        year = request.args.get('year', type=int)
        source = request.args.get('source')
        sort_by = request.args.get('sort', 'recent')
        search_query = request.args.get('q', '').strip()

        # Build query
        query = Paper.query.filter_by(deleted_at=None)

        # Filter by tag
        if tag_name:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag:
                query = query.join(PaperTag).filter(PaperTag.tag_id == tag.id)

        # Filter by year
        if year:
            query = query.filter(Paper.year == year)

        # Filter by source
        if source:
            query = query.filter(Paper.source == source)

        # Search in title and abstract
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                or_(
                    Paper.title.ilike(search_pattern),
                    Paper.abstract.ilike(search_pattern)
                )
            )

        # Sorting
        if sort_by == 'recent':
            query = query.order_by(Paper.published_date.desc().nullslast())
        elif sort_by == 'citations':
            query = query.order_by(Paper.citation_count.desc())
        elif sort_by == 'relevance' and search_query:
            # Simple relevance: prioritize title matches
            query = query.order_by(
                Paper.title.ilike(search_pattern).desc(),
                Paper.citation_count.desc()
            )
        else:
            query = query.order_by(Paper.created_at.desc())

        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        papers_data = [paper.to_dict() for paper in pagination.items]

        return jsonify({
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'papers': papers_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"List papers error: {e}")
        raise


@papers_bp.route('/<int:paper_id>', methods=['GET'])
@optional_auth
def get_paper(paper_id):
    """
    Get detailed information about a specific paper.

    Path parameters:
        - paper_id: Paper ID

    Returns:
        {
            "id": int,
            "title": str,
            "abstract": str,
            "authors": List[str],
            "year": int,
            "tags": List[dict],
            "citations": List[dict],
            "references": List[dict],
            ...
        }
    """
    try:
        paper = Paper.query.filter_by(id=paper_id, deleted_at=None).first()

        if not paper:
            raise NotFoundError(f'Paper {paper_id} not found')

        # Get paper data
        paper_data = paper.to_dict()

        # Get tags with confidence scores
        paper_tags = db.session.query(PaperTag, Tag).join(Tag).filter(
            PaperTag.paper_id == paper_id
        ).all()

        paper_data['tags'] = [
            {
                'name': tag.name,
                'slug': tag.slug,
                'confidence': paper_tag.confidence
            }
            for paper_tag, tag in paper_tags
        ]

        # Get citation count and sample citations
        citations = db.session.query(Citation, Paper).join(
            Paper, Citation.citing_paper_id == Paper.id
        ).filter(
            Citation.cited_paper_id == paper_id,
            Paper.deleted_at == None
        ).limit(10).all()

        paper_data['cited_by'] = [
            {
                'id': citing_paper.id,
                'title': citing_paper.title,
                'year': citing_paper.year,
                'authors': citing_paper.authors
            }
            for _, citing_paper in citations
        ]

        # Get references (papers this paper cites)
        references = db.session.query(Citation, Paper).join(
            Paper, Citation.cited_paper_id == Paper.id
        ).filter(
            Citation.citing_paper_id == paper_id,
            Paper.deleted_at == None
        ).limit(10).all()

        paper_data['references'] = [
            {
                'id': cited_paper.id,
                'title': cited_paper.title,
                'year': cited_paper.year,
                'authors': cited_paper.authors
            }
            for _, cited_paper in references
        ]

        return jsonify(paper_data), 200

    except NotFoundError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Get paper error: {e}")
        raise


@papers_bp.route('/<int:paper_id>/scores', methods=['GET'])
@optional_auth
def get_paper_scores(paper_id):
    """
    Get all scores for a paper.

    Path parameters:
        - paper_id: Paper ID

    Returns:
        {
            "paper_id": int,
            "tag_score": float,
            "citation_score": float,
            "novelty_score": float,
            "holmes_score": float,
            "is_diamond": bool,
            "scored_at": str (ISO 8601)
        }
    """
    try:
        paper = Paper.query.filter_by(id=paper_id, deleted_at=None).first()

        if not paper:
            raise NotFoundError(f'Paper {paper_id} not found')

        scores = {
            'paper_id': paper.id,
            'tag_score': float(paper.tag_score) if paper.tag_score else None,
            'citation_score': float(paper.citation_score) if paper.citation_score else None,
            'novelty_score': float(paper.novelty_score) if paper.novelty_score else None,
            'holmes_score': float(paper.holmes_score) if paper.holmes_score else None,
            'is_diamond': paper.is_diamond,
            'scored_at': paper.scored_at.isoformat() if paper.scored_at else None
        }

        return jsonify(scores), 200

    except NotFoundError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Get paper scores error: {e}")
        raise


@papers_bp.route('/<int:paper_id>/novel-combos', methods=['GET'])
@optional_auth
def get_paper_novel_combos(paper_id):
    """
    Get novel tag combinations for a paper.

    Path parameters:
        - paper_id: Paper ID

    Returns:
        {
            "paper_id": int,
            "novel_combos": [
                {
                    "tag_ids": [int, int],
                    "tag_names": [str, str],
                    "frequency": int
                }
            ]
        }
    """
    try:
        from ara_v2.services.tag_combo_tracker import TagComboTracker

        paper = Paper.query.filter_by(id=paper_id, deleted_at=None).first()

        if not paper:
            raise NotFoundError(f'Paper {paper_id} not found')

        tracker = TagComboTracker()
        novel_combos = tracker.get_paper_novel_combos(paper_id)

        return jsonify({
            'paper_id': paper_id,
            'novel_combos': novel_combos
        }), 200

    except NotFoundError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Get paper novel combos error: {e}")
        raise


@papers_bp.route('/<int:paper_id>/citations', methods=['POST'])
@require_auth
@limiter.limit("10 per hour")
def build_citations(paper_id):
    """
    Build citation network for a paper (requires authentication).

    Path parameters:
        - paper_id: Paper ID

    Request body:
        {
            "max_citations": 50,  # Optional
            "max_references": 50   # Optional
        }

    Returns:
        {
            "citations_added": int,
            "references_added": int
        }
    """
    try:
        paper = Paper.query.filter_by(id=paper_id, deleted_at=None).first()

        if not paper:
            raise NotFoundError(f'Paper {paper_id} not found')

        data = request.get_json() or {}
        max_citations = data.get('max_citations', 50)
        max_references = data.get('max_references', 50)

        # Initialize ingestion service
        ingestion_service = PaperIngestionService()

        # Build citation network
        stats = ingestion_service.build_citation_network(
            paper,
            max_citations=max_citations,
            max_references=max_references
        )

        return jsonify(stats), 200

    except NotFoundError as e:
        raise
    except Exception as e:
        current_app.logger.error(f"Build citations error: {e}")
        raise


@papers_bp.route('/featured', methods=['GET'])
@optional_auth
def featured():
    """
    Get high-scoring papers (placeholder for Phase 2).

    Returns:
        {
            "papers": List[dict]
        }
    """
    # For now, return most cited papers
    papers = Paper.query.filter_by(deleted_at=None).order_by(
        Paper.citation_count.desc()
    ).limit(20).all()

    return jsonify({
        'papers': [paper.to_dict() for paper in papers]
    }), 200


@papers_bp.route('/diamonds', methods=['GET'])
@optional_auth
def diamonds():
    """
    Get diamond-classified papers (placeholder for Phase 2).

    Returns:
        {
            "papers": List[dict]
        }
    """
    # Placeholder: return papers with holmes_score when Phase 2 is implemented
    return jsonify({
        'message': 'Diamond classification coming in Phase 2',
        'papers': []
    }), 200
