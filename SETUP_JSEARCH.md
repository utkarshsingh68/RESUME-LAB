# JSearch API Setup Guide
## Get LinkedIn, Indeed, and Glassdoor Jobs

### What is JSearch?
JSearch is a RapidAPI service that aggregates job listings from:
- **LinkedIn** 
- **Indeed**
- **Glassdoor**
- Google Jobs
- ZipRecruiter
- And more...

### Free Tier
- ✅ **500 requests/month** for FREE
- ✅ No credit card required for free tier
- ✅ Access to all job sources (LinkedIn, Indeed, Glassdoor)

---

## Setup Steps (5 minutes)

### 1. Get Your RapidAPI Key

1. **Sign up for RapidAPI** (free):
   - Go to: https://rapidapi.com/auth/sign-up
   - Sign up with Google/GitHub or email

2. **Subscribe to JSearch API**:
   - Visit: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
   - Click **"Subscribe to Test"**
   - Select **"Basic Plan"** (FREE - 500 requests/month)
   - Click **"Subscribe"**

3. **Copy your API Key**:
   - After subscribing, you'll see your API key in the code examples
   - Look for: `X-RapidAPI-Key: YOUR_KEY_HERE`
   - Copy the key value

### 2. Add Key to Your .env File

1. Open your `.env` file (or copy from `.env.example`)
2. Add your RapidAPI key:

```bash
RAPIDAPI_KEY=your_actual_api_key_here
```

### 3. Test the Integration

Run the backend server:
```bash
python -m backend.main
```

Then test the endpoint:
```bash
# Fetch LinkedIn jobs for "python developer"
curl -X POST "http://localhost:8000/api/jobs/fetch?source=linkedin&query=python%20developer&location=United%20States&limit=10"

# Fetch Indeed jobs for "data scientist"
curl -X POST "http://localhost:8000/api/jobs/fetch?source=indeed&query=data%20scientist&location=New%20York&limit=20"

# Fetch Glassdoor jobs (remote only)
curl -X POST "http://localhost:8000/api/jobs/fetch?source=glassdoor&query=software%20engineer&remote_only=true&limit=15"
```

---

## API Usage Examples

### Using the API

**Endpoint**: `POST /api/jobs/fetch`

**Parameters**:
- `source`: `jsearch`, `linkedin`, `indeed`, `glassdoor`, or `remoteok`
- `query`: Job search query (e.g., "python developer", "data scientist")
- `location`: Location filter (e.g., "New York", "United States", "Remote")
- `remote_only`: `true` to filter only remote jobs
- `limit`: Max jobs to fetch (1-100)
- `append`: `true` to add to existing jobs, `false` to replace

**Example Queries**:

```python
# Python Developer in San Francisco
POST /api/jobs/fetch?source=linkedin&query=python%20developer&location=San%20Francisco&limit=50

# Remote Data Scientist roles
POST /api/jobs/fetch?source=indeed&query=data%20scientist&remote_only=true&limit=30

# Machine Learning Engineer (all locations)
POST /api/jobs/fetch?source=jsearch&query=machine%20learning%20engineer&location=United%20States&limit=100
```

### Programmatic Usage

```python
from core.job_fetcher import JobFetcher

fetcher = JobFetcher()

# Fetch LinkedIn jobs
jobs = fetcher.fetch_jsearch_jobs(
    query="python developer",
    location="New York",
    remote_jobs_only=False,
    limit=50
)

# Save to database
fetcher.save_jobs_to_file(jobs, append=True)
```

---

## Check Available Sources

**Endpoint**: `GET /api/jobs/sources`

This will show:
- Available job sources
- Which ones are configured
- Setup instructions
- Free tier limits

---

## Rate Limits

### Free Tier (500 requests/month)
- ~16 requests per day
- Each job search = 1 request
- Plan accordingly for your usage

### Paid Plans
If you need more:
- **Pro Plan**: $9.99/month - 10,000 requests
- **Ultra Plan**: $49.99/month - 100,000 requests
- **Mega Plan**: $149.99/month - 500,000 requests

---

## Troubleshooting

### Error: "RAPIDAPI_KEY not configured"
- Make sure you added `RAPIDAPI_KEY=...` to your `.env` file
- Restart the backend server after updating `.env`

### Error: "No jobs fetched"
- Check that your API key is valid
- Verify you haven't exceeded free tier limit (500/month)
- Try a different search query
- Check RapidAPI dashboard for usage stats

### Jobs from specific source only
- LinkedIn: `source=linkedin`
- Indeed: `source=indeed`
- Glassdoor: `source=glassdoor`
- All sources: `source=jsearch`

---

## Advanced Features

### Search by Skills
```
query=python+django+postgresql&location=Remote
```

### Filter by Date Posted
Modify `job_fetcher.py` to add `date_posted` parameter:
- `all` - All jobs
- `today` - Posted today
- `3days` - Last 3 days
- `week` - Last week
- `month` - Last month

### Company-Specific Search
```
query=software+engineer+at+Google&location=Mountain+View
```

---

## Next Steps

1. ✅ Get your RapidAPI key
2. ✅ Add to `.env` file
3. ✅ Test with a simple query
4. ✅ Integrate with your resume analyzer
5. ✅ Start matching resumes to real LinkedIn/Indeed/Glassdoor jobs!

---

## Support

- **JSearch API Docs**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
- **RapidAPI Support**: https://support.rapidapi.com/
- **Check Usage**: https://rapidapi.com/developer/billing
