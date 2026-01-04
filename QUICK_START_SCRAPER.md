# Quick Start Guide - Web Job Scraper

## 🚀 How to Use (Simple Steps)

### 1. Navigate to Jobs Section
- Open http://localhost:8000
- Click **"Jobs"** in the navigation menu

### 2. Find the "Fetch Fresh Jobs" Card
- Located at the top of the Jobs section
- Has a globe icon 🌐

### 3. Configure Your Search

**Job Source** (dropdown):
```
✅ Remotive (Free, Recommended)     ← Start here!
   scrape_all (Free)
   RemoteOK (Free)
   JSearch - LinkedIn/Indeed (API Key)
   LinkedIn Jobs (API Key)
   Indeed (API Key)
   Glassdoor (API Key)
```

**Search Query** (text input):
```
Examples:
- python developer
- software-dev
- data scientist
- frontend developer
- machine learning
```

**Limit** (number):
```
Default: 25
Range: 1-100
Recommended: 25-50
```

### 4. Click "Fetch Jobs from Web"

You'll see:
```
🔵 Fetching jobs from remotive... This may take a moment.
```

Then:
```
✅ ✓ Started fetching jobs from remotive
```

After 5 seconds:
```
✅ Job database updated! Recommendations refreshed.
```

### 5. View Your Results

- Jobs automatically appear below
- If you've uploaded a resume: See personalized matches
- If no resume: Jobs are saved for later

## 📊 Recommended Settings

### For Software Engineers:
```
Source: Remotive
Query: software-dev
Limit: 50
```

### For Python Developers:
```
Source: Remotive
Query: python
Limit: 25
```

### For Data Scientists:
```
Source: scrape_all
Query: data scientist
Limit: 50
```

### For Remote Jobs Only:
```
Source: Remotive or RemoteOK
Query: your specialty
Limit: 25-50
```

## ⚡ Pro Tips

1. **Start with Remotive** - Most reliable free source
2. **Use specific queries** - Better results than generic terms
3. **Fetch 25-50 jobs** - Good balance of quantity and quality
4. **Upload resume first** - Get personalized recommendations
5. **Fetch regularly** - Jobs update daily
6. **Try multiple sources** - Different jobs from each

## 🎯 Workflow Examples

### Workflow 1: First Time User
```
1. Go to Jobs tab
2. Select "Remotive"
3. Query: "software-dev"
4. Limit: 25
5. Click Fetch
6. Upload your resume
7. See recommendations!
```

### Workflow 2: Regular User
```
1. Go to Jobs tab
2. Select "scrape_all"
3. Query: specific role
4. Limit: 50
5. Click Fetch
6. Refresh recommendations
7. Filter by location/role
```

### Workflow 3: Power User with API Key
```
1. Configure RAPIDAPI_KEY in .env
2. Select "JSearch"
3. Query: detailed job title
4. Limit: 100
5. Click Fetch
6. Get comprehensive matches
```

## 🔧 Troubleshooting

### "No jobs fetched"
- ✅ Check internet connection
- ✅ Try different source
- ✅ Use simpler query
- ✅ Reduce limit

### "Session expired"
- ✅ Upload resume again
- ✅ Refresh page

### API key errors
- ✅ Check .env file
- ✅ Verify RAPIDAPI_KEY
- ✅ Use free sources instead

### Jobs not appearing
- ✅ Wait 5-10 seconds
- ✅ Click "Refresh Recommendations"
- ✅ Check filters aren't too strict

## 📱 Status Indicators

**Blue (Info)**: 🔵 Processing
```
Fetching jobs from remotive... This may take a moment.
```

**Green (Success)**: ✅ Complete
```
✓ Started fetching jobs from remotive
Job database updated! Recommendations refreshed.
```

**Red (Error)**: ❌ Failed
```
✗ Error: No jobs fetched. Check API keys or network.
```

## 🎨 What You'll See

### Before Fetching:
```
┌─────────────────────────────────────┐
│  Upload a resume to unlock         │
│  tailored job matches              │
└─────────────────────────────────────┘
```

### While Fetching:
```
┌─────────────────────────────────────┐
│  🔄 Generating personalized job    │
│      matches...                     │
└─────────────────────────────────────┘
```

### After Fetching (with resume):
```
┌─────────────────────────────────────┐
│  Senior Python Developer            │
│  Tech Company • Remote              │
│  85% match                          │
│  Ready to Apply                     │
└─────────────────────────────────────┘
```

## ✅ Success Checklist

- [ ] Opened Jobs tab
- [ ] Found "Fetch Fresh Jobs" card
- [ ] Selected job source
- [ ] Entered search query
- [ ] Set job limit
- [ ] Clicked "Fetch Jobs from Web"
- [ ] Saw status message
- [ ] Waited 5 seconds
- [ ] Jobs appeared in recommendations

## 🎉 You're Done!

Now you can:
- ✅ Fetch jobs automatically
- ✅ Get personalized matches
- ✅ Apply to best-fit positions
- ✅ Track your progress
- ✅ Optimize your resume

**Happy job hunting! 🚀**
