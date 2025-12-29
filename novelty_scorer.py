"""
Novelty scoring system for Novel Ideas & Tools.
Scores papers based on recency, interdisciplinary signals, tooling, and contrarian approaches.
"""
from datetime import datetime, timedelta
import re

class NoveltyScorer:
    """Score papers for novelty based on multiple criteria."""

    NEURO_KEYWORDS = ['neuroscience', 'neural', 'brain', 'cognitive', 'cortex', 'synapse']
    GOVERNANCE_KEYWORDS = ['data governance', 'data security', 'privacy', 'regulation', 'policy']
    INTERDISCIPLINARY_KEYWORDS = ['economics', 'philosophy', 'biology', 'sociology', 'psychology']
    TOOLING_KEYWORDS = ['framework', 'toolkit', 'method', 'benchmark', 'library', 'platform', 'tool']
    CONTRARIAN_KEYWORDS = ['critique', 'alternative', 'rethinking', 'challenges', 'reconsidering', 'contrary']

    @staticmethod
    def score_paper(paper):
        """Score a paper for novelty (0-100 points). Returns: (total_score, breakdown_dict)"""
        scores = {'recency': 0, 'interdisciplinary': 0, 'tooling': 0, 'contrarian': 0, 'impact': 0}
        text = f"{paper.title} {paper.abstract or ''}".lower()
        scores['recency'] = NoveltyScorer._score_recency(paper)
        scores['interdisciplinary'] = NoveltyScorer._score_interdisciplinary(text)
        scores['tooling'] = NoveltyScorer._score_tooling(text, paper)
        scores['contrarian'] = NoveltyScorer._score_contrarian(text, paper)
        scores['impact'] = NoveltyScorer._score_impact(scores)
        return sum(scores.values()), scores

    @staticmethod
    def _score_recency(paper):
        if not paper.created_at:
            return 0
        days_old = (datetime.utcnow() - paper.created_at).days
        if days_old <= 30:
            return 20
        elif days_old <= 60:
            return 15
        elif days_old <= 90:
            return 10
        return 0

    @staticmethod
    def _score_interdisciplinary(text):
        has_ai = any(w in text for w in ['ai ', 'artificial intelligence', 'machine learning', 'alignment'])
        if not has_ai:
            return 0
        if any(w in text for w in NoveltyScorer.NEURO_KEYWORDS):
            return 25
        if any(w in text for w in NoveltyScorer.GOVERNANCE_KEYWORDS):
            return 25
        if any(w in text for w in NoveltyScorer.INTERDISCIPLINARY_KEYWORDS):
            return 20
        return 0

    @staticmethod
    def _score_tooling(text, paper):
        score = 0
        if paper.pdf_url and ('github.com' in paper.pdf_url or 'gitlab.com' in paper.pdf_url):
            score += 15
        if any(w in text for w in NoveltyScorer.TOOLING_KEYWORDS):
            score += 10
        return min(score, 25)

    @staticmethod
    def _score_contrarian(text, paper):
        score = 0
        if any(w in text for w in NoveltyScorer.CONTRARIAN_KEYWORDS):
            score += 15
        if paper.citation_count < 10 and NoveltyScorer._score_recency(paper) >= 10:
            score += 10
        return min(score, 15)

    @staticmethod
    def _score_impact(scores):
        criteria_met = sum([
            scores['recency'] >= 15,
            scores['interdisciplinary'] >= 20,
            scores['tooling'] >= 15,
            scores['contrarian'] >= 10
        ])
        return {4: 25, 3: 15, 2: 8, 1: 3}.get(criteria_met, 0)