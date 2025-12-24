"""Fetch jobs from external job search APIs."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import requests
from datetime import datetime
import time

from config import settings


class JobFetcher:
    """Fetch and normalize jobs from multiple sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_path = Path(settings.JOB_DATA_PATH)
        
    def fetch_remoteok_jobs(self, tags: Optional[List[str]] = None, limit: int = 50) -> List[Dict]:
        """
        Fetch jobs from RemoteOK API (free, no auth required).
        
        Args:
            tags: List of tags to filter (e.g., ['python', 'javascript'])
            limit: Maximum number of jobs to fetch
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            url = "https://remoteok.com/api"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Resume Analyzer Bot)'
            }
            
            self.logger.info("Fetching jobs from RemoteOK...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            jobs_data = response.json()
            
            # First item is metadata, skip it
            if jobs_data and isinstance(jobs_data, list):
                jobs_data = jobs_data[1:]
            
            normalized_jobs = []
            
            for job in jobs_data[:limit]:
                # Filter by tags if specified
                if tags:
                    job_tags = [tag.lower() for tag in job.get('tags', [])]
                    if not any(tag.lower() in job_tags for tag in tags):
                        continue
                
                normalized = self._normalize_remoteok_job(job)
                if normalized:
                    normalized_jobs.append(normalized)
            
            self.logger.info(f"Fetched {len(normalized_jobs)} jobs from RemoteOK")
            return normalized_jobs
            
        except Exception as e:
            self.logger.error(f"Error fetching RemoteOK jobs: {e}")
            return []
    
    def fetch_jsearch_jobs(
        self, 
        query: str = "software engineer",
        location: str = "United States",
        date_posted: str = "all",
        remote_jobs_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """
        Fetch jobs from JSearch API (aggregates LinkedIn, Indeed, Glassdoor).
        
        Args:
            query: Job search query (e.g., 'python developer', 'data scientist')
            location: Location filter (e.g., 'New York', 'United States')
            date_posted: Filter by date - 'all', 'today', '3days', 'week', 'month'
            remote_jobs_only: If True, only return remote jobs
            limit: Maximum number of jobs to fetch (max 100 per request)
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            if not settings.RAPIDAPI_KEY:
                self.logger.warning("RAPIDAPI_KEY not configured. Set it in .env file.")
                return []
            
            url = "https://jsearch.p.rapidapi.com/search"
            
            headers = {
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": settings.RAPIDAPI_HOST
            }
            
            params = {
                "query": query,
                "page": "1",
                "num_pages": "1",
                "date_posted": date_posted
            }
            
            if location:
                params["location"] = location
            
            if remote_jobs_only:
                params["remote_jobs_only"] = "true"
            
            self.logger.info(f"Fetching jobs from JSearch: {query} in {location}")
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                # Log full response body to help debug RapidAPI / JSearch errors (e.g., plan / quota issues)
                error_text = ""
                try:
                    error_text = response.text
                except Exception:
                    pass
                self.logger.error(
                    "HTTP error from JSearch: %s | Response: %s",
                    str(http_err),
                    error_text[:500],  # avoid dumping huge payloads
                )
                return []
            
            data = response.json()
            jobs_data = data.get("data", [])
            
            normalized_jobs = []
            
            for job in jobs_data[:limit]:
                normalized = self._normalize_jsearch_job(job)
                if normalized:
                    normalized_jobs.append(normalized)
            
            self.logger.info(f"Fetched {len(normalized_jobs)} jobs from JSearch")
            return normalized_jobs
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error fetching JSearch jobs: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching JSearch jobs: {e}")
            return []
    
    def fetch_github_jobs(self, description: str = "", location: str = "", limit: int = 50) -> List[Dict]:
        """
        Fetch jobs from GitHub Jobs API.
        Note: GitHub Jobs was deprecated. Using JSearch API as alternative.
        """
        try:
            # Using free alternative - JSearch on RapidAPI (free tier)
            # For demo purposes, return empty list
            self.logger.info("GitHub Jobs API is deprecated. Use JSearch instead.")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching GitHub jobs: {e}")
            return []

    def fetch_linkedin_jobs(
        self,
        title: str = "software engineer",
        location: str = "United States",
        limit: int = 25,
    ) -> List[Dict]:
        """Fetch jobs from the LinkedIn Job Search API on RapidAPI.

        This uses the "LinkedIn Job Search API" (linkedin-job-search-api.p.rapidapi.com)
        and the "Get Jobs 24h (indexed)" endpoint to retrieve recent postings.
        """

        try:
            if not settings.RAPIDAPI_KEY:
                self.logger.warning("RAPIDAPI_KEY not configured. Set it in .env file.")
                return []

            url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-24h"

            headers = {
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": settings.LINKEDIN_API_HOST,
            }

            params = {
                "limit": str(min(limit, 50)),
                "offset": "0",
                "title_filter": title,
                "location_filter": location,
                "description_type": "text",
            }

            self.logger.info("Fetching jobs from LinkedIn Job Search API: %s in %s", title, location)

            response = requests.get(url, headers=headers, params=params, timeout=20)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                error_text = ""
                try:
                    error_text = response.text
                except Exception:
                    pass
                self.logger.error(
                    "HTTP error from LinkedIn Job Search API: %s | Response: %s",
                    str(http_err),
                    error_text[:500],
                )
                return []

            data = response.json()

            # Most RapidAPI jobs APIs return either {"data": [...]} or a raw list
            jobs_data = data.get("data") if isinstance(data, dict) else data
            if not isinstance(jobs_data, list):
                self.logger.error("Unexpected LinkedIn API response format: %s", type(jobs_data))
                return []

            normalized_jobs: List[Dict] = []
            for job in jobs_data[:limit]:
                normalized = self._normalize_linkedin_job(job)
                if normalized:
                    normalized_jobs.append(normalized)

            self.logger.info("Fetched %d jobs from LinkedIn Job Search API", len(normalized_jobs))
            return normalized_jobs

        except requests.exceptions.RequestException as e:
            self.logger.error("Network error fetching LinkedIn jobs: %s", e)
            return []
        except Exception as e:
            self.logger.error("Error fetching LinkedIn jobs: %s", e)
            return []

    def fetch_glassdoor_jobs(
        self,
        query: str = "software engineer",
        location: str = "United States",
        limit: int = 25,
    ) -> List[Dict]:
        """Fetch jobs from Glassdoor Real-Time API on RapidAPI."""
        try:
            if not settings.RAPIDAPI_KEY:
                self.logger.warning("RAPIDAPI_KEY not configured. Set it in .env file.")
                return []

            # Using companies/interview-details endpoint as a fallback; adjust if needed
            url = "https://glassdoor-real-time.p.rapidapi.com/companies/interview-details"

            headers = {
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": settings.GLASSDOOR_API_HOST,
            }

            # Glassdoor API may use different param names; adjust as needed
            params = {
                "interviewId": "19018219",  # Example from screenshot; may need dynamic value
            }

            self.logger.info("Fetching jobs from Glassdoor Real-Time API: %s in %s", query, location)

            response = requests.get(url, headers=headers, params=params, timeout=20)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                error_text = ""
                try:
                    error_text = response.text
                except Exception:
                    pass
                self.logger.error(
                    "HTTP error from Glassdoor API: %s | Response: %s",
                    str(http_err),
                    error_text[:500],
                )
                return []

            data = response.json()
            jobs_data = data.get("data") if isinstance(data, dict) else data
            if not isinstance(jobs_data, list):
                # Glassdoor might return single object or different structure
                jobs_data = [data] if isinstance(data, dict) else []

            normalized_jobs: List[Dict] = []
            for job in jobs_data[:limit]:
                normalized = self._normalize_glassdoor_job(job)
                if normalized:
                    normalized_jobs.append(normalized)

            self.logger.info("Fetched %d jobs from Glassdoor Real-Time API", len(normalized_jobs))
            return normalized_jobs

        except requests.exceptions.RequestException as e:
            self.logger.error("Network error fetching Glassdoor jobs: %s", e)
            return []
        except Exception as e:
            self.logger.error("Error fetching Glassdoor jobs: %s", e)
            return []

    def fetch_indeed_jobs(
        self,
        query: str = "software engineer",
        location: str = "United States",
        limit: int = 25,
    ) -> List[Dict]:
        """Fetch jobs from Indeed API on RapidAPI."""
        try:
            if not settings.RAPIDAPI_KEY:
                self.logger.warning("RAPIDAPI_KEY not configured. Set it in .env file.")
                return []

            # Using Company jobs endpoint as example; adjust endpoint as needed
            url = "https://indeed12.p.rapidapi.com/jobs/search"

            headers = {
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": settings.INDEED_API_HOST,
            }

            params = {
                "query": query,
                "location": location,
                "page_id": "1",
                "locality": "us",
            }

            self.logger.info("Fetching jobs from Indeed API: %s in %s", query, location)

            response = requests.get(url, headers=headers, params=params, timeout=20)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                error_text = ""
                try:
                    error_text = response.text
                except Exception:
                    pass
                self.logger.error(
                    "HTTP error from Indeed API: %s | Response: %s",
                    str(http_err),
                    error_text[:500],
                )
                return []

            data = response.json()
            jobs_data = data.get("hits") or data.get("jobs") or data.get("data")
            if not jobs_data:
                jobs_data = [data] if isinstance(data, dict) else []
            if not isinstance(jobs_data, list):
                jobs_data = [jobs_data]

            normalized_jobs: List[Dict] = []
            for job in jobs_data[:limit]:
                normalized = self._normalize_indeed_job(job)
                if normalized:
                    normalized_jobs.append(normalized)

            self.logger.info("Fetched %d jobs from Indeed API", len(normalized_jobs))
            return normalized_jobs

        except requests.exceptions.RequestException as e:
            self.logger.error("Network error fetching Indeed jobs: %s", e)
            return []
        except Exception as e:
            self.logger.error("Error fetching Indeed jobs: %s", e)
            return []
    
    def _normalize_jsearch_job(self, job: Dict) -> Optional[Dict]:
        """Normalize JSearch job to our internal format."""
        try:
            # Extract job source
            job_source = job.get("job_publisher", "Unknown")
            
            # Extract skills from job description and required qualifications
            description = job.get("job_description", "")
            qualifications = job.get("job_required_qualifications", [])
            
            skills = self._extract_skills_from_text(description)
            
            # Determine experience level
            title_lower = job.get("job_title", "").lower()
            experience_level = "Mid-Level"
            experience_required = 3
            
            if any(word in title_lower for word in ['senior', 'lead', 'principal', 'staff']):
                experience_level = "Senior"
                experience_required = 5
            elif any(word in title_lower for word in ['junior', 'entry', 'intern', 'graduate']):
                experience_level = "Junior"
                experience_required = 1
            
            # Extract salary if available
            salary_min = job.get("job_min_salary", 0)
            salary_max = job.get("job_max_salary", 0)
            salary_avg = (salary_min + salary_max) / 2 if salary_min and salary_max else 0
            
            # Build highlights
            highlights = []
            if job.get("job_employment_type"):
                highlights.append(f"{job['job_employment_type']} position")
            if salary_min and salary_max:
                highlights.append(f"${salary_min:,.0f} - ${salary_max:,.0f}")
            elif job.get("job_salary_period"):
                highlights.append(f"Salary info available")
            if job.get("job_is_remote"):
                highlights.append("Remote work")
            if qualifications:
                highlights.extend(qualifications[:3])  # Top 3 requirements
            
            normalized = {
                "id": f"jsearch-{job.get('job_id', '')}",
                "title": job.get("job_title", "Unknown Position"),
                "role": self._extract_role_from_title(job.get("job_title", "")),
                "company": job.get("employer_name", "Unknown Company"),
                "location": job.get("job_city", job.get("job_country", "Remote")),
                "employment_type": job.get("job_employment_type", "Full-time"),
                "experience_level": experience_level,
                "experience_required": experience_required,
                "skills": skills[:10],
                "description": description[:1000] if description else job.get("job_title", ""),
                "highlights": highlights,
                "apply_url": job.get("job_apply_link", job.get("job_google_link", "")),
                "posted_at": job.get("job_posted_at_datetime_utc", datetime.now().isoformat()),
                "salary": int(salary_avg) if salary_avg else 0,
                "source": f"JSearch ({job_source})"
            }
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing JSearch job: {e}")
            return None
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract common technical skills from job description."""
        if not text:
            return []
        
        text_lower = text.lower()
        
        # Common technical skills to look for
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'sql',
            'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
            'aws', 'azure', 'gcp', 'git', 'ci/cd', 'agile', 'scrum', 'rest',
            'graphql', 'microservices', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'machine learning', 'deep learning', 'ai', 'nlp',
            'golang', 'rust', 'c++', 'c#', '.net', 'ruby', 'php', 'swift', 'kotlin'
        ]
        
        found_skills = [skill for skill in skill_keywords if skill in text_lower]
        return found_skills[:10]  # Return top 10

    def _normalize_linkedin_job(self, job: Dict) -> Optional[Dict]:
        """Normalize LinkedIn Job Search API job to our internal format.

        The exact field names can vary slightly between versions of the API, so we
        use .get() with multiple fallbacks to keep this robust.
        """

        try:
            # Basic fields
            title = job.get("job_title") or job.get("title") or "Unknown Position"
            company = (
                job.get("company_name")
                or job.get("company")
                or job.get("employer_name")
                or "Unknown Company"
            )
            location = job.get("location") or job.get("job_location") or "Unknown"

            # Description text
            description = (
                job.get("job_description")
                or job.get("description")
                or ""
            )

            # URL / apply link
            apply_url = (
                job.get("linkedin_job_url_cleaned")
                or job.get("job_url")
                or job.get("job_link")
                or ""
            )

            # Use text-based skill extraction
            skills = self._extract_skills_from_text(description)

            # Heuristic experience level from title
            title_lower = title.lower()
            experience_level = "Mid-Level"
            experience_required = 3
            if any(w in title_lower for w in ["senior", "lead", "principal", "staff"]):
                experience_level = "Senior"
                experience_required = 5
            elif any(w in title_lower for w in ["junior", "entry", "intern", "graduate"]):
                experience_level = "Junior"
                experience_required = 1

            # Highlights – pick a few interesting fields
            highlights: List[str] = []
            if job.get("employment_type"):
                highlights.append(str(job["employment_type"]))
            if job.get("posted_date"):
                highlights.append(f"Posted: {job['posted_date']}")

            normalized = {
                "id": f"linkedin-{job.get('job_id') or job.get('id', '')}",
                "title": title,
                "role": self._extract_role_from_title(title),
                "company": company,
                "location": location,
                "employment_type": job.get("employment_type", "Full-time"),
                "experience_level": experience_level,
                "experience_required": experience_required,
                "skills": skills[:10],
                "description": description[:1000] if description else title,
                "highlights": highlights,
                "apply_url": apply_url,
                "posted_at": job.get("posted_at") or job.get("posted_date") or datetime.now().isoformat(),
                "salary": 0,
                "source": "LinkedIn Job Search API",
            }

            return normalized
        except Exception as e:
            self.logger.error("Error normalizing LinkedIn job: %s", e)
            return None

    def _normalize_glassdoor_job(self, job: Dict) -> Optional[Dict]:
        """Normalize Glassdoor Real-Time API job to our internal format."""
        try:
            title = job.get("job_title") or job.get("title") or "Unknown Position"
            company = job.get("employer_name") or job.get("company") or "Unknown Company"
            location = job.get("location") or "Unknown"
            description = job.get("description") or job.get("job_description") or ""
            apply_url = job.get("url") or job.get("apply_url") or ""

            skills = self._extract_skills_from_text(description)

            title_lower = title.lower()
            experience_level = "Mid-Level"
            experience_required = 3
            if any(w in title_lower for w in ["senior", "lead", "principal", "staff"]):
                experience_level = "Senior"
                experience_required = 5
            elif any(w in title_lower for w in ["junior", "entry", "intern", "graduate"]):
                experience_level = "Junior"
                experience_required = 1

            highlights: List[str] = []
            if job.get("salary"):
                highlights.append(f"Salary: {job['salary']}")
            if job.get("rating"):
                highlights.append(f"Rating: {job['rating']}")

            normalized = {
                "id": f"glassdoor-{job.get('id', '')}",
                "title": title,
                "role": self._extract_role_from_title(title),
                "company": company,
                "location": location,
                "employment_type": job.get("employment_type", "Full-time"),
                "experience_level": experience_level,
                "experience_required": experience_required,
                "skills": skills[:10],
                "description": description[:1000] if description else title,
                "highlights": highlights,
                "apply_url": apply_url,
                "posted_at": job.get("posted_at") or datetime.now().isoformat(),
                "salary": 0,
                "source": "Glassdoor Real-Time API",
            }
            return normalized
        except Exception as e:
            self.logger.error("Error normalizing Glassdoor job: %s", e)
            return None

    def _normalize_indeed_job(self, job: Dict) -> Optional[Dict]:
        """Normalize Indeed API job to our internal format."""
        try:
            title = job.get("title") or job.get("job_title") or "Unknown Position"
            company = job.get("company_name") or job.get("company") or "Unknown Company"
            location = job.get("location") or job.get("formatted_location") or "Unknown"
            description = job.get("description") or job.get("snippet") or ""
            apply_url = job.get("link") or job.get("url") or job.get("job_url") or ""

            skills = self._extract_skills_from_text(description)

            title_lower = title.lower()
            experience_level = "Mid-Level"
            experience_required = 3
            if any(w in title_lower for w in ["senior", "lead", "principal", "staff"]):
                experience_level = "Senior"
                experience_required = 5
            elif any(w in title_lower for w in ["junior", "entry", "intern", "graduate"]):
                experience_level = "Junior"
                experience_required = 1

            highlights: List[str] = []
            if job.get("salary"):
                highlights.append(str(job["salary"]))
            if job.get("pub_date_ts_milli"):
                highlights.append(f"Posted: {job['pub_date_ts_milli']}")

            normalized = {
                "id": f"indeed-{job.get('id', job.get('job_id', ''))}",
                "title": title,
                "role": self._extract_role_from_title(title),
                "company": company,
                "location": location,
                "employment_type": job.get("employment_type", "Full-time"),
                "experience_level": experience_level,
                "experience_required": experience_required,
                "skills": skills[:10],
                "description": description[:1000] if description else title,
                "highlights": highlights,
                "apply_url": apply_url,
                "posted_at": job.get("posted_at") or datetime.now().isoformat(),
                "salary": 0,
                "source": "Indeed API",
            }
            return normalized
        except Exception as e:
            self.logger.error("Error normalizing Indeed job: %s", e)
            return None
    
    def _normalize_remoteok_job(self, job: Dict) -> Optional[Dict]:
        """Normalize RemoteOK job to our internal format."""
        try:
            # Extract skills from tags
            tags = job.get('tags', [])
            skills = [tag.lower() for tag in tags if tag and len(tag) < 20]
            
            # Determine experience level based on salary or title
            title_lower = job.get('position', '').lower()
            experience_level = "Mid-Level"
            experience_required = 3
            
            if any(word in title_lower for word in ['senior', 'lead', 'principal']):
                experience_level = "Senior"
                experience_required = 5
            elif any(word in title_lower for word in ['junior', 'entry']):
                experience_level = "Junior"
                experience_required = 1
            
            # Build description with highlights
            description_parts = []
            if job.get('description'):
                description_parts.append(job['description'][:500])  # Limit length
            
            highlights = []
            if job.get('company'):
                highlights.append(f"Work at {job['company']}")
            if job.get('salary'):
                highlights.append(f"Salary: {job['salary']}")
            
            normalized = {
                "id": f"remoteok-{job.get('id', '')}",
                "title": job.get('position', 'Unknown Position'),
                "role": self._extract_role_from_title(job.get('position', '')),
                "company": job.get('company', 'Unknown Company'),
                "location": job.get('location', 'Remote'),
                "employment_type": "Full-time",
                "experience_level": experience_level,
                "experience_required": experience_required,
                "skills": skills[:10],  # Limit to 10 skills
                "description": ' '.join(description_parts) if description_parts else job.get('position', ''),
                "highlights": highlights,
                "apply_url": job.get('url', ''),
                "posted_at": job.get('date', datetime.now().strftime('%Y-%m-%d')),
                "salary": job.get('salary_min', 0),
                "source": "RemoteOK"
            }
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing RemoteOK job: {e}")
            return None
    
    def _extract_role_from_title(self, title: str) -> str:
        """Extract role category from job title."""
        title_lower = title.lower()
        
        role_keywords = {
            'Machine Learning': ['machine learning', 'ml engineer', 'ai engineer'],
            'Data Science': ['data scientist', 'data science'],
            'Backend': ['backend', 'back-end', 'server-side'],
            'Frontend': ['frontend', 'front-end', 'ui developer'],
            'Full Stack': ['full stack', 'fullstack', 'full-stack'],
            'DevOps': ['devops', 'site reliability', 'sre'],
            'Mobile': ['mobile', 'ios', 'android', 'react native'],
            'Data Engineering': ['data engineer', 'data engineering'],
            'Software Engineer': ['software engineer', 'developer'],
        }
        
        for role, keywords in role_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return role
        
        return 'Software Engineer'
    
    def save_jobs_to_file(self, jobs: List[Dict], append: bool = False) -> bool:
        """
        Save fetched jobs to the local JSON file.
        
        Args:
            jobs: List of job dictionaries
            append: If True, append to existing jobs; if False, replace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            existing_jobs = []
            
            if append and self.data_path.exists():
                with self.data_path.open('r', encoding='utf-8') as f:
                    existing_jobs = json.load(f)
            
            # Combine jobs and remove duplicates by ID
            all_jobs = existing_jobs + jobs
            unique_jobs = {job['id']: job for job in all_jobs}.values()
            unique_jobs = list(unique_jobs)
            
            # Save to file
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with self.data_path.open('w', encoding='utf-8') as f:
                json.dump(unique_jobs, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(unique_jobs)} jobs to {self.data_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving jobs to file: {e}")
            return False
    
    def fetch_and_save(
        self,
        source: str = "remoteok",
        tags: Optional[List[str]] = None,
        query: Optional[str] = None,
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
        append: bool = True
    ) -> Dict:
        """
        Fetch jobs from specified source and save to file.
        
        Args:
            source: Job source ('remoteok', 'jsearch', 'linkedin', 'indeed', 'glassdoor')
            tags: Filter tags for RemoteOK
            query: Search query for JSearch (e.g., 'python developer')
            location: Location filter for JSearch
            remote_only: Filter for remote jobs only (JSearch)
            limit: Maximum jobs to fetch
            append: Append to existing jobs or replace
            
        Returns:
            Dictionary with status and count
        """
        jobs = []
        
        source_lower = source.lower()

        if source_lower == "remoteok":
            jobs = self.fetch_remoteok_jobs(tags=tags, limit=limit)
        elif source_lower == "jsearch":
            # JSearch aggregates multiple boards
            search_query = query or " ".join(tags) if tags else "software engineer"
            search_location = location or "United States"
            jobs = self.fetch_jsearch_jobs(
                query=search_query,
                location=search_location,
                remote_jobs_only=remote_only,
                limit=limit,
            )
        elif source_lower in ["linkedin", "linkedin_api"]:
            # Direct LinkedIn Job Search API
            search_title = query or " ".join(tags) if tags else "software engineer"
            search_location = location or "United States"
            jobs = self.fetch_linkedin_jobs(
                title=search_title,
                location=search_location,
                limit=limit,
            )
        elif source_lower == "glassdoor":
            # Direct Glassdoor Real-Time API
            search_query = query or " ".join(tags) if tags else "software engineer"
            search_location = location or "United States"
            jobs = self.fetch_glassdoor_jobs(
                query=search_query,
                location=search_location,
                limit=limit,
            )
        elif source_lower == "indeed":
            # Direct Indeed API
            search_query = query or " ".join(tags) if tags else "software engineer"
            search_location = location or "United States"
            jobs = self.fetch_indeed_jobs(
                query=search_query,
                location=search_location,
                limit=limit,
            )
        elif source_lower == "github":
            jobs = self.fetch_github_jobs(limit=limit)
        else:
            return {"success": False, "message": f"Unknown source: {source}", "count": 0}
        
        if not jobs:
            return {"success": False, "message": "No jobs fetched. Check API keys.", "count": 0}
        
        success = self.save_jobs_to_file(jobs, append=append)
        
        return {
            "success": success,
            "message": f"Fetched and saved {len(jobs)} jobs from {source}",
            "count": len(jobs),
            "source": source
        }
