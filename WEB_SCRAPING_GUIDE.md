# Web Scraping Feature - Job Search

## Overview
The Resume Analyzer now includes web scraping capabilities to fetch job listings from various sources without requiring API keys. This expands your job search options beyond API-based sources.

## Available Sources

### 🆓 Free Web Scraping Sources (No API Key Required)

#### 1. **Remotive** ✅ Working
- **Source**: `remotive`
- **Type**: API endpoint (public)
- **Jobs**: Remote jobs across multiple categories
- **Categories**: software-dev, design, marketing, sales, customer-support
- **Rate Limit**: None
- **Status**: ✓ Fully functional

#### 2. **scrape_all** ✅ Working
- **Source**: `scrape_all`
- **Type**: Combined scraping
- **Jobs**: Aggregates from Remotive and other sources
- **Rate Limit**: None
- **Status**: ✓ Fully functional

#### 3. **Y Combinator**
- **Source**: `ycombinator`
- **Type**: Web scraping
- **Jobs**: Startup jobs from Y Combinator companies
- **Status**: ⚠️ Requires JavaScript rendering (future enhancement)

#### 4. **WeWorkRemotely**
- **Source**: `weworkremotely`
- **Type**: Web scraping
- **Jobs**: Remote tech jobs
- **Status**: ⚠️ Requires JavaScript rendering (future enhancement)

### 🔑 API-Based Sources (Require RAPIDAPI_KEY)

- **JSearch**: LinkedIn, Indeed, Glassdoor aggregated
- **LinkedIn Jobs**: Direct LinkedIn API
- **Indeed**: Direct Indeed API
- **Glassdoor**: Direct Glassdoor API
- **RemoteOK**: Free API, no key required

## Usage

### Via API Endpoint

```bash
# Fetch jobs from Remotive (recommended free source)
POST http://localhost:8000/api/jobs/fetch?source=remotive&query=software-dev&limit=50

# Scrape from all available sources
POST http://localhost:8000/api/jobs/fetch?source=scrape_all&limit=75

# Fetch with specific query
POST http://localhost:8000/api/jobs/fetch?source=remotive&query=python&limit=30
```

### Query Parameters

- `source`: Job source (remotive, scrape_all, ycombinator, etc.)
- `query`: Search query or category
- `limit`: Maximum number of jobs (default: 50)
- `append`: Append to existing jobs or replace (default: true)
- `location`: Location filter (for some sources)
- `remote_only`: Filter remote jobs only (default: false)

### Python Code Example

```python
from core.job_fetcher import JobFetcher

fetcher = JobFetcher()

# Fetch from Remotive
result = fetcher.fetch_and_save(
    source="remotive",
    query="software-dev",
    limit=50,
    append=True
)

print(f"Fetched {result['count']} jobs")

# Fetch from all scraping sources
result = fetcher.fetch_and_save(
    source="scrape_all",
    query="python developer",
    limit=75,
    append=True
)
```

## Dependencies

The web scraping feature requires:

```txt
beautifulsoup4>=4.12.2
lxml>=4.9.0  # Or use html.parser
```

Install with:
```bash
pip install beautifulsoup4 lxml
```

## Data Format

All scraped jobs are normalized to a standard format:

```json
{
  "id": "remotive_12345",
  "title": "Senior Python Developer",
  "company": "Tech Company Inc",
  "location": "Remote",
  "url": "https://example.com/job/12345",
  "source": "Remotive",
  "date_posted": "2026-01-03T10:00:00",
  "job_type": "Remote",
  "description": "...",
  "salary": null,
  "requirements": [],
  "benefits": [],
  "category": "Software Development",
  "tags": ["python", "backend", "api"]
}
```

## Recommendations

### Best Free Sources (No API Key)
1. **Remotive** - Most reliable, good job quality
2. **scrape_all** - Best for maximum coverage
3. **RemoteOK** - Free API, reliable

### Best Paid Sources (Free Tier Available)
1. **JSearch** - Aggregates LinkedIn, Indeed, Glassdoor
2. **LinkedIn Jobs** - Direct LinkedIn API
3. **Indeed** - Direct Indeed API

## Future Enhancements

To add support for JavaScript-rendered sites:

```bash
pip install selenium webdriver-manager
```

Or use Playwright:
```bash
pip install playwright
playwright install chromium
```

## Troubleshooting

### No jobs returned
- Check internet connection
- Verify the source is working (try Remotive first)
- Check server logs for errors

### Rate limiting
- Add delays between requests
- Use `append=True` to gradually build job database
- Rotate between different sources

### JavaScript sites not working
- Sites like WeWorkRemotely require browser automation
- Use Remotive or RemoteOK as alternatives
- Or implement Selenium/Playwright support

## API Response Examples

### Get Available Sources
```bash
GET http://localhost:8000/api/jobs/sources
```

Response shows all sources with their status and requirements.

### Fetch Jobs
```bash
POST http://localhost:8000/api/jobs/fetch?source=remotive&limit=25
```

Returns:
```json
{
  "status": "started",
  "message": "Fetching jobs from remotive in background...",
  "source": "remotive",
  "query": "software-dev",
  "location": null,
  "limit": 25
}
```

## Testing

Test the scraping functionality:

```bash
python test_scraper.py
```

## Notes

- Jobs are saved to `data/job_listings.json`
- Duplicates are automatically removed by job ID
- Background tasks are used to avoid blocking the API
- Job recommender automatically refreshes when new jobs are added
