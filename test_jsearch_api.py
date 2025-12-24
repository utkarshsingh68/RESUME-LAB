"""Test JSearch API subscription."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("RAPIDAPI_KEY")
print(f"Using API Key: {api_key[:20]}...")

url = "https://jsearch.p.rapidapi.com/search"
headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}
params = {
    "query": "python developer",
    "page": "1",
    "num_pages": "1"
}

print("\nTesting JSearch /search endpoint...")
try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Found {len(data.get('data', []))} jobs")
        if data.get('data'):
            print(f"\nFirst job: {data['data'][0].get('job_title')}")
    else:
        print(f"❌ ERROR: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")
