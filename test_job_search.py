#!/usr/bin/env python3
"""
Test script for JSearch API integration
Demonstrates fetching jobs from LinkedIn, Indeed, and Glassdoor
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from core.job_fetcher import JobFetcher
from config import settings
import json


def test_jsearch():
    """Test JSearch API integration."""
    
    print("=" * 70)
    print("JSearch API Test - LinkedIn, Indeed, Glassdoor Job Search")
    print("=" * 70)
    
    # Check if API key is configured
    if not settings.RAPIDAPI_KEY:
        print("\n❌ RAPIDAPI_KEY not configured!")
        print("\nSetup Instructions:")
        print("1. Get free API key from: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
        print("2. Add to .env file: RAPIDAPI_KEY=your_key_here")
        print("3. Free tier: 500 requests/month")
        print("\nSee SETUP_JSEARCH.md for detailed instructions.")
        return
    
    print("\n✅ RAPIDAPI_KEY is configured")
    print(f"   Key: {settings.RAPIDAPI_KEY[:10]}...{settings.RAPIDAPI_KEY[-5:]}")
    
    # Initialize job fetcher
    fetcher = JobFetcher()
    
    # Test 1: Fetch Python developer jobs
    print("\n" + "─" * 70)
    print("Test 1: Fetching Python Developer jobs from LinkedIn/Indeed/Glassdoor")
    print("─" * 70)
    
    jobs = fetcher.fetch_jsearch_jobs(
        query="python developer",
        location="United States",
        remote_jobs_only=False,
        limit=5
    )
    
    if jobs:
        print(f"\n✅ Successfully fetched {len(jobs)} jobs!")
        print("\nSample Job:")
        job = jobs[0]
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Location: {job['location']}")
        print(f"  Source: {job['source']}")
        print(f"  Skills: {', '.join(job['skills'][:5])}")
        print(f"  Apply URL: {job['apply_url'][:60]}...")
    else:
        print("\n❌ No jobs fetched. Check your API key or query.")
        return
    
    # Test 2: Fetch remote data science jobs
    print("\n" + "─" * 70)
    print("Test 2: Fetching Remote Data Science jobs")
    print("─" * 70)
    
    jobs = fetcher.fetch_jsearch_jobs(
        query="data scientist",
        location="Remote",
        remote_jobs_only=True,
        limit=3
    )
    
    if jobs:
        print(f"\n✅ Successfully fetched {len(jobs)} remote jobs!")
        for i, job in enumerate(jobs, 1):
            print(f"\n  Job {i}:")
            print(f"    Title: {job['title']}")
            print(f"    Company: {job['company']}")
            print(f"    Source: {job['source']}")
    
    # Test 3: Save jobs to file
    print("\n" + "─" * 70)
    print("Test 3: Saving jobs to database")
    print("─" * 70)
    
    result = fetcher.fetch_and_save(
        source="jsearch",
        query="machine learning engineer",
        location="San Francisco",
        limit=10,
        append=True
    )
    
    if result["success"]:
        print(f"\n✅ {result['message']}")
        print(f"   Saved to: {fetcher.data_path}")
        
        # Show saved jobs count
        with open(fetcher.data_path, 'r') as f:
            all_jobs = json.load(f)
        print(f"   Total jobs in database: {len(all_jobs)}")
    else:
        print(f"\n❌ Failed: {result['message']}")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    
    print("\n📚 Next Steps:")
    print("1. Check saved jobs in: data/job_listings.json")
    print("2. Start the backend: python -m backend.main")
    print("3. Use API endpoint: POST /api/jobs/fetch")
    print("4. See SETUP_JSEARCH.md for more examples")


def test_remoteok():
    """Test RemoteOK API (no auth required)."""
    
    print("\n" + "─" * 70)
    print("Bonus: Testing RemoteOK (Free, No Auth Required)")
    print("─" * 70)
    
    fetcher = JobFetcher()
    
    jobs = fetcher.fetch_remoteok_jobs(
        tags=["python", "remote"],
        limit=5
    )
    
    if jobs:
        print(f"\n✅ Successfully fetched {len(jobs)} jobs from RemoteOK!")
        print("\nSample Job:")
        job = jobs[0]
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Location: {job['location']}")
        print(f"  Skills: {', '.join(job['skills'][:5])}")
    else:
        print("\n❌ No jobs fetched from RemoteOK")


if __name__ == "__main__":
    test_jsearch()
    test_remoteok()
