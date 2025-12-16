"""
Tag assignment service for ARA v2.
Implements hybrid tag assignment using TF-IDF, rule-based matching, and source-specific tags.
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter
from flask import current_app
from ara_v2.models.tag import Tag
from ara_v2.utils.database import db


class TagAssigner:
    """
    Hybrid tag assignment system combining multiple strategies:
    1. Rule-based matching (keywords and phrases)
    2. TF-IDF extraction (important terms)
    3. Source-specific tagging (ArXiv categories, S2 fields, etc.)
    """

    # Comprehensive tag mapping: tag_name -> list of keywords/phrases
    TAG_KEYWORDS = {
        'interpretability': [
            'interpretability', 'interpret', 'explainability', 'explainable',
            'transparency', 'black box', 'feature visualization', 'saliency',
            'attention mechanism', 'activation atlas'
        ],
        'mechanistic_interpretability': [
            'mechanistic interpretability', 'mechanistic', 'circuits',
            'neuron analysis', 'activation', 'mechanistic understanding',
            'reverse engineering neural', 'neural circuit'
        ],
        'alignment': [
            'alignment', 'value alignment', 'aligned', 'human values',
            'goal alignment', 'preference learning', 'intent alignment'
        ],
        'rlhf': [
            'rlhf', 'reinforcement learning from human feedback',
            'reinforcement learning human', 'rl from human feedback',
            'reward modeling', 'preference modeling'
        ],
        'adversarial_robustness': [
            'adversarial', 'robustness', 'adversarial examples',
            'adversarial attack', 'adversarial training', 'perturbation',
            'robust optimization', 'certified robustness'
        ],
        'safety': [
            'ai safety', 'safety', 'safe ai', 'safety critical',
            'fail-safe', 'safety mechanism'
        ],
        'governance': [
            'governance', 'ai governance', 'policy', 'regulation',
            'oversight', 'compliance', 'standards'
        ],
        'ethics': [
            'ethics', 'ethical', 'moral', 'fairness', 'bias',
            'discrimination', 'justice', 'responsible ai'
        ],
        'risk': [
            'risk', 'existential risk', 'catastrophic', 'dangerous',
            'threat', 'hazard', 'harm'
        ],
        'scalable_oversight': [
            'scalable oversight', 'oversight', 'supervision',
            'recursive reward', 'amplification', 'debate'
        ],
        'reward_hacking': [
            'reward hacking', 'reward gaming', 'specification gaming',
            'goodhart', 'proxy gaming', 'side effects'
        ],
        'inner_alignment': [
            'inner alignment', 'mesa-optimization', 'mesa-optimizer',
            'inner optimizer', 'objective robustness'
        ],
        'outer_alignment': [
            'outer alignment', 'objective specification', 'reward specification',
            'reward function design'
        ],
        'deception': [
            'deception', 'deceptive', 'hidden objectives', 'treacherous turn',
            'misaligned behavior'
        ],
        'capability': [
            'capability', 'performance', 'benchmark', 'state-of-the-art',
            'sota', 'advancement'
        ],
        'llm': [
            'large language model', 'llm', 'language model', 'gpt',
            'transformer', 'bert', 'chatgpt', 'claude'
        ],
        'multimodal': [
            'multimodal', 'vision-language', 'multi-modal', 'clip',
            'vision transformer', 'image-text'
        ],
        'agent': [
            'agent', 'autonomous', 'reinforcement learning', 'rl',
            'policy learning', 'decision making'
        ],
        'uncertainty': [
            'uncertainty', 'confidence', 'calibration', 'epistemic',
            'aleatoric', 'uncertainty quantification'
        ],
        'transparency': [
            'transparency', 'transparent', 'openness', 'disclosure',
            'model cards', 'documentation'
        ],
        'verification': [
            'verification', 'formal verification', 'proof', 'guarantee',
            'certified', 'provable'
        ],
        'testing': [
            'testing', 'evaluation', 'benchmark', 'test suite',
            'validation', 'assessment'
        ],
        'dataset': [
            'dataset', 'corpus', 'benchmark', 'data collection',
            'annotation', 'labeling'
        ],
        'computer_vision': [
            'computer vision', 'image', 'visual', 'object detection',
            'segmentation', 'recognition'
        ],
        'nlp': [
            'natural language processing', 'nlp', 'text', 'language',
            'semantic', 'syntax', 'tokenization'
        ],
        'theoretical': [
            'theoretical', 'theory', 'mathematical', 'formal',
            'analysis', 'proof'
        ],
        'empirical': [
            'empirical', 'experiment', 'experimental', 'evaluation',
            'study', 'case study'
        ],
        'survey': [
            'survey', 'review', 'overview', 'literature review',
            'systematic review'
        ]
    }

    # ArXiv category to tag mapping
    ARXIV_CATEGORY_MAP = {
        'cs.AI': ['ai', 'machine_learning'],
        'cs.LG': ['machine_learning'],
        'cs.CL': ['nlp'],
        'cs.CV': ['computer_vision'],
        'cs.CY': ['governance', 'ethics'],
        'cs.HC': ['human_computer_interaction'],
        'stat.ML': ['machine_learning', 'theoretical'],
    }

    # Semantic Scholar field to tag mapping
    S2_FIELD_MAP = {
        'Computer Science': ['ai'],
        'Machine Learning': ['machine_learning'],
        'Artificial Intelligence': ['ai'],
        'Natural Language Processing': ['nlp'],
        'Computer Vision': ['computer_vision'],
        'Ethics': ['ethics'],
        'Philosophy': ['ethics', 'theoretical'],
    }

    def __init__(self):
        """Initialize the tag assigner."""
        # Compile regex patterns for efficient matching
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for all tag keywords."""
        self.tag_patterns = {}

        for tag_name, keywords in self.TAG_KEYWORDS.items():
            # Create case-insensitive regex pattern for each keyword
            patterns = [
                re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                for keyword in keywords
            ]
            self.tag_patterns[tag_name] = patterns

    def assign_tags(
        self,
        title: str,
        abstract: Optional[str] = None,
        source_fields: Optional[List[str]] = None,
        arxiv_categories: Optional[List[str]] = None,
        min_confidence: float = 0.3,
        max_tags: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Assign tags to a paper using hybrid approach.

        Args:
            title: Paper title (required)
            abstract: Paper abstract (optional but recommended)
            source_fields: Fields from source API (e.g., Semantic Scholar fields)
            arxiv_categories: ArXiv categories if from ArXiv
            min_confidence: Minimum confidence threshold (0-1)
            max_tags: Maximum number of tags to return

        Returns:
            list: List of (tag_name, confidence) tuples, sorted by confidence
        """
        if not title:
            return []

        # Combine text for analysis
        text = title
        if abstract:
            text += " " + abstract

        # Normalize text
        text = text.lower()

        # Strategy 1: Rule-based matching
        rule_based_scores = self._rule_based_matching(text)

        # Strategy 2: TF-IDF extraction (simplified version)
        tfidf_scores = self._tfidf_extraction(text)

        # Strategy 3: Source-specific tags
        source_scores = self._source_specific_tags(source_fields, arxiv_categories)

        # Combine scores with weights
        combined_scores = self._combine_scores(
            rule_based_scores,
            tfidf_scores,
            source_scores,
            weights={'rule': 0.5, 'tfidf': 0.3, 'source': 0.2}
        )

        # Filter by confidence and limit to max_tags
        tags = [
            (tag, score) for tag, score in combined_scores.items()
            if score >= min_confidence
        ]

        # Sort by confidence (descending)
        tags.sort(key=lambda x: x[1], reverse=True)

        return tags[:max_tags]

    def _rule_based_matching(self, text: str) -> Dict[str, float]:
        """
        Match tags using predefined keywords and phrases.

        Args:
            text: Normalized text (title + abstract)

        Returns:
            dict: {tag_name: confidence_score}
        """
        scores = {}

        for tag_name, patterns in self.tag_patterns.items():
            match_count = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                match_count += len(matches)

            if match_count > 0:
                # Confidence based on number of matches (capped at 1.0)
                confidence = min(match_count * 0.3, 1.0)
                scores[tag_name] = confidence

        return scores

    def _tfidf_extraction(self, text: str) -> Dict[str, float]:
        """
        Extract important terms using simplified TF-IDF approach.

        Args:
            text: Normalized text

        Returns:
            dict: {tag_name: relevance_score}
        """
        # Simple implementation: count important unigrams and bigrams
        # In production, you'd use scikit-learn's TfidfVectorizer

        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'be', 'been', 'this', 'that', 'these', 'those', 'we', 'our'
        }

        # Tokenize
        words = re.findall(r'\b\w+\b', text.lower())
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]

        # Count word frequencies
        word_freq = Counter(filtered_words)

        # Map to tags based on keyword matches
        scores = {}
        for tag_name, keywords in self.TAG_KEYWORDS.items():
            # Check if any keyword appears in top terms
            keyword_freq = sum(
                word_freq.get(kw.lower().replace(' ', ''), 0)
                for kw in keywords
            )

            if keyword_freq > 0:
                # Normalize by total word count
                confidence = min(keyword_freq / len(filtered_words), 0.5)
                scores[tag_name] = confidence

        return scores

    def _source_specific_tags(
        self,
        source_fields: Optional[List[str]],
        arxiv_categories: Optional[List[str]]
    ) -> Dict[str, float]:
        """
        Extract tags from source-specific metadata.

        Args:
            source_fields: Fields from Semantic Scholar or CrossRef subjects
            arxiv_categories: ArXiv categories

        Returns:
            dict: {tag_name: confidence_score}
        """
        scores = {}

        # ArXiv categories
        if arxiv_categories:
            for category in arxiv_categories:
                if category in self.ARXIV_CATEGORY_MAP:
                    for tag in self.ARXIV_CATEGORY_MAP[category]:
                        scores[tag] = scores.get(tag, 0) + 0.8

        # Semantic Scholar fields
        if source_fields:
            for field in source_fields:
                # Direct match
                if field in self.S2_FIELD_MAP:
                    for tag in self.S2_FIELD_MAP[field]:
                        scores[tag] = scores.get(tag, 0) + 0.7

                # Fuzzy matching for fields
                field_lower = field.lower()
                for tag_name, keywords in self.TAG_KEYWORDS.items():
                    if any(kw.lower() in field_lower for kw in keywords):
                        scores[tag_name] = scores.get(tag_name, 0) + 0.5

        # Cap all scores at 1.0
        return {tag: min(score, 1.0) for tag, score in scores.items()}

    def _combine_scores(
        self,
        rule_scores: Dict[str, float],
        tfidf_scores: Dict[str, float],
        source_scores: Dict[str, float],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Combine scores from different strategies using weighted average.

        Args:
            rule_scores: Scores from rule-based matching
            tfidf_scores: Scores from TF-IDF extraction
            source_scores: Scores from source-specific tagging
            weights: Weights for each strategy

        Returns:
            dict: Combined scores
        """
        all_tags = set(rule_scores.keys()) | set(tfidf_scores.keys()) | set(source_scores.keys())

        combined = {}
        for tag in all_tags:
            # Calculate weighted sum and track which strategies contributed
            rule_score = rule_scores.get(tag, 0)
            tfidf_score = tfidf_scores.get(tag, 0)
            source_score = source_scores.get(tag, 0)

            weighted_sum = (
                rule_score * weights['rule'] +
                tfidf_score * weights['tfidf'] +
                source_score * weights['source']
            )

            # Normalize by sum of weights that actually contributed (non-zero scores)
            contributing_weight = 0
            if rule_score > 0:
                contributing_weight += weights['rule']
            if tfidf_score > 0:
                contributing_weight += weights['tfidf']
            if source_score > 0:
                contributing_weight += weights['source']

            # Avoid division by zero (though this shouldn't happen)
            if contributing_weight > 0:
                combined[tag] = weighted_sum / contributing_weight
            else:
                combined[tag] = 0

        return combined

    def get_or_create_tags(
        self,
        tag_names: List[str]
    ) -> List[Tag]:
        """
        Get existing tags or create new ones.

        Args:
            tag_names: List of tag names

        Returns:
            list: List of Tag model instances
        """
        tags = []

        for tag_name in tag_names:
            # Try to find existing tag
            tag = Tag.query.filter_by(name=tag_name).first()

            if not tag:
                # Create new tag
                tag = Tag(
                    name=tag_name,
                    slug=tag_name.replace('_', '-'),
                    category='auto_assigned',  # Mark as auto-assigned
                    description=f'Auto-generated tag for {tag_name.replace("_", " ")}'
                )
                db.session.add(tag)

            tags.append(tag)

        return tags

    def assign_and_save_tags(
        self,
        paper,
        min_confidence: float = 0.3,
        max_tags: int = 10
    ) -> List[Tuple[Tag, float]]:
        """
        Assign tags to a paper and save to database.

        Args:
            paper: Paper model instance
            min_confidence: Minimum confidence threshold
            max_tags: Maximum number of tags

        Returns:
            list: List of (Tag, confidence) tuples
        """
        # Extract source-specific fields
        source_fields = None
        arxiv_categories = None

        if paper.source == 'semantic_scholar' and paper.raw_data:
            source_fields = paper.raw_data.get('fieldsOfStudy', [])
        elif paper.source == 'arxiv' and paper.raw_data:
            arxiv_categories = paper.raw_data.get('categories', [])
        elif paper.source == 'crossref' and paper.raw_data:
            source_fields = paper.raw_data.get('subjects', [])

        # Assign tags
        tag_assignments = self.assign_tags(
            title=paper.title,
            abstract=paper.abstract,
            source_fields=source_fields,
            arxiv_categories=arxiv_categories,
            min_confidence=min_confidence,
            max_tags=max_tags
        )

        if not tag_assignments:
            return []

        # Get or create Tag instances
        tag_names = [name for name, _ in tag_assignments]
        tags = self.get_or_create_tags(tag_names)

        # Create mapping of name -> Tag
        tag_map = {tag.name: tag for tag in tags}

        # Return tags with their confidence scores
        result = []
        for tag_name, confidence in tag_assignments:
            if tag_name in tag_map:
                result.append((tag_map[tag_name], confidence))

        current_app.logger.info(
            f"Assigned {len(result)} tags to paper {paper.id}: "
            f"{[t.name for t, _ in result]}"
        )

        return result
