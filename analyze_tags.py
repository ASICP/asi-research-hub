import json
import os

RECOMMENDED_TAGS = [
    # Core AI Safety
    'alignment_fundamentals',
    'technical_safety',
    'AI_risks',
    
    # Interpretability
    'mechanistic_interpretability',
    'interpretability',
    'circuits',
    'features',
    'superposition',
    
    # Training & Methods
    'RLHF',
    'constitutional_AI',
    'reward_modeling',
    'scalable_oversight',
    
    # Robustness & Testing
    'robustness',
    'red_teaming',
    'adversarial',
    'jailbreaking',
    
    # Evaluation
    'evaluation',
    'benchmarks',
    'calibration',
    
    # Safety Properties
    'hallucination',
    'truthfulness',
    'uncertainty',
    'deception',
    
    # Governance
    'governance',
    'AI_policy',
    'ethics',
    'regulation',
    
    # Agents & Tools
    'agents',
    'tool_use',
    'web_browsing',
    
    # Research Areas
    'inner_alignment',
    'outer_alignment',
    'mesa_optimization',
    'goal_misgeneralization'
]

def main():
    with open('papers.json', 'r') as f:
        papers = json.load(f)
        
    all_tags = set()
    for p in papers:
        for t in p.get('tags', []):
            all_tags.add(t)
            
    print(f"📊 Tag Analysis:")
    print(f"   Total unique tags in papers.json: {len(all_tags)}")
    
    recommended_set = set(RECOMMENDED_TAGS)
    
    # Check coverage
    used_recommended = all_tags.intersection(recommended_set)
    unused_recommended = recommended_set - all_tags
    other_tags = all_tags - recommended_set
    
    print(f"   Recommended tags used: {len(used_recommended)} / {len(recommended_set)}")
    
    if other_tags:
        print(f"\n⚠️  Tags found that are NOT in recommended list ({len(other_tags)}):")
        # Print first 10
        print(f"   {', '.join(list(other_tags)[:10])}...")
        
    if unused_recommended:
        print(f"\nℹ️  Recommended tags NOT used yet ({len(unused_recommended)}):")
        print(f"   {', '.join(list(unused_recommended))}")

if __name__ == '__main__':
    main()
