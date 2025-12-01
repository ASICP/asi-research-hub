"""
ASI Research Hub - Updated Configuration
Updated: November 28, 2025
Changes: Comprehensive AI Safety & Alignment tag taxonomy
"""

import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ALGORITHM = 'HS256'
    
    # Database settings (PostgreSQL)
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/asi_research_hub')
    
    # SendGrid settings
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@asi2.org')
    
    # Frontend URL (for CORS and email links)
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5000')
    
    # API settings
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
    PERPLEXITY_MONTHLY_LIMIT = 500  # Hard limit: 500 searches per month
    
    # reCAPTCHA settings
    RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY', '')
    RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY', '')
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}
    
    # Pagination
    PAPERS_PER_PAGE = 20
    
    # User tiers
    USER_TIERS = ['student', 'researcher', 'government', 'corporate']
    
    # User regions (in order)
    USER_REGIONS = ['Asia', 'Africa', 'Europe', 'Oceania', 'N. America', 'S. America']
    
    # ============================================================================
    # UPDATED: COMPREHENSIVE AI SAFETY & ALIGNMENT TAG TAXONOMY
    # ============================================================================
    # Based on AI Safety research standards (2025)
    # Organized by research category for better navigation
    
    VALID_TAGS = [
        # ========== CORE AI SAFETY ==========
        'alignment_fundamentals',      # Core alignment theory and concepts
        'technical_safety',            # Technical approaches to AI safety
        'AI_risks',                    # Existential and catastrophic risks
        'AI_ethics',                   # Ethical considerations and frameworks
        'AI_policy',                   # Policy and regulatory approaches
        'governance',                  # AI governance frameworks
        'regulation',                  # Regulatory mechanisms and standards
        
        # ========== ALIGNMENT RESEARCH ==========
        'inner_alignment',             # Mesa-optimizer alignment
        'outer_alignment',             # Objective specification
        'mesa_optimization',           # Inner optimizers and learned optimization
        'goal_misgeneralization',      # Goals generalizing incorrectly
        'deceptive_alignment',         # Deceptive or misaligned behavior
        'value_alignment',             # Aligning with human values
        'scalable_oversight',          # Oversight for superhuman systems
        'constitutional_AI',           # Constitutional AI approaches
        'RLAIF',                       # RL from AI Feedback
        'RLHF',                        # RL from Human Feedback
        'reward_modeling',             # Learning reward functions
        'reward_hacking',              # Gaming reward functions
        'iterated_amplification',      # Amplification approaches
        'debate',                      # Debate for alignment
        'recursive_reward_modeling',   # Recursive RM for scalable oversight
        
        # ========== INTERPRETABILITY ==========
        'mechanistic_interpretability', # Understanding model internals
        'interpretability',            # General interpretability
        'transformer_circuits',        # Circuit-level transformer analysis
        'features',                    # Feature extraction and analysis
        'superposition',               # Feature superposition
        'polysemanticity',             # Neurons representing multiple concepts
        'sparse_autoencoders',         # SAEs for feature extraction
        'monosemanticity',             # One feature per dimension
        'circuits',                    # Neural network circuits
        'activation_engineering',      # Activation-based control
        'steering_vectors',            # Representation steering
        'representation_engineering',  # RepE and control vectors
        'reverse_engineering',         # Reverse engineering models
        
        # ========== CAPABILITIES & EVALUATION ==========
        'evaluation',                  # Model evaluation methods
        'benchmarks',                  # Evaluation benchmarks
        'capabilities',                # Model capabilities assessment
        'emergent_abilities',          # Emergent capabilities
        'scaling_laws',                # Scaling behavior
        'phase_transitions',           # Capability phase transitions
        'generalization',              # Generalization behavior
        'generalization_failure',      # Failed generalization
        'in_context_learning',         # ICL mechanisms
        'induction_heads',             # Induction head circuits
        'world_knowledge',             # Factual knowledge
        'multitask',                   # Multitask learning
        'factual_recall',              # Factual memory
        'bidirectional_inference',     # A→B and B→A reasoning
        'reversal_curse',              # Failure of bidirectional reasoning
        
        # ========== ROBUSTNESS & SAFETY TESTING ==========
        'robustness',                  # General robustness
        'adversarial',                 # Adversarial examples
        'adversarial_attacks',         # Attack methods
        'adversarial_training',        # Training against attacks
        'red_teaming',                 # Red team testing
        'adversarial_testing',         # Adversarial evaluation
        'safety_testing',              # Safety property testing
        'jailbreaking',                # Breaking safety constraints
        'GCG',                         # Greedy Coordinate Gradient attacks
        'backdoors',                   # Backdoor vulnerabilities
        'transferability',             # Attack transferability
        'safety_failures',             # Documented safety failures
        'RLHF_limitations',            # RLHF failure modes
        'alignment_brittleness',       # Fragility of alignment
        'persistent_misalignment',     # Hard-to-remove misalignment
        
        # ========== TRUTHFULNESS & CALIBRATION ==========
        'hallucination',               # False generation
        'truthfulness',                # Truthful output
        'honesty',                     # Honest behavior
        'uncertainty',                 # Uncertainty representation
        'calibration',                 # Probability calibration
        'confidence',                  # Confidence estimation
        'self_knowledge',              # Model knowing its limitations
        'hallucination_detection',     # Detecting hallucinations
        'misinformation',              # Generating misinformation
        'human_falsehoods',            # Mimicking human errors
        
        # ========== TRAINING & METHODS ==========
        'pretraining',                 # Pretraining methods
        'post_training',               # Post-training methods
        'fine_tuning',                 # Fine-tuning approaches
        'human_feedback',              # Human feedback methods
        'human_preferences',           # Learning from preferences
        'conditional_training',        # Conditional training
        'self_improvement',            # Self-supervised improvement
        'distillation',                # Knowledge distillation
        'synthetic_data',              # Synthetic training data
        'data_curation',               # Training data selection
        'sample_efficiency',           # Sample-efficient learning
        'reasoning_alignment',         # Aligning reasoning
        
        # ========== AGENTS & TOOL USE ==========
        'agents',                      # AI agents
        'agent_modeling',              # Modeling agent behavior
        'tool_use',                    # Using external tools
        'web_browsing',                # Web interaction
        'grounding',                   # Grounding in reality
        'decision_making',             # Decision-making processes
        'mental_states',               # Theory of mind
        'theory_of_mind',              # Understanding others' beliefs
        'human_AI_teams',              # Human-AI collaboration
        'orchestration',               # Multi-agent orchestration
        'long_horizon_tasks',          # Extended task completion
        
        # ========== FAILURE MODES & RISKS ==========
        'RL_failure_modes',            # RL-specific failures
        'distributional_shift',        # Distribution shift problems
        'causal_confusion',            # Causal reasoning errors
        'auto_induced_shift',          # Self-caused distribution shift
        'training_stability',          # Training instability
        'optimization_risks',          # Risks from optimization
        'side_effects',                # Unintended side effects
        'safe_exploration',            # Safe RL exploration
        'competing_objectives',        # Conflicting optimization targets
        'limitations',                 # Known limitations
        'unpredictability',            # Unpredictable behavior
        'scale_risks',                 # Risks from scaling
        
        # ========== GOVERNANCE & DOCUMENTATION ==========
        'transparency',                # Model transparency
        'documentation',               # Documentation standards
        'model_cards',                 # Model card reporting
        'responsible_AI',              # Responsible AI practices
        'fairness',                    # Fairness properties
        'bias',                        # Bias detection/mitigation
        'environmental_impact',        # Carbon/energy costs
        'compute_governance',          # Compute-based governance
        'supply_chains',               # Hardware supply chains
        'monitoring',                  # Monitoring systems
        
        # ========== SAFETY PROPERTIES ==========
        'gridworlds',                  # Gridworld environments
        'safety_properties',           # Desired safety properties
        'RL_safety',                   # Reinforcement learning safety
        'harmlessness',                # Avoiding harm
        'deception',                   # Deceptive behavior
        'safety_relevant_features',    # Features important for safety
        'control',                     # Controlling model behavior
        'human_in_the_loop',           # Human oversight
        'automated_testing',           # Automated safety testing
        'offensive_content',           # Harmful content generation
        
        # ========== SPECIALIZED AREAS ==========
        'Claude_Sonnet',               # Claude-specific research
        'feature_extraction',          # Extracting interpretable features
        'sparse_coding',               # Sparse representations
        'comprehensive_evaluation',    # Holistic evaluation
        'safety_metrics',              # Safety measurement
        'question_answering',          # QA systems
        
        # ========== LEGACY/GENERAL TAGS ==========
        # (Keep for backwards compatibility with existing papers)
        'LLM',                         # Large language models (general)
        'transformers',                # Transformer architecture
        'compression',                 # Compression theory
        'foundational_models',         # Foundation models
        'reasoning',                   # Reasoning capabilities
        'clinical_summarization',      # Medical/clinical applications
        'healthcare',                  # Healthcare applications
        'Bayesian_inference',          # Bayesian methods
        'martingale',                  # Martingale theory
        'robotics',                    # Robotics applications
        'bio_inspired',                # Bio-inspired methods
        'reinforcement_learning',      # General RL
    ]
    
    # ============================================================================
    # TAG CATEGORIES FOR UI (Optional: Use for filtering/navigation)
    # ============================================================================
    TAG_CATEGORIES = {
        'Core Safety': [
            'alignment_fundamentals', 'technical_safety', 'AI_risks', 
            'AI_ethics', 'AI_policy', 'governance', 'regulation'
        ],
        'Alignment': [
            'inner_alignment', 'outer_alignment', 'mesa_optimization',
            'goal_misgeneralization', 'deceptive_alignment', 'value_alignment',
            'scalable_oversight', 'constitutional_AI', 'RLAIF', 'RLHF'
        ],
        'Interpretability': [
            'mechanistic_interpretability', 'interpretability', 'transformer_circuits',
            'features', 'superposition', 'polysemanticity', 'sparse_autoencoders',
            'monosemanticity', 'circuits', 'activation_engineering', 'steering_vectors'
        ],
        'Evaluation': [
            'evaluation', 'benchmarks', 'capabilities', 'emergent_abilities',
            'scaling_laws', 'truthfulness', 'calibration'
        ],
        'Robustness': [
            'robustness', 'adversarial', 'adversarial_attacks', 'red_teaming',
            'jailbreaking', 'backdoors', 'safety_testing'
        ],
        'Agents': [
            'agents', 'agent_modeling', 'tool_use', 'web_browsing',
            'decision_making', 'theory_of_mind', 'human_AI_teams'
        ],
        'Governance': [
            'transparency', 'documentation', 'model_cards', 'responsible_AI',
            'fairness', 'bias', 'compute_governance', 'monitoring'
        ]
    }
    
    # ============================================================================
    # TAG DISPLAY NAMES (Optional: Human-readable versions)
    # ============================================================================
    TAG_DISPLAY_NAMES = {
        'AI_risks': 'AI Risks',
        'AI_ethics': 'AI Ethics',
        'AI_policy': 'AI Policy',
        'RLAIF': 'RL from AI Feedback',
        'RLHF': 'RL from Human Feedback',
        'GCG': 'GCG Attacks',
        'RL_safety': 'RL Safety',
        'RL_failure_modes': 'RL Failure Modes',
        'LLM': 'Large Language Models',
        'constitutional_AI': 'Constitutional AI',
        'in_context_learning': 'In-Context Learning',
        # Add more as needed...
    }
    
    # ============================================================================
    # PRIORITY TAGS (Featured on homepage)
    # ============================================================================
    PRIORITY_TAGS = [
        'alignment_fundamentals',
        'mechanistic_interpretability',
        'RLHF',
        'red_teaming',
        'truthfulness',
        'scalable_oversight',
        'deceptive_alignment',
        'adversarial_attacks'
    ]
