"""Quick script to fetch jobs from JSearch API."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.job_fetcher import JobFetcher

def main():
    fetcher = JobFetcher()
    
    print("🔍 Fetching jobs from JSearch (LinkedIn, Indeed, Glassdoor)...")
    
    result = fetcher.fetch_and_save(
        source="jsearch",
        query="python developer data scientist machine learning",
        location="United States",
        remote_only=True,
        limit=100,
        append=False  # Replace existing jobs
    )
    
    print(f"\n✅ Result: {result}")
    print(f"📊 Total jobs fetched: {result.get('count', 0)}")

if __name__ == "__main__":
    main()
