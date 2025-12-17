# Phase 2 Implementation Plan - ARA v2
## The HOLMES Scoring System + UI Enhancements

**Duration:** 4-5 weeks
**Start Date:** December 16, 2025
**Status:** Ready to Begin
**Phase 1 Completion:** December 14, 2025 ✅

---

## Overview

Phase 2 consists of two major parts:
- **Phase 2A (3-4 weeks):** HOLMES Scoring Engine - Intelligent paper ranking system
- **Phase 2B (1-2 weeks):** UI Enhancements - User-facing improvements

---

## Phase 2A: HOLMES Scoring Engine (Weeks 1-4)

### Milestone Criteria (from Technical Specification)

- [ ] Papers receive Tag Score on ingestion
- [ ] Papers receive Citation Score (where data available)
- [ ] Novel papers trigger Claude evaluation
- [ ] Papers receive Novelty Score
- [ ] HOLMES composite score calculated with default weights
- [ ] Diamond papers (top 10%) flagged automatically

---

## Week 1: Tag Scoring System

### Day 1-2: Tag Score Algorithm

**Goal:** Implement tag-based relevance scoring

**Tasks:**
- [ ] Create `ara_v2/services/scoring/tag_scorer.py`
- [ ] Implement tag weight calculation
  - [ ] Base weight from tag frequency
  - [ ] Recency multiplier (exponential decay)
  - [ ] Growth bonus for trending tags
- [ ] Implement score normalization (0-100 scale)
- [ ] Create `update_tag_statistics()` function
  - [ ] Update tag.frequency counters
  - [ ] Calculate growth_rate (papers per month)
  - [ ] Track last_seen timestamps

**Deliverables:**
```python
# ara_v2/services/scoring/tag_scorer.py
def calculate_tag_score(paper_id: int) -> float:
    """Calculate Tag Score (0-100)."""
    pass

def update_tag_statistics(tag_id: int):
    """Update tag frequency and growth metrics."""
    pass

def get_max_tag_weight() -> float:
    """Get theoretical maximum tag weight for normalization."""
    pass
```

### Day 3-4: Tag Combo Tracking

**Goal:** Detect novel tag combinations

**Tasks:**
- [ ] Implement `create_or_update_tag_combo()` in paper ingestion
- [ ] Add array_sort constraint enforcement (PostgreSQL)
- [ ] Create tag combo detection logic
  - [ ] Generate all 2-tag combinations from paper tags
  - [ ] Check against tag_combos table
  - [ ] Mark novel combos (frequency <= 3)
- [ ] Update PaperTag.is_novel_combo flag

**Deliverables:**
```python
# ara_v2/services/paper_ingestion.py
def track_tag_combinations(paper_id: int, tag_ids: List[int]):
    """Track and update tag combination frequencies."""
    pass

def is_novel_combination(tag_ids: List[int]) -> bool:
    """Check if tag combination is novel."""
    pass
```

### Day 5: Tag Score API Endpoints

**Goal:** Expose tag scoring via API

**Tasks:**
- [ ] Add `/api/papers/:id/scores` endpoint (includes tag_score)
- [ ] Add `/api/tags/trending` endpoint (sorted by growth_rate)
- [ ] Add `/api/tags/combos` endpoint (novel combinations)
- [ ] Add background job to recalculate tag stats (optional)

**Deliverables:**
- GET `/api/papers/:id/scores` - Returns all scores for a paper
- GET `/api/tags/trending?limit=20` - Trending tags
- GET `/api/tags/combos?novel_only=true` - Tag combinations

---

## Week 2: Citation Scoring System

### Day 6-7: Citation Network Building

**Goal:** Build and store citation graphs

**Tasks:**
- [ ] Enhance Semantic Scholar connector
  - [ ] Fetch citations for paper
  - [ ] Fetch references for paper
- [ ] Create `build_citation_network()` function
  - [ ] Store citations in citations table
  - [ ] Handle missing papers (create stub entries)
  - [ ] Avoid duplicates
- [ ] Add `/api/papers/:id/citations` POST endpoint
  - [ ] Rate limited (10/hour per user)
  - [ ] Queues citation fetch job

