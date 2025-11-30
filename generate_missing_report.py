import json
import os

def main():
    with open('papers.json', 'r') as f:
        papers = json.load(f)
        
    missing = []
    
    for p in papers:
        filename = p.get('filename')
        if not filename: continue
        
        path = os.path.join('static/uploads', filename)
        if not os.path.exists(path):
            missing.append(p.get('title', filename))
            
    output_path = 'missing_papers.txt'
    with open(output_path, 'w') as f:
        f.write("ASI Research Hub - Missing Papers Report\n")
        f.write("========================================\n\n")
        f.write(f"Total Missing PDFs: {len(missing)}\n\n")
        for title in missing:
            f.write(f"- {title}\n")
            
    print(f"✅ Generated {output_path} with {len(missing)} missing papers.")

if __name__ == '__main__':
    main()
