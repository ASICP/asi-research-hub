"""
Quick test to verify the UI improvements are working
"""
import requests

BASE_URL = 'http://localhost:5000/api'

def test_featured_citations():
    """Test that featured papers return citation data"""
    response = requests.get(f"{BASE_URL}/papers/featured")
    
    if response.status_code == 200:
        data = response.json()
        papers = data.get('papers', [])
        
        print(f"✅ Featured Papers: {len(papers)} papers")
        
        # Check first paper for citation fields
        if papers:
            first = papers[0]
            print(f"\n📄 Sample Paper: {first['title'][:50]}...")
            print(f"   ArXiv ID: {first.get('arxiv_id', 'N/A')}")
            print(f"   DOI: {first.get('doi', 'N/A')}")
            
            # Count papers with citations
            with_arxiv = sum(1 for p in papers if p.get('arxiv_id'))
            with_doi = sum(1 for p in papers if p.get('doi'))
            
            print(f"\n📊 Citation Coverage:")
            print(f"   Papers with ArXiv: {with_arxiv}/{len(papers)}")
            print(f"   Papers with DOI: {with_doi}/{len(papers)}")
    else:
        print(f"❌ Failed: {response.status_code}")

if __name__ == '__main__':
    print("🔍 Testing UI Improvements...\n")
    test_featured_citations()
    print("\n✅ Test complete!")