**Deliverables:**
```python
# ara_v2/services/citation_builder.py
def build_citation_network(paper_id: int, depth: int = 1):
    """Fetch and store citation network for a paper."""
    pass

def get_inbound_citations(paper_id: int) -> List[Paper]:
    """Get papers that cite this paper."""
    pass

def get_outbound_citations(paper_id: int) -> List[Paper]:
    """Get papers this paper cites."""
    pass
```

### Day 8-9: Citation Score Algorithm

**Goal:** Calculate citation-based ranking

**Tasks:**
- [ ] Create `ara_v2/services/scoring/citation_scorer.py`
- [ ] Implement three components:
  - [ ] Direct citation count (log scale)
  - [ ] Citation quality (2nd-order citations)
  - [ ] Co-citation cluster strength
- [ ] Implement percentile normalization
- [ ] Cache scores in papers.citation_score column

**Deliverables:**
```python
# ara_v2/services/scoring/citation_scorer.py
def calculate_citation_score(paper_id: int) -> float:
    """Calculate Citation Score (0-100)."""
    pass

def calculate_co_citation_strength(paper_id: int) -> float:
    """Measure clustering via co-citations."""
    pass

def get_citation_percentile(raw_score: float) -> float:
    """Convert raw score to percentile rank."""
    pass
```

### Day 10: Citation Score Integration

**Goal:** Integrate citation scoring into API

**Tasks:**
- [ ] Update `/api/papers/:id/scores` to include citation_score
- [ ] Add `/api/papers/highly-cited?limit=50` endpoint
- [ ] Create background job for batch citation score updates
- [ ] Add citation score to paper ingestion pipeline

---

## Week 3: Novelty Scoring with Claude API

### Day 11-12: Novelty Signal Detection

**Goal:** Identify papers that warrant Claude evaluation

**Tasks:**
- [ ] Create `ara_v2/services/scoring/novelty_detector.py`
- [ ] Implement tag novelty detection
  - [ ] Check for new tags (frequency == 1)
  - [ ] Check for rare tag combos (frequency <= 3)
  - [ ] Calculate combo rarity score
- [ ] Implement trigger logic
  - [ ] Should evaluate if: new tag OR rare combo OR rarity_score > 0.5
- [ ] Create novelty signal report

**Deliverables:**
```python
# ara_v2/services/scoring/novelty_detector.py
def detect_tag_novelty(paper_id: int) -> dict:
    """
    Returns: {
        'has_new_tag': bool,
        'has_rare_combo': bool,
        'combo_rarity_score': float,
        'new_tag_names': List[str],
        'rare_combo_tags': List[List[str]]
    }
    """
    pass

def should_trigger_llm_evaluation(novelty_signals: dict) -> bool:
    """Determine if Claude evaluation is warranted."""
    pass
```

### Day 13-14: Claude API Integration

**Goal:** Implement novelty evaluation with Claude

**Tasks:**
- [ ] Create `ara_v2/services/claude_evaluator.py`
- [ ] Implement prompt template for novelty evaluation
  - [ ] Include title, abstract, novelty signals
  - [ ] Request JSON response with verdict + reasoning
- [ ] Implement Claude API call with budget checking
  - [ ] Check daily/monthly budget before calling
  - [ ] Deduct cost after successful call
  - [ ] Queue evaluation if budget exhausted
- [ ] Store evaluation in novelty_evals table
  - [ ] Save prompt, response, verdict, confidence
  - [ ] Update paper.novelty_score

**Deliverables:**
```python
# ara_v2/services/claude_evaluator.py
def evaluate_novelty_with_claude(
    paper_id: int,
    novelty_signals: dict
) -> dict:
    """
    Returns: {
        'verdict': 'highly_novel'|'moderately_novel'|'incremental'|'derivative',
        'confidence': float,
        'reasoning': str,
        'key_novelty_claims': List[str]
    }
    """
    pass

def queue_pending_evaluations():
    """Process pending evals when budget available."""
    pass
```

### Day 15: Novelty Score Calculation

**Goal:** Calculate final novelty score

**Tasks:**
- [ ] Create `ara_v2/services/scoring/novelty_scorer.py`
- [ ] Implement scoring logic:
  - [ ] Base score from tag signals (0-50 points)
  - [ ] Claude verdict bonus (0-50 points)
    - highly_novel: +50
    - moderately_novel: +30
    - incremental: +10
    - derivative: +0
  - [ ] Multiply by Claude confidence
