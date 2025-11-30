import requests
import sys

BASE_URL = 'http://localhost:5000/api'

def check_endpoint(name, url, expected_status=200):
    try:
        response = requests.get(url)
        status = response.status_code
        if status == expected_status:
            print(f"✅ {name}: OK ({status})")
            return True, response.json()
        else:
            print(f"❌ {name}: Failed ({status})")
            return False, None
    except Exception as e:
        print(f"❌ {name}: Error ({e})")
        return False, None

def main():
    print("🔍 Starting Application Audit...")
    print(f"   Target: {BASE_URL}")
    print("----------------------------------------")
    
    # 1. Health Check
    ok, data = check_endpoint("Health Check", f"{BASE_URL}/health")
    if not ok:
        print("⚠️  Critical: Health check failed. Is the app running?")
        sys.exit(1)
        
    # 2. Featured Papers
    ok, data = check_endpoint("Featured Papers", f"{BASE_URL}/papers/featured")
    if ok:
        count = len(data)
        print(f"   -> Found {count} featured papers")
        if count == 0:
            print("   ⚠️  Warning: No featured papers returned")
            
    # 3. Search Test (General)
    ok, data = check_endpoint("Search 'alignment'", f"{BASE_URL}/search?q=alignment")
    if ok:
        count = len(data.get('results', []))
        print(f"   -> Found {count} results for 'alignment'")
        if count == 0:
            print("   ⚠️  Warning: Search returned 0 results")
            
    # 4. Search Test (Specific)
    ok, data = check_endpoint("Search 'interpretability'", f"{BASE_URL}/search?q=interpretability")
    if ok:
        count = len(data.get('results', []))
        print(f"   -> Found {count} results for 'interpretability'")

    # 5. Search Test (Tag)
    ok, data = check_endpoint("Tag Search 'RLHF'", f"{BASE_URL}/search?tag=RLHF")
    if ok:
        count = len(data.get('results', []))
        print(f"   -> Found {count} results for tag 'RLHF'")

    print("----------------------------------------")
    print("✅ Audit Complete")

if __name__ == '__main__':
    main()
