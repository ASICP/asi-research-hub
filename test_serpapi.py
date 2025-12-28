"""
Test script to diagnose SerpAPI Google Scholar integration.
Run this to check if your SERPAPI_API_KEY is working correctly.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY', '')

def test_serpapi():
    """Test SerpAPI configuration and connectivity."""

    print("=" * 60)
    print("SerpAPI Google Scholar Diagnostic Test")
    print("=" * 60)

    # Check 1: API Key exists
    print("\n1. Checking API Key Configuration...")
    if not SERPAPI_API_KEY:
        print("   ❌ SERPAPI_API_KEY not found in environment variables")
        print("   → Add SERPAPI_API_KEY to your .env file or Replit Secrets")
        return False
    else:
        # Mask the key for security
        masked_key = SERPAPI_API_KEY[:8] + "..." + SERPAPI_API_KEY[-4:]
        print(f"   ✓ API Key found: {masked_key}")

    # Check 2: Test simple query
    print("\n2. Testing SerpAPI Connection...")
    test_url = "https://serpapi.com/search"

    params = {
        'q': 'AI safety',
        'engine': 'google_scholar',
        'api_key': SERPAPI_API_KEY,
        'num': 5,
        'hl': 'en'
    }

    try:
        response = requests.get(test_url, params=params, timeout=15)
        print(f"   Response Status: {response.status_code}")

        # Check response
        if response.status_code == 200:
            data = response.json()

            # Check for API errors
            if 'error' in data:
                print(f"   ❌ SerpAPI Error: {data['error']}")
                return False

            # Check for results
            organic_results = data.get('organic_results', [])
            if organic_results:
                print(f"   ✓ Successfully fetched {len(organic_results)} results")
                print(f"\n   Sample result:")
                print(f"   Title: {organic_results[0].get('title', 'N/A')}")
                return True
            else:
                print("   ⚠️  No organic results returned")
                print(f"   Full response: {data}")
                return False

        elif response.status_code == 401:
            print("   ❌ Authentication failed - Invalid API key")
            return False

        elif response.status_code == 403:
            print("   ❌ Access forbidden - API key might be deactivated")
            return False

        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (15 seconds)")
        return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {str(e)}")
        return False

    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        return False

def check_quota():
    """Check SerpAPI account quota."""
    print("\n3. Checking Account Quota...")
    print("   Visit https://serpapi.com/dashboard to check your usage")
    print("   Free tier: 100 searches/month")

    # Try to get account info
    account_url = "https://serpapi.com/account"
    try:
        response = requests.get(account_url, params={'api_key': SERPAPI_API_KEY}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   Account info: {data}")
        else:
            print(f"   Could not fetch account info (status {response.status_code})")
    except:
        print("   Could not fetch account info")

if __name__ == "__main__":
    success = test_serpapi()

    if success:
        check_quota()
        print("\n" + "=" * 60)
        print("✓ SerpAPI is configured correctly!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ SerpAPI configuration has issues")
        print("\nTroubleshooting steps:")
        print("1. Get a free API key from https://serpapi.com/")
        print("2. Add it to your .env file: SERPAPI_API_KEY=your_key_here")
        print("3. On Replit: Add to Secrets tab")
        print("4. Check quota at https://serpapi.com/dashboard")
        print("=" * 60)
