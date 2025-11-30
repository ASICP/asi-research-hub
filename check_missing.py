import json
import os

def main():
    with open('papers.json', 'r') as f:
        papers = json.load(f)
        
    missing = []
    total = len(papers)
    
    print(f"🔍 Checking {total} papers against static/uploads/...")
    
    for p in papers:
        filename = p.get('filename')
        if not filename: continue
        
        path = os.path.join('static/uploads', filename)
        if not os.path.exists(path):
            missing.append(p.get('title', filename))
            
    print(f"\n📊 Results:")
    print(f"   Total in JSON: {total}")
    print(f"   Missing PDFs:  {len(missing)}")
    
    if missing:
        print("\n❌ Missing Papers (Failed to Download):")
        for title in missing:
            print(f"   - {title}")
    else:
        print("\n✅ All papers accounted for!")

if __name__ == '__main__':
    main()
