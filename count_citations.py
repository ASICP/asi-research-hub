import json
import re

def parse_concatenated_json(content):
    """Parse multiple JSON objects from a string"""
    objects = []
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(content):
        content = content.strip()
        if not content:
            break
        try:
            obj, idx = decoder.raw_decode(content[pos:])
            objects.append(obj)
            pos += idx
            # Skip whitespace
            while pos < len(content) and content[pos].isspace():
                pos += 1
        except json.JSONDecodeError:
            # Try to recover if it's just a simple concatenation without whitespace handling issues
            # But raw_decode should handle it. If it fails, maybe there's garbage.
            break
    return objects

try:
    with open('papers_new.json', 'r') as f:
        content = f.read()

    # Try to parse multiple arrays
    lists = parse_concatenated_json(content)
    
    all_papers = []
    for lst in lists:
        if isinstance(lst, list):
            all_papers.extend(lst)
            
    print(f"📄 Found {len(all_papers)} total entries (before deduplication).")
    
    # Deduplicate by filename
    unique_papers = {}
    for paper in all_papers:
        filename = paper.get('filename')
        if not filename:
            continue
            
        # If we already have this paper, keep the one with more info (e.g. higher citation count or non-empty author)
        if filename in unique_papers:
            existing = unique_papers[filename]
            
            # Logic: prefer entry with non-empty title/author
            existing_score = (1 if existing.get('authors') else 0) + (1 if existing.get('citation_count') else 0)
            new_score = (1 if paper.get('authors') else 0) + (1 if paper.get('citation_count') else 0)
            
            if new_score > existing_score:
                unique_papers[filename] = paper
        else:
            unique_papers[filename] = paper
            
    final_list = list(unique_papers.values())
    print(f"✅ Deduplicated to {len(final_list)} unique papers.")
    
    # Calculate citations
    total_citations = 0
    for paper in final_list:
        count = paper.get('citation_count', 0)
        if isinstance(count, str):
            try:
                count = int(count.replace(',', ''))
            except:
                count = 0
        total_citations += count
        
    print(f"📊 Total Citation Count: {total_citations}")
    
    # Save the cleaned file
    with open('papers.json', 'w') as f:
        json.dump(final_list, f, indent=4)
    print("💾 Saved cleaned metadata to papers.json")
    
except Exception as e:
    print(f"❌ Error: {e}")
