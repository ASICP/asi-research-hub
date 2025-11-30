import json
import os

def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return []
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return []

def analyze_papers(papers, name):
    print(f"\n📊 Analyzing {name}:")
    print(f"   Total entries: {len(papers)}")
    
    filenames = [p.get('filename') for p in papers if p.get('filename')]
    unique_filenames = set(filenames)
    duplicates = len(filenames) - len(unique_filenames)
    
    print(f"   Unique filenames: {len(unique_filenames)}")
    print(f"   Internal duplicates: {duplicates}")
    return unique_filenames

def main():
    current_path = 'papers.json'
    updated_path = '/Users/warmachine/Downloads/asi-hub-updates/papers_UPDATED.json'
    new_path = '/Users/warmachine/Downloads/asi-hub-updates/NEW_AI_SAFETY_PAPERS.json'
    
    current_papers = load_json(current_path)
    updated_papers = load_json(updated_path)
    new_papers = load_json(new_path)
    
    current_set = analyze_papers(current_papers, "Current papers.json")
    updated_set = analyze_papers(updated_papers, "papers_UPDATED.json")
    new_set = analyze_papers(new_papers, "NEW_AI_SAFETY_PAPERS.json")
    
    # Compare updated vs current
    common = current_set.intersection(updated_set)
    only_in_current = current_set - updated_set
    only_in_updated = updated_set - current_set
    
    print(f"\n🔄 Comparison (Updated vs Current):")
    print(f"   Common: {len(common)}")
    print(f"   Only in Current: {len(only_in_current)}")
    print(f"   Only in Updated: {len(only_in_updated)}")
    
    # Check if NEW papers are in UPDATED
    new_in_updated = new_set.intersection(updated_set)
    new_not_in_updated = new_set - updated_set
    
    print(f"\n🆕 NEW Papers analysis:")
    print(f"   Already in Updated: {len(new_in_updated)}")
    print(f"   Not in Updated: {len(new_not_in_updated)}")

if __name__ == '__main__':
    main()