- [ ] Integrate into paper ingestion pipeline
- [ ] Add fallback for papers without Claude eval

**Deliverables:**
```python
# ara_v2/services/scoring/novelty_scorer.py
def calculate_novelty_score(paper_id: int) -> float:
    """Calculate Novelty Score (0-100)."""
    pass

def calculate_novelty_score_no_llm(paper_id: int) -> float:
    """Fallback novelty score without Claude."""
    pass
```

---

## Week 4: HOLMES Composite Score + Diamonds

### Day 16-17: HOLMES Score Calculation

**Goal:** Combine all scores into HOLMES composite

**Tasks:**
- [ ] Create `ara_v2/services/scoring/holmes_scorer.py`
- [ ] Implement weighted combination:
  - [ ] Default weights: Tag 35%, Citation 40%, Novelty 25%
  - [ ] Allow custom weight configurations
- [ ] Add recency boost for recent papers
- [ ] Calculate percentile rank across all papers
- [ ] Store in papers.holmes_score column

**Deliverables:**
```python
# ara_v2/services/scoring/holmes_scorer.py
def calculate_holmes_score(
    paper_id: int,
    weights: dict = None
) -> float:
    """
    Calculate HOLMES composite score (0-100).

    Default weights: {'tag': 0.35, 'citation': 0.40, 'novelty': 0.25}
    """
    pass

def get_holmes_percentile(paper_id: int) -> float:
    """Get percentile rank (0-100)."""
    pass

def apply_recency_boost(score: float, publish_date: datetime) -> float:
    """Boost recent papers (published within 6 months)."""
    pass
```

### Day 18: Diamond Detection

**Goal:** Identify top 10% papers (Diamonds)

**Tasks:**
- [ ] Implement diamond classification logic
  - [ ] HOLMES score >= 90th percentile = Diamond
  - [ ] OR Novelty score >= 95th percentile = Diamond
- [ ] Add `papers.is_diamond` boolean column (migration)
- [ ] Create background job to update diamond status
- [ ] Add `/api/papers/diamonds` endpoint

**Deliverables:**
```python
# ara_v2/services/scoring/diamond_classifier.py
def classify_as_diamond(paper_id: int) -> bool:
    """Determine if paper qualifies as Diamond."""
    pass

def update_all_diamond_status():
    """Batch update diamond flags for all papers."""
    pass

def get_diamond_papers(limit: int = 100) -> List[Paper]:
    """Get top diamond papers."""
    pass
```

### Day 19: Scoring API Endpoints

**Goal:** Expose all scores via API

**Tasks:**
- [ ] Update `/api/papers/:id/scores` to include all scores:
  - [ ] tag_score
  - [ ] citation_score
  - [ ] novelty_score
  - [ ] holmes_score
  - [ ] holmes_percentile
  - [ ] is_diamond
- [ ] Add `/api/papers?sort_by=holmes_score&order=desc`
- [ ] Add `/api/papers/diamonds?limit=50`
- [ ] Add `/api/papers/:id/novelty-evaluation` (Claude details)

**Deliverables:**
- GET `/api/papers/:id/scores` - All scores for a paper
- GET `/api/papers/diamonds` - Top-ranked papers
- GET `/api/papers/:id/novelty-evaluation` - Claude eval details

### Day 20-21: Testing & Optimization

**Goal:** Comprehensive testing and performance tuning

**Tasks:**
- [ ] Write unit tests for all scorers
  - [ ] TagScorer tests
  - [ ] CitationScorer tests
  - [ ] NoveltyScorer tests
  - [ ] HolmesScorer tests
- [ ] Integration tests
  - [ ] Full scoring pipeline
  - [ ] Diamond classification
  - [ ] Claude budget enforcement
- [ ] Performance optimization
  - [ ] Add indexes for score queries
  - [ ] Cache score calculations
  - [ ] Batch score updates
- [ ] Load testing
  - [ ] Concurrent score requests
  - [ ] Large citation networks
- [ ] Bug fixes and polish

**Test Coverage Goals:**
- Unit tests: 90%+ coverage on scoring modules
- Integration tests: Full paper ingestion → scoring → classification flow
- Performance: Score calculation < 500ms per paper

---

## Phase 2B: UI Enhancements (Week 5)

