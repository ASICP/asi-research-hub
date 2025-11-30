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
        start_idx = content.find('[')
        end_idx = content.rfind(']')
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx+1]
            json_str = re.sub(r'//.*', '', json_str)
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            try:
                return json.loads(json_str)
            except:
                pass
        
        # Fallback: Try to parse object by object
        objects = []
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(content):
            try:
                while pos < len(content) and content[pos] not in '{[':
                    pos += 1
                if pos >= len(content): break
                obj, idx = decoder.raw_decode(content[pos:])
                if isinstance(obj, list): objects.extend(obj)
                elif isinstance(obj, dict): objects.append(obj)
                pos += idx
            except:
                pos += 1
        return objects
            
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return []

def main():
    # Load existing papers
    existing_papers = load_json_file('papers.json')
    print(f"📂 Existing database: {len(existing_papers)} papers")
    
    # Load incoming papers
    incoming_papers = load_json_file('papers_incoming_final.json')
    print(f"📂 Incoming file: {len(incoming_papers)} entries")
    
    # Track unique papers by filename
    existing_filenames = set()
    for p in existing_papers:
        fname = p.get('filename', '').strip()
        if fname: existing_filenames.add(fname)
            
    # Analyze incoming
    new_entries = []
    seen_incoming = set()
    incoming_citations = 0
    
    for p in incoming_papers:
        fname = p.get('filename', '').strip()
        if not fname: continue
        
        # Count citations for this paper regardless of duplicate status (user asked for run on "this file")
        # But usually we want total citations of the *new* stuff or the *total* stuff?
        # User said "run a citation count on this file". So I will count citations in the incoming file.
        c = p.get('citation_count', 0)
        if isinstance(c, str):
            try: c = int(c.replace(',', ''))
            except: c = 0
        incoming_citations += c
            
        if fname in seen_incoming: continue
        seen_incoming.add(fname)
        
        if fname not in existing_filenames:
            new_entries.append(p)
            
    print(f"\n==========================================")
    print(f"📊 ANALYSIS REPORT")
    print(f"==========================================")
    print(f"Incoming Total Entries: {len(incoming_papers)}")
    print(f"Incoming Citation Sum:  {incoming_citations}")
    print(f"------------------------------------------")
    print(f"Already in DB:          {len(seen_incoming) - len(new_entries)}")
    print(f"✅ New Entries to Add:  {len(new_entries)}")
    print(f"==========================================")

if __name__ == '__main__':
    main()
