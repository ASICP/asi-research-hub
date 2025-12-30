"""
Paper ingestion service for ARA v2.
Handles fetching papers from external sources, deduplication, tag assignment, and storage.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from flask import current_app
from sqlalchemy.exc import IntegrityError

from ara_v2.models.paper import Paper
from ara_v2.models.tag import Tag
from ara_v2.models.paper_tag import PaperTag
from ara_v2.models.citation import Citation
from ara_v2.utils.database import db
from ara_v2.services.connectors.semantic_scholar import SemanticScholarConnector
from ara_v2.services.connectors.arxiv import ArxivConnector
from ara_v2.services.connectors.crossref import CrossRefConnector
from ara_v2.services.connectors.serpapi_google_scholar import SerpAPIGoogleScholarConnector
from ara_v2.services.tag_assigner import TagAssigner
from ara_v2.services.scoring.tag_scorer import TagScorer, update_tag_statistics
from ara_v2.services.tag_combo_tracker import track_paper_tag_combinations


class PaperIngestionService:
    """
    Service for ingesting papers from external sources into ARA database.

    Responsibilities:
    - Search multiple sources for papers
    - Deduplicate papers across sources
    - Assign tags using hybrid algorithm
    - Store papers and relationships in database
    - Build citation networks
    """

    def __init__(self):
        """Initialize the paper ingestion service."""
        self.s2_connector = SemanticScholarConnector()
        self.arxiv_connector = ArxivConnector()
        self.crossref_connector = CrossRefConnector()

        # Initialize SerpAPI connector for Google Scholar (if API key is configured)
        try:
            from flask import current_app
            api_key = current_app.config.get('SERPAPI_API_KEY', '')
            if api_key:
                self.serpapi_connector = SerpAPIGoogleScholarConnector(api_key=api_key)
                current_app.logger.info("SerpAPI Google Scholar connector initialized")
            else:
                self.serpapi_connector = None
                current_app.logger.warning("SerpAPI key not configured - Google Scholar searches will be disabled")
        except Exception as e:
            self.serpapi_connector = None
            current_app.logger.error(f"Failed to initialize SerpAPI connector: {e}")

        self.tag_assigner = TagAssigner()

    def search_and_ingest(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 20,
        assign_tags: bool = True
    ) -> Dict[str, Any]:
        """
        Search for papers across multiple sources and ingest them.

        Args:
            query: Search query string
            sources: List of sources to search (defaults to all)
            max_results_per_source: Max results per source
            assign_tags: Whether to automatically assign tags

        Returns:
            dict: {
                'total_fetched': int,
                'total_ingested': int,
                'duplicates_found': int,
                'papers': List[Paper]
            }
        """
        if sources is None:
            sources = ['semantic_scholar', 'arxiv', 'crossref', 'google_scholar']

        all_papers_data = []
        fetch_stats = {}

        # Search each source
        for source in sources:
            try:
                if source == 'semantic_scholar':
                    result = self.s2_connector.search_papers(query, limit=max_results_per_source)
                    papers_data = result['papers']
                elif source == 'arxiv':
                    result = self.arxiv_connector.search_papers(query, max_results=max_results_per_source)
                    papers_data = result['papers']
                elif source == 'crossref':
                    result = self.crossref_connector.search_papers(query, rows=max_results_per_source)
                    papers_data = result['papers']
                elif source == 'google_scholar':
                    # Google Scholar via SerpAPI with arXiv fallback on timeout
                    if not self.serpapi_connector:
                        current_app.logger.warning("Google Scholar requested but SerpAPI not configured - skipping")
                        fetch_stats[source] = 0
                        continue

                    try:
                        current_app.logger.info(f"Searching Google Scholar via SerpAPI for: {query}")
                        result = self.serpapi_connector.search_papers(query, limit=max_results_per_source)
                        papers_data = result['papers']
                        current_app.logger.info(f"✓ Google Scholar returned {len(papers_data)} papers")
                    except Exception as scholar_error:
                        error_msg = str(scholar_error).lower()

                        # Check if it's a timeout error
                        if 'timeout' in error_msg or 'timed out' in error_msg:
                            current_app.logger.warning(
                                f"⚠️ Google Scholar search timed out: {scholar_error}"
                            )
                            current_app.logger.info(f"→ Falling back to arXiv for query: {query}")

                            try:
                                # Fallback to arXiv
                                result = self.arxiv_connector.search_papers(query, max_results=max_results_per_source)
                                papers_data = result['papers']
                                current_app.logger.info(f"✓ arXiv fallback returned {len(papers_data)} papers")
                                fetch_stats[f'{source}_fallback_arxiv'] = len(papers_data)
                            except Exception as arxiv_error:
                                current_app.logger.error(f"arXiv fallback also failed: {arxiv_error}")
                                fetch_stats[source] = 0
                                continue
                        else:
                            # Not a timeout - log error and skip
                            current_app.logger.error(f"Google Scholar search failed: {scholar_error}")
                            fetch_stats[source] = 0
                            continue
                else:
                    current_app.logger.warning(f"Unknown source: {source}")
                    continue

                all_papers_data.extend(papers_data)
                fetch_stats[source] = len(papers_data)

                current_app.logger.info(f"Fetched {len(papers_data)} papers from {source}")

            except Exception as e:
                current_app.logger.error(f"Error searching {source}: {e}")
                fetch_stats[source] = 0

        # Deduplicate across sources
        deduplicated_data = self._deduplicate_papers(all_papers_data)

        # Ingest papers
        ingested_papers = []
        duplicates_count = 0

        for paper_data in deduplicated_data:
            paper, is_new = self.ingest_paper(paper_data, assign_tags=assign_tags)

            if paper:
                ingested_papers.append(paper)
                if not is_new:
                    duplicates_count += 1

        # Commit all changes
        try:
            db.session.commit()
            current_app.logger.info(
                f"Ingestion complete: {len(ingested_papers)} papers "
                f"({duplicates_count} duplicates found)"
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to commit ingestion: {e}")
            raise

        return {
            'total_fetched': len(all_papers_data),
            'total_ingested': len(ingested_papers),
            'new_papers': len(ingested_papers) - duplicates_count,
            'duplicates_found': duplicates_count,
            'fetch_stats': fetch_stats,
            'papers': ingested_papers
        }

    def ingest_paper(
        self,
        paper_data: Dict[str, Any],
        assign_tags: bool = True
    ) -> Tuple[Optional[Paper], bool]:
        """
        Ingest a single paper into the database.

        Args:
            paper_data: Normalized paper data from connector
            assign_tags: Whether to automatically assign tags

        Returns:
            tuple: (Paper instance or None, is_new)
                   is_new is True if paper was newly created, False if updated
        """
        # Check for existing paper
        existing_paper = self._find_existing_paper(paper_data)

        if existing_paper:
            # Update existing paper
            updated = self._update_paper(existing_paper, paper_data)
            return existing_paper, False

        # Create new paper
        try:
            paper = Paper(
                source=paper_data.get('source', ''),
                source_id=paper_data.get('source_id', ''),
                doi=paper_data.get('doi'),
                arxiv_id=paper_data.get('arxiv_id'),
                title=paper_data.get('title', ''),
                abstract=paper_data.get('abstract'),
                authors=paper_data.get('authors', []),
                year=paper_data.get('year'),
                citation_count=paper_data.get('citation_count', 0),
                raw_data=paper_data.get('raw_data')  # Store source-specific metadata for tag assignment
            )

            db.session.add(paper)
            db.session.flush()  # Get paper.id without committing

            combo_stats = {}

            # Assign tags if requested
            if assign_tags:
                self._assign_tags_to_paper(paper)

                # Flush to ensure paper_tags are saved before combo tracking
                db.session.flush()

                # Track tag combinations (for novelty detection)
                combo_stats = track_paper_tag_combinations(paper.id)

                # Calculate tag score after tags are assigned
                self._calculate_and_save_tag_score(paper)

            current_app.logger.info(
                f"Created new paper: {paper.title[:50]}... "
                f"(tags={paper.tags_relationship.count()}, novel_combos={combo_stats.get('novel_combos', 0)})"
            )

            return paper, True

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating paper: {e}")
            raise e # Re-raise to debug upload failures

    def _find_existing_paper(self, paper_data: Dict[str, Any]) -> Optional[Paper]:
        """
        Find existing paper by DOI, ArXiv ID, or source ID.

        Args:
            paper_data: Normalized paper data

        Returns:
            Paper: Existing paper or None
        """
        # Try DOI first (most reliable)
        doi = paper_data.get('doi')
        if doi:
            paper = Paper.query.filter_by(doi=doi).first()
            if paper:
                return paper

        # Try ArXiv ID
        arxiv_id = paper_data.get('arxiv_id')
        if arxiv_id:
            paper = Paper.query.filter_by(arxiv_id=arxiv_id).first()
            if paper:
                return paper

        # Try source + source_id
        source = paper_data.get('source')
        source_id = paper_data.get('source_id')
        if source and source_id:
            paper = Paper.query.filter_by(
                source=source,
                source_id=source_id
            ).first()
            if paper:
                return paper

        # Try title matching (fuzzy - only if no other IDs)
        title = paper_data.get('title', '').strip().lower()
        if title and len(title) > 20:
            # Simple title matching (could be improved with fuzzy matching)
            paper = Paper.query.filter(
                db.func.lower(Paper.title) == title).first()
            if paper:
                return paper

        return None

    def _update_paper(self, paper: Paper, paper_data: Dict[str, Any]) -> bool:
        """
        Update existing paper with new data if it has changed.

        Args:
            paper: Existing Paper instance
            paper_data: New paper data

        Returns:
            bool: True if paper was updated
        """
        updated = False

        # Update citation count if higher
        new_citation_count = paper_data.get('citation_count', 0)
        if new_citation_count > paper.citation_count:
            paper.citation_count = new_citation_count
            updated = True

        # Fill in missing fields
        if not paper.doi and paper_data.get('doi'):
            paper.doi = paper_data['doi']
            updated = True

        if not paper.arxiv_id and paper_data.get('arxiv_id'):
            paper.arxiv_id = paper_data['arxiv_id']
            updated = True

        if not paper.abstract and paper_data.get('abstract'):
            paper.abstract = paper_data['abstract']
            updated = True

        if not paper.venue and paper_data.get('venue'):
            updated = True

        # Update raw_data if not present (for tag assignment)
        if not paper.raw_data and paper_data.get('raw_data'):
            paper.raw_data = paper_data['raw_data']
            updated = True

            paper.venue = paper_data['venue']
            updated = True

        # Update raw_data if not present (for tag assignment)
        if not paper.raw_data and paper_data.get('raw_data'):
            paper.raw_data = paper_data['raw_data']
            updated = True

        if updated:
            current_app.logger.info(f"Updated paper: {paper.title[:50]}...")

        return updated

    def _deduplicate_papers(
        self,
        papers_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate papers across sources using DOI, ArXiv ID, and title.

        Args:
            papers_data: List of normalized paper data

        Returns:
            list: Deduplicated paper data
        """
        seen_dois = set()
        seen_arxiv_ids = set()
        seen_titles = set()
        unique_papers = []

        for paper_data in papers_data:
            doi = paper_data.get('doi')
            arxiv_id = paper_data.get('arxiv_id')
            title = paper_data.get('title', '').strip().lower()

            # Check DOI
            if doi and doi in seen_dois:
                continue

            # Check ArXiv ID
            if arxiv_id and arxiv_id in seen_arxiv_ids:
                continue

            # Check title (only for titles > 20 chars)
            if title and len(title) > 20 and title in seen_titles:
                continue

            # Add to seen sets
            if doi:
                seen_dois.add(doi)
            if arxiv_id:
                seen_arxiv_ids.add(arxiv_id)
            if title and len(title) > 20:
                seen_titles.add(title)

            unique_papers.append(paper_data)

        current_app.logger.info(
            f"Deduplicated {len(papers_data)} -> {len(unique_papers)} papers"
        )

        return unique_papers

    def _assign_tags_to_paper(self, paper: Paper):
        """
        Assign tags to a paper using the tag assignment algorithm.

        Args:
            paper: Paper instance
        """
        tag_assignments = self.tag_assigner.assign_and_save_tags(paper)

        if not tag_assignments:
            return

        # Create PaperTag relationships
        for tag, confidence in tag_assignments:
            paper_tag = PaperTag(
                paper_id=paper.id,
                tag_id=tag.id,
                confidence=confidence
            )
            db.session.add(paper_tag)
        # Flush to ensure PaperTag records are in the database before counting
        db.session.flush()

        # Flush to ensure PaperTag records are in the database before counting
        db.session.flush()

        # Update tag statistics
        for tag, _ in tag_assignments:
            tag.paper_count = db.session.query(PaperTag).filter_by(tag_id=tag.id).count()
            tag.frequency = tag.paper_count  # Sync frequency with paper count for dashboard
            tag.last_used = datetime.utcnow()

            # Update tag growth rate
            update_tag_statistics(tag.id)

    def _calculate_and_save_tag_score(self, paper: Paper):
        """
        Calculate and save tag score for a paper.

        Args:
            paper: Paper instance with tags already assigned
        """
        try:
            scorer = TagScorer()
            tag_score = scorer.calculate_tag_score(paper.id)

            # Save score to paper
            paper.tag_score = tag_score
            paper.scored_at = datetime.utcnow()

            current_app.logger.info(
                f"Calculated tag score for paper {paper.id}: {tag_score:.2f}"
            )

        except Exception as e:
            current_app.logger.error(
                f"Error calculating tag score for paper {paper.id}: {e}"
            )
            # Don't fail the ingestion if scoring fails
            paper.tag_score = None

    def build_citation_network(
        self,
        paper: Paper,
        max_citations: int = 50,
        max_references: int = 50
    ) -> Dict[str, int]:
        """
        Build citation network for a paper using Semantic Scholar.

        Args:
            paper: Paper instance
            max_citations: Maximum citations to fetch
            max_references: Maximum references to fetch

        Returns:
            dict: {'citations_added': int, 'references_added': int}
        """
        if not paper.source_id or paper.source != 'semantic_scholar':
            current_app.logger.warning(
                f"Paper {paper.id} not from Semantic Scholar, skipping citation network"
            )
            return {'citations_added': 0, 'references_added': 0}

        stats = {'citations_added': 0, 'references_added': 0}

        try:
            # Get papers that cite this paper
            citing_papers = self.s2_connector.get_paper_citations(
                paper.source_id,
                limit=max_citations
            )

            for citing_data in citing_papers:
                # Ingest citing paper
                citing_paper, _ = self.ingest_paper(citing_data, assign_tags=False)

                if citing_paper:
                    # Create citation relationship
                    citation = Citation(
                        citing_paper_id=citing_paper.id,
                        cited_paper_id=paper.id
                    )
                    db.session.add(citation)
                    stats['citations_added'] += 1

            # Get papers referenced by this paper
            referenced_papers = self.s2_connector.get_paper_references(
                paper.source_id,
                limit=max_references
            )

            for referenced_data in referenced_papers:
                # Ingest referenced paper
                referenced_paper, _ = self.ingest_paper(referenced_data, assign_tags=False)

                if referenced_paper:
                    # Create citation relationship
                    citation = Citation(
                        citing_paper_id=paper.id,
                        cited_paper_id=referenced_paper.id
                    )
                    db.session.add(citation)
                    stats['references_added'] += 1

            db.session.commit()

            current_app.logger.info(
                f"Built citation network for paper {paper.id}: "
                f"{stats['citations_added']} citations, {stats['references_added']} references"
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error building citation network: {e}")

        return stats

    def search_ai_safety_papers(
        self,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Convenience method to search and ingest AI safety papers from all sources.

        Args:
            max_results: Maximum results per source

        Returns:
            dict: Ingestion statistics
        """
        query = (
            'AI safety OR alignment OR interpretability OR '
            'machine learning safety OR adversarial robustness'
        )

        return self.search_and_ingest(
            query=query,
            max_results_per_source=max_results,
            assign_tags=True
        )