### Milestone Criteria

- [ ] Display auto-assigned tags on papers
- [ ] Show paper sources (ArXiv, S2, CrossRef)
- [ ] Add paper recommendation engine
- [ ] Better search filters

### Day 22-23: Enhanced Paper Display

**Goal:** Improve paper presentation with scores and metadata

**Tasks:**
- [ ] Update paper detail view to show:
  - [ ] Auto-assigned tags with confidence scores
  - [ ] Paper source (ArXiv, S2, CrossRef) with icon
  - [ ] All scores (Tag, Citation, Novelty, HOLMES)
  - [ ] Diamond badge if applicable
  - [ ] Novelty signals (new tags, rare combos)
- [ ] Update paper list view to show:
  - [ ] Source badge
  - [ ] HOLMES score badge
  - [ ] Diamond indicator
- [ ] Add score visualizations
  - [ ] Bar charts for score breakdown
  - [ ] Percentile indicators

**Deliverables:**
- Enhanced GET `/api/papers/:id` response with full metadata
- Frontend component updates (if applicable)

### Day 24: Paper Recommendation Engine

**Goal:** "Papers like this" feature

**Tasks:**
- [ ] Create `ara_v2/services/recommendation_engine.py`
- [ ] Implement recommendation strategies:
  - [ ] Tag similarity (Jaccard index)
  - [ ] Citation network proximity
  - [ ] Co-citation analysis
  - [ ] HOLMES score similarity
- [ ] Create `/api/papers/:id/recommendations` endpoint
  - [ ] Returns top 10 related papers
  - [ ] Includes similarity score and reason
- [ ] Add "Similar papers" section to paper detail view

**Deliverables:**
```python
# ara_v2/services/recommendation_engine.py
def get_recommendations(
    paper_id: int,
    strategy: str = 'hybrid',
    limit: int = 10
) -> List[dict]:
    """
    Returns: [
        {
            'paper_id': int,
            'paper': Paper,
            'similarity_score': float,
            'reason': 'shared_tags' | 'co_cited' | 'similar_score'
        }
    ]
    """
    pass

def calculate_tag_similarity(paper_id1: int, paper_id2: int) -> float:
    """Jaccard similarity of tag sets."""
    pass

def calculate_citation_proximity(paper_id1: int, paper_id2: int) -> float:
    """Citation network distance."""
    pass
```

API Endpoint:
- GET `/api/papers/:id/recommendations?strategy=hybrid&limit=10`

### Day 25: Advanced Search Filters

**Goal:** Richer search and filtering options

**Tasks:**
- [ ] Enhance `/api/papers/search` endpoint with:
  - [ ] Filter by source: `?source=arxiv,semantic_scholar`
  - [ ] Filter by score ranges: `?min_holmes_score=80`
  - [ ] Filter by diamond status: `?diamonds_only=true`
  - [ ] Filter by novelty: `?novel_only=true`
  - [ ] Filter by tag combinations: `?tags=interpretability,alignment`
  - [ ] Sort by multiple criteria: `?sort_by=holmes_score,citation_count`
- [ ] Add tag-based search:
  - [ ] `/api/papers?tags=mechanistic_interpretability,circuits`
  - [ ] AND/OR logic support
- [ ] Add faceted search results:
  - [ ] Include counts by source
  - [ ] Include score distribution
  - [ ] Include tag frequency

**Deliverables:**
Enhanced search endpoint:
```
POST /api/papers/search
{
    "query": "interpretability",
    "sources": ["semantic_scholar", "arxiv"],
    "tags": ["mechanistic_interpretability"],
    "min_holmes_score": 70,
    "diamonds_only": false,
    "novel_only": true,
    "year_from": 2023,
    "sort_by": "holmes_score",
    "order": "desc",
    "page": 1,
    "per_page": 20
}

Response:
{
    "papers": [...],
    "total_count": 145,
    "facets": {
        "by_source": {"arxiv": 89, "semantic_scholar": 56},
        "score_ranges": {"90-100": 12, "80-90": 34, ...},
        "top_tags": ["interpretability": 98, "neural_networks": 67]
    },
    "filters_applied": {...}
}
```

### Day 26: Polish & Documentation

**Goal:** Final polish and comprehensive documentation

