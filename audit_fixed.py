import requests
import sys

BASE_URL = 'http://localhost:5000/api'

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health Check: OK")
            return True
        else:
            print(f"❌ Health Check: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health Check: Error ({e})")
        return False

def test_featured():
    """Test featured papers endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/papers/featured")
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('papers', []))
            print(f"✅ Featured Papers: OK ({count} papers)")
            return True
        else:
            print(f"❌ Featured Papers: Failed ({response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Featured Papers: Error ({e})")
        return False

def test_tags():
    """Test tags endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/tags")
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('tags', []))
            print(f"✅ Tags: OK ({count} tags)")
            return True
        else:
            print(f"❌ Tags: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Tags: Error ({e})")
        return False

def main():
    print("🔍 ASI Research Hub - System Audit")
    print("=" * 50)
    
    # Test endpoints that don't require auth
    test_health()
    test_featured()
    test_tags()
    
    print("=" * 50)
    print("\nNote: Search endpoints require authentication (JWT)")
    print("      and POST method, so they're not tested here.")
    print("\n✅ Basic audit complete!")

if __name__ == '__main__':
    main()
