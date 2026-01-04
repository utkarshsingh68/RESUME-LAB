"""Test the web scraping API endpoints."""
import requests
import json
import time


BASE_URL = "http://localhost:8000"


def test_get_job_sources():
    """Test getting available job sources."""
    print("Testing /api/jobs/sources endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/jobs/sources")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {len(data['sources'])} job sources")
        
        # Show scraping sources
        print("\nWeb Scraping Sources (No API Key Required):")
        for source in data['sources']:
            if source.get('type') == 'scraping':
                print(f"  - {source['display_name']}: {source['description']}")
                print(f"    Configured: {source['configured']}")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        return False


def test_fetch_remotive_jobs():
    """Test fetching jobs from Remotive."""
    print("\nTesting /api/jobs/fetch with Remotive...")
    
    params = {
        'source': 'remotive',
        'query': 'software-dev',
        'limit': 10,
        'append': False
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/fetch", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Job fetch started: {data['message']}")
        
        # Wait a bit for background task to complete
        print("  Waiting for background task to complete...")
        time.sleep(5)
        
        # Check if jobs were saved
        try:
            with open('data/job_listings.json', 'r', encoding='utf-8') as f:
                jobs = json.load(f)
                print(f"✓ Found {len(jobs)} jobs in database")
                
                if jobs:
                    job = jobs[0]
                    print(f"\nSample job:")
                    print(f"  Title: {job['title']}")
                    print(f"  Company: {job['company']}")
                    print(f"  Source: {job['source']}")
                    print(f"  URL: {job['url'][:80]}...")
        except FileNotFoundError:
            print("  ⚠️ Job file not created yet (may still be processing)")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        return False


def test_scrape_all():
    """Test scraping from all sources."""
    print("\nTesting /api/jobs/fetch with scrape_all...")
    
    params = {
        'source': 'scrape_all',
        'limit': 20,
        'append': True
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/fetch", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Scraping started: {data['message']}")
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Web Scraping API Endpoints")
    print("=" * 70)
    
    try:
        # Test 1: Get sources
        result1 = test_get_job_sources()
        
        # Test 2: Fetch from Remotive
        result2 = test_fetch_remotive_jobs()
        
        # Test 3: Scrape from all sources
        result3 = test_scrape_all()
        
        print("\n" + "=" * 70)
        print("Test Results:")
        print(f"Get Job Sources: {'✓ PASSED' if result1 else '✗ FAILED'}")
        print(f"Fetch Remotive: {'✓ PASSED' if result2 else '✗ FAILED'}")
        print(f"Scrape All: {'✓ PASSED' if result3 else '✗ FAILED'}")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the server is running!")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