**Tasks:**
- [ ] Update API-DOCUMENTATION.md with:
  - [ ] All new scoring endpoints
  - [ ] Recommendation endpoint
  - [ ] Enhanced search filters
  - [ ] Score calculation explanations
- [ ] Create PHASE-2-COMPLETE.md summary
- [ ] Add inline code documentation
- [ ] Create example API calls for:
  - [ ] Scoring workflows
  - [ ] Recommendation usage
  - [ ] Advanced search
- [ ] Performance review
  - [ ] Add database indexes for new queries
  - [ ] Optimize slow endpoints
- [ ] User acceptance testing
  - [ ] Test all new features end-to-end
  - [ ] Fix any UI/UX issues

**Deliverables:**
- Complete API documentation
- Phase 2 completion summary
- Performance benchmarks
- User guide for new features

---

## Dependencies & Prerequisites

### Required Services (Already Set Up ✅)
- PostgreSQL database
- Redis instance
- Claude API key (for novelty evaluation)

### New Database Migrations

```bash
# Migration 011: Add score columns to papers
- papers.tag_score (DECIMAL)
- papers.citation_score (DECIMAL)
- papers.novelty_score (DECIMAL)
- papers.holmes_score (DECIMAL)
- papers.is_diamond (BOOLEAN)

# Migration 012: Add indexes for scoring queries
- Index on papers.holmes_score
- Index on papers.is_diamond
- Index on papers.citation_score

# Migration 013: Novelty evaluation tracking
- (Table already exists from Phase 1 ✅)
```

### Environment Variables

```bash
# Claude API (NEW)
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_DAILY_BUDGET=5.00
CLAUDE_MONTHLY_BUDGET=50.00
CLAUDE_CALLS_PER_MINUTE=5
CLAUDE_CALLS_PER_HOUR=100

# Scoring Configuration
DEFAULT_TAG_WEIGHT=0.35
DEFAULT_CITATION_WEIGHT=0.40
DEFAULT_NOVELTY_WEIGHT=0.25
DIAMOND_PERCENTILE_THRESHOLD=90
```

---

## File Structure

### New Files to Create

```
ara_v2/
├── services/
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── tag_scorer.py          (NEW)
│   │   ├── citation_scorer.py     (NEW)
│   │   ├── novelty_detector.py    (NEW)
│   │   ├── novelty_scorer.py      (NEW)
│   │   ├── holmes_scorer.py       (NEW)
│   │   └── diamond_classifier.py  (NEW)
│   ├── claude_evaluator.py        (NEW)
│   ├── citation_builder.py        (NEW)
│   └── recommendation_engine.py   (NEW - Phase 2B)
├── api/
│   └── endpoints/
│       └── scores.py              (NEW)
└── alembic/
    └── versions/
        ├── 011_add_score_columns.py (NEW)
        └── 012_add_score_indexes.py (NEW)

tests/
├── unit/
│   ├── test_tag_scorer.py         (NEW)
│   ├── test_citation_scorer.py    (NEW)
│   ├── test_novelty_detector.py   (NEW)
│   ├── test_novelty_scorer.py     (NEW)
│   ├── test_holmes_scorer.py      (NEW)
│   └── test_recommendations.py    (NEW - Phase 2B)
└── integration/
    └── test_scoring_pipeline.py   (NEW)
```

---

## Testing Strategy

### Unit Tests (150+ new tests)

**Tag Scorer (30 tests)**
- Tag weight calculation with different frequencies
- Recency multiplier decay
- Growth bonus calculation
- Score normalization
- Edge cases (no tags, max tags)

**Citation Scorer (30 tests)**
- Direct citation count
- Citation quality calculation
- Co-citation strength
- Percentile normalization
- Missing citation data handling

**Novelty Detector (25 tests)**
- New tag detection
- Rare combo detection
- Rarity score calculation
- Trigger logic
- Edge cases

**Novelty Scorer (25 tests)**
- Claude evaluation parsing
- Verdict-to-score mapping
- Confidence weighting
- Fallback scoring (no Claude)
- Budget enforcement

**HOLMES Scorer (25 tests)**
- Weighted combination
- Custom weights
- Recency boost
- Percentile calculation
- Edge cases

**Diamond Classifier (15 tests)**
- Diamond threshold logic
- Batch classification
- Edge cases

