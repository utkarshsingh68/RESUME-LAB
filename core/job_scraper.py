"""Web scraping module for job listings from various job boards."""
import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re


class JobScraper:
    """Scrape jobs from various job boards without requiring API keys."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
    def scrape_weworkremotely(
        self, 
        category: str = "programming",
        limit: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs from WeWorkRemotely.com (remote jobs).
        
        Note: WeWorkRemotely uses JavaScript to load content dynamically.
        This simple scraper may not work reliably. Use Remotive instead.
        
        Args:
            category: Job category ('programming', 'design', 'marketing', 'customer-support')
            limit: Maximum number of jobs to scrape
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            self.logger.warning("WeWorkRemotely uses JavaScript rendering. Results may be empty. Use Remotive instead.")
            return []
            
        except Exception as e:
            self.logger.error(f"Error scraping WeWorkRemotely: {e}")
            return []
    
    def scrape_stackoverflow(
        self,
        query: str = "python",
        location: str = "",
        limit: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs from StackOverflow Jobs.
        
        Args:
            query: Search query/technology
            location: Location filter
            limit: Maximum number of jobs to scrape
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            # Note: Stack Overflow Jobs was shut down in 2022
            # Keeping this as a template for other sites
            self.logger.warning("Stack Overflow Jobs was discontinued in 2022")
            return []
            
        except Exception as e:
            self.logger.error(f"Error scraping StackOverflow: {e}")
            return []
    
    def scrape_remotive(
        self,
        category: str = "software-dev",
        limit: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs from Remotive.io (remote jobs).
        
        Args:
            category: Job category (software-dev, design, marketing, etc.)
            limit: Maximum number of jobs to scrape
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            # Remotive has an API endpoint we can use
            url = "https://remotive.com/api/remote-jobs"
            self.logger.info(f"Fetching Remotive jobs: {category}")
            
            params = {
                'category': category,
                'limit': limit
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job_data in data.get('jobs', [])[:limit]:
                try:
                    job = {
                        'id': f"remotive_{job_data.get('id', abs(hash(job_data.get('url'))))}",
                        'title': job_data.get('title', ''),
                        'company': job_data.get('company_name', ''),
                        'location': 'Remote',
                        'url': job_data.get('url', ''),
                        'source': 'Remotive',
                        'date_posted': job_data.get('publication_date', datetime.now().isoformat()),
                        'job_type': job_data.get('job_type', 'Remote'),
                        'description': job_data.get('description', ''),
                        'salary': job_data.get('salary', None),
                        'requirements': [],
                        'benefits': []
                    }
                    
                    # Extract category/tags
                    if job_data.get('category'):
                        job['category'] = job_data['category']
                    
                    if job_data.get('tags'):
                        job['tags'] = job_data['tags']
                    
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Remotive job: {e}")
                    continue
            
            self.logger.info(f"Scraped {len(jobs)} jobs from Remotive")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error scraping Remotive: {e}")
            return []
    
    def scrape_ycombinator(
        self,
        query: str = "",
        limit: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs from Y Combinator's Work at a Startup.
        
        Args:
            query: Search query
            limit: Maximum number of jobs to scrape
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            url = "https://www.workatastartup.com/jobs"
            self.logger.info(f"Scraping Y Combinator jobs")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            jobs = []
            
            # Y Combinator uses dynamic loading, so this is simplified
            # In production, you'd use Selenium or their API if available
            job_cards = soup.find_all('div', class_='job-card')[:limit]
            
            for card in job_cards:
                try:
                    # This is a simplified parser - adjust based on actual HTML structure
                    title_elem = card.find('h3')
                    company_elem = card.find('span', class_='company')
                    
                    if not title_elem:
                        continue
                    
                    job = {
                        'id': f"yc_{abs(hash(title_elem.text))}",
                        'title': title_elem.text.strip(),
                        'company': company_elem.text.strip() if company_elem else 'YC Startup',
                        'location': 'Varies',
                        'url': url,
                        'source': 'Y Combinator',
                        'date_posted': datetime.now().isoformat(),
                        'job_type': 'Full-time',
                        'description': '',
                        'salary': None,
                        'requirements': [],
                        'benefits': []
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing YC job: {e}")
                    continue
            
            self.logger.info(f"Scraped {len(jobs)} jobs from Y Combinator")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error scraping Y Combinator: {e}")
            return []
    
    def scrape_angellist(
        self,
        role: str = "software-engineer",
        location: str = "",
        limit: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs from AngelList (now Wellfound).
        
        Args:
            role: Role/position type
            location: Location filter
            limit: Maximum number of jobs to scrape
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            # AngelList requires authentication and uses heavy JavaScript
            # This would require Selenium or their API
            self.logger.warning("AngelList scraping requires API access or Selenium")
            return []
            
        except Exception as e:
            self.logger.error(f"Error scraping AngelList: {e}")
            return []
    
    def scrape_greenhouse(
        self,
        company_domain: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs from a company's Greenhouse careers page.
        
        Args:
            company_domain: Company domain (e.g., 'company.greenhouse.io')
            limit: Maximum number of jobs to scrape
            
        Returns:
            List of normalized job dictionaries
        """
        try:
            # Greenhouse has a standard API endpoint
            url = f"https://boards-api.greenhouse.io/v1/boards/{company_domain}/jobs"
            self.logger.info(f"Fetching Greenhouse jobs for {company_domain}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job_data in data.get('jobs', [])[:limit]:
                try:
                    job = {
                        'id': f"greenhouse_{job_data.get('id')}",
                        'title': job_data.get('title', ''),
                        'company': company_domain.replace('.greenhouse.io', ''),
                        'location': job_data.get('location', {}).get('name', ''),
                        'url': job_data.get('absolute_url', ''),
                        'source': 'Greenhouse',
                        'date_posted': job_data.get('updated_at', datetime.now().isoformat()),
                        'job_type': 'Full-time',
                        'description': '',
                        'salary': None,
                        'requirements': [],
                        'benefits': []
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Greenhouse job: {e}")
                    continue
            
            self.logger.info(f"Scraped {len(jobs)} jobs from Greenhouse ({company_domain})")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error scraping Greenhouse: {e}")
            return []
    
    def scrape_all_sources(
        self,
        query: str = "python",
        location: str = "",
        limit_per_source: int = 25
    ) -> List[Dict]:
        """
        Scrape jobs from all available sources.
        
        Args:
            query: Search query
            location: Location filter
            limit_per_source: Maximum jobs per source
            
        Returns:
            Combined list of jobs from all sources
        """
        all_jobs = []
        
        # Remotive (working API)
        all_jobs.extend(self.scrape_remotive(
            category="software-dev",
            limit=limit_per_source
        ))
        
        time.sleep(1)  # Be polite with requests
        
        # Y Combinator
        all_jobs.extend(self.scrape_ycombinator(
            query=query,
            limit=limit_per_source
        ))
        
        self.logger.info(f"Total scraped jobs from all sources: {len(all_jobs)}")
        return all_jobs
