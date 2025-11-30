import json
import os
import re

def load_json_file(filepath):
    """Load JSON file, handling potential concatenation errors and comments"""
    if not os.path.exists(filepath):
        return []
        
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
            
        if not content:
            return []

        # Try to find the JSON array part
        # Look for the first '[' and last ']'
        start_idx = content.find('[')
        end_idx = content.rfind(']')
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx+1]
            
            # Remove comments (// ...)
            json_str = re.sub(r'//.*', '', json_str)
            
            # Fix potential trailing commas before closing braces/brackets
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON Decode Error in extracted block: {e}")
                # Fallback to raw decode loop if simple load fails
                pass
        
        # Fallback: Try to parse object by object
        objects = []
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(content):
            try:
                # Skip non-json garbage
                while pos < len(content) and content[pos] not in '{[':
                    pos += 1
                
                if pos >= len(content):
                    break
                    
                obj, idx = decoder.raw_decode(content[pos:])
                if isinstance(obj, list):
                    objects.extend(obj)
                elif isinstance(obj, dict):
                    objects.append(obj)
                pos += idx
            except:
                pos += 1 # Advance if decode fails
                
        return objects
            
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return []

def main():
    # Load existing papers
    existing_papers = load_json_file('papers.json')
    print(f"📂 Existing database: {len(existing_papers)} papers")
    
    # Load incoming papers
    incoming_papers = load_json_file('papers_incoming.json')
    print(f"📂 Incoming file: {len(incoming_papers)} entries")
    
    # Track unique papers by filename (normalization)
    paper_map = {}
    
    # 1. Load existing into map
    for p in existing_papers:
        fname = p.get('filename', '').strip()
        if fname:
            paper_map[fname] = p
            
    initial_count = len(paper_map)
    
    # 2. Process incoming
    duplicates_in_incoming = 0
    new_added = 0
    
    seen_incoming_filenames = set()
    
    for p in incoming_papers:
        fname = p.get('filename', '').strip()
        if not fname:
            continue
            
        if fname in seen_incoming_filenames:
            duplicates_in_incoming += 1
            continue
        seen_incoming_filenames.add(fname)
        
        # Check against existing
        if fname in paper_map:
            # It's a duplicate with existing. 
            pass 
        else:
            # It's new
            paper_map[fname] = p
            new_added += 1
            
    # Save result
    final_list = list(paper_map.values())
    
    with open('papers.json', 'w') as f:
        json.dump(final_list, f, indent=4)
        
    print(f"\n==========================================")
    print(f"📊 MERGE REPORT")
    print(f"==========================================")
    print(f"Incoming Entries:      {len(incoming_papers)}")
    print(f"Duplicates (Internal): {duplicates_in_incoming}")
    print(f"Already in DB:         {len(incoming_papers) - duplicates_in_incoming - new_added}")
    print(f"✅ New Added:          {new_added}")
    print(f"------------------------------------------")
    print(f"Total Unique Papers:   {len(final_list)}")
    print(f"==========================================")

if __name__ == '__main__':
    main()