**Recommendation Engine (20 tests - Phase 2B)**
- Tag similarity
- Citation proximity
- Hybrid recommendations
- Ranking logic

### Integration Tests (30 tests)

- Full paper ingestion → scoring pipeline
- Citation network building → citation score
- Novel paper detection → Claude eval → novelty score
- HOLMES score calculation → diamond classification
- Recommendation generation
- Advanced search with filters

### Performance Tests

- Score calculation latency (target: <500ms)
- Citation network fetching (target: <5s for depth=1)
- Claude API call (target: <3s)
- Recommendation generation (target: <1s)
- Batch scoring (target: 1000 papers in <10 min)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Claude API costs exceed budget | Daily/monthly limits enforced; queue system for pending evals |
| Citation data unavailable | Fallback score based on available data; graceful degradation |
| Slow score calculations | Cache scores; batch updates; add database indexes |
| Novel tag combos too frequent | Adjust rarity threshold; require multiple signals |
| HOLMES weights not optimal | Make weights configurable; A/B testing capability |

---

## Success Metrics

### Technical Metrics
- All 6 scoring components implemented and tested
- Test coverage >90% on scoring modules
- Score calculation latency <500ms
- Diamond classification accuracy validated by manual review

### Business Metrics
- >80% of papers have complete HOLMES scores
- Diamond papers represent ~10% of total (by design)
- Claude evaluation costs stay within budget (<$50/month)
- Citation networks built for >50% of papers

### User Metrics (Phase 2B)
- Users can filter by scores
- Users can discover recommendations
- Users see source attribution
- Advanced search improves discovery

---

## Phase 2 Completion Criteria

**Must Have:**
1. ✅ Tag Score calculated for all papers
2. ✅ Citation Score calculated (where data available)
3. ✅ Novelty detection identifies candidates
4. ✅ Claude evaluation working with budget controls
5. ✅ HOLMES composite score calculated
6. ✅ Diamond papers auto-flagged
7. ✅ All scores exposed via API
8. ✅ Paper recommendations working
9. ✅ Enhanced search filters
10. ✅ UI displays scores and sources

**Nice to Have (move to Phase 3 if time-constrained):**
- Background workers for batch scoring
- Score history tracking over time
- A/B testing for weight optimization
- Advanced co-citation clustering

---

## Handoff to Phase 3

Before starting Phase 3 (Mind Maps), ensure:
- [ ] All Phase 2 milestone criteria met
- [ ] At least 500 papers scored for testing
- [ ] Claude budget system working correctly
- [ ] Diamond papers validated manually (sample check)
- [ ] All endpoints documented
- [ ] Performance benchmarks met
- [ ] No critical bugs in production

---

## Quick Start Commands

```bash
# Setup (if starting fresh)
source venv/bin/activate
pip install -r requirements.txt

# Database migrations
alembic revision --autogenerate -m "Add score columns to papers"
alembic revision --autogenerate -m "Add score indexes"
alembic upgrade head

# Test scoring system
pytest tests/unit/test_tag_scorer.py -v
pytest tests/unit/test_citation_scorer.py -v
pytest tests/unit/test_holmes_scorer.py -v
pytest tests/integration/test_scoring_pipeline.py -v

# Run with scoring enabled
export FLASK_APP=ara_v2.app
export FLASK_ENV=development
flask run

# Batch score existing papers (example script)
python scripts/batch_score_papers.py --limit=100

# Update diamond status
python scripts/update_diamond_status.py
```

---

## Notes

- **Claude API costs:** Monitor daily. Typical cost: $0.007 per evaluation
- **Citation data:** Semantic Scholar is best source (free, comprehensive)
- **Score weights:** Start with defaults (Tag 35%, Citation 40%, Novelty 25%)
- **Diamond threshold:** 90th percentile is guideline; adjust based on data
- **Recommendation engine:** Start simple (tag similarity), enhance later
- **Testing:** Score calculations are deterministic - good for unit tests

---

## Daily Progress Tracking

Use TodoWrite tool to track:
- [ ] Daily tasks completed
- [ ] Blockers encountered
- [ ] Tests written and passing
- [ ] Documentation updated

---

**Last Updated:** December 16, 2025
**Next Review:** End of Week 1 (Day 5)
**Estimated Completion:** January 20, 2026
