"""Test the web scraping functionality."""
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from core.job_scraper import JobScraper


def test_remotive_scraper():
    """Test Remotive API scraper."""
    print("Testing Remotive scraper...")
    scraper = JobScraper()
    
    jobs = scraper.scrape_remotive(category="software-dev", limit=5)
    
    print(f"Fetched {len(jobs)} jobs from Remotive")
    
    if jobs:
        print("\nSample job:")
        job = jobs[0]
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}")
        print(f"Source: {job['source']}")
    
    return len(jobs) > 0


def test_weworkremotely_scraper():
    """Test WeWorkRemotely scraper."""
    print("\nTesting WeWorkRemotely scraper...")
    scraper = JobScraper()
    
    jobs = scraper.scrape_weworkremotely(category="programming", limit=5)
    
    print(f"Fetched {len(jobs)} jobs from WeWorkRemotely")
    
    if jobs:
        print("\nSample job:")
        job = jobs[0]
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}")
        print(f"Source: {job['source']}")
    
    return len(jobs) > 0


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Job Scraper")
    print("=" * 60)
    
    # Test Remotive (has API endpoint)
    remotive_success = test_remotive_scraper()
    
    # Test WeWorkRemotely (actual scraping)
    wework_success = test_weworkremotely_scraper()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Remotive: {'✓ PASSED' if remotive_success else '✗ FAILED'}")
    print(f"WeWorkRemotely: {'✓ PASSED' if wework_success else '✗ FAILED'}")
    print("=" * 60)
