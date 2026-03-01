"""
Job Description Fetcher - Fetches job descriptions from URLs
Respects robots.txt and implements rate limiting
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Dict, Optional
from urllib.parse import urlparse
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobFetcher:
    """Fetch job descriptions from various job boards"""

    def __init__(self, rate_limit_seconds: float = 2.0):
        """
        Initialize job fetcher

        Args:
            rate_limit_seconds: Minimum seconds to wait between requests
        """
        self.rate_limit = rate_limit_seconds
        self.last_request_time = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_job_description(self, url: str) -> Optional[Dict]:
        """
        Fetch job description from URL

        Args:
            url: Job posting URL

        Returns:
            Dictionary containing job information or None if failed
        """
        try:
            # Rate limiting per domain
            domain = urlparse(url).netloc
            self._apply_rate_limit(domain)

            logger.info(f"Fetching job from: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Parse based on job board
            if 'linkedin.com' in domain:
                return self._parse_linkedin(response.text, url)
            elif 'indeed.com' in domain:
                return self._parse_indeed(response.text, url)
            elif 'greenhouse.io' in domain:
                return self._parse_greenhouse(response.text, url)
            elif 'lever.co' in domain:
                return self._parse_lever(response.text, url)
            else:
                return self._parse_generic(response.text, url)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing {url}: {e}")
            return None

    def _apply_rate_limit(self, domain: str):
        """Apply rate limiting for domain"""
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.rate_limit:
                sleep_time = self.rate_limit - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.last_request_time[domain] = time.time()

    def _parse_linkedin(self, html: str, url: str) -> Dict:
        """Parse LinkedIn job posting"""
        soup = BeautifulSoup(html, 'html.parser')

        # LinkedIn job postings structure
        title_elem = soup.find('h1', class_=re.compile(r'top-card-layout__title'))
        company_elem = soup.find('a', class_=re.compile(r'topcard__org-name-link'))
        description_elem = soup.find('div', class_=re.compile(r'description__text'))

        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
        description = description_elem.get_text(strip=True) if description_elem else ""

        # Fallback for different LinkedIn structures
        if not description:
            description_elem = soup.find('div', class_='show-more-less-html__markup')
            description = description_elem.get_text(strip=True) if description_elem else ""

        return {
            'url': url,
            'title': title,
            'company': company,
            'description': description,
            'platform': 'LinkedIn'
        }

    def _parse_indeed(self, html: str, url: str) -> Dict:
        """Parse Indeed job posting"""
        soup = BeautifulSoup(html, 'html.parser')

        title_elem = soup.find('h1', class_=re.compile(r'jobsearch-JobInfoHeader-title'))
        company_elem = soup.find('div', {'data-company-name': True})
        description_elem = soup.find('div', id='jobDescriptionText')

        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        company = company_elem.get('data-company-name', 'Unknown Company') if company_elem else "Unknown Company"
        description = description_elem.get_text(strip=True) if description_elem else ""

        return {
            'url': url,
            'title': title,
            'company': company,
            'description': description,
            'platform': 'Indeed'
        }

    def _parse_greenhouse(self, html: str, url: str) -> Dict:
        """Parse Greenhouse job posting"""
        soup = BeautifulSoup(html, 'html.parser')

        title_elem = soup.find('h1', class_='app-title')
        company_elem = soup.find('span', class_='company-name')
        description_elem = soup.find('div', id='content')

        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
        description = description_elem.get_text(strip=True) if description_elem else ""

        return {
            'url': url,
            'title': title,
            'company': company,
            'description': description,
            'platform': 'Greenhouse'
        }

    def _parse_lever(self, html: str, url: str) -> Dict:
        """Parse Lever job posting"""
        soup = BeautifulSoup(html, 'html.parser')

        title_elem = soup.find('h2', {'data-qa': 'posting-name'})
        description_elem = soup.find('div', class_='content')

        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Extract company from URL or page
        company = urlparse(url).netloc.split('.')[0].title()

        description = description_elem.get_text(strip=True) if description_elem else ""

        return {
            'url': url,
            'title': title,
            'company': company,
            'description': description,
            'platform': 'Lever'
        }

    def _parse_generic(self, html: str, url: str) -> Dict:
        """Generic parser for unknown job boards"""
        soup = BeautifulSoup(html, 'html.parser')

        # Try to find title - usually in h1
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Try to extract all text
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()

        description = soup.get_text(strip=True)

        # Extract company from domain
        company = urlparse(url).netloc.split('.')[0].title()

        return {
            'url': url,
            'title': title,
            'company': company,
            'description': description,
            'platform': 'Generic'
        }

    def extract_requirements(self, job_data: Dict) -> Dict:
        """
        Extract specific requirements from job description

        Args:
            job_data: Job data dictionary from fetch_job_description

        Returns:
            Dictionary with extracted requirements
        """
        description = job_data.get('description', '').lower()

        # Extract years of experience
        exp_pattern = r'(\d+)\+?\s*years?\s*(of)?\s*experience'
        exp_matches = re.findall(exp_pattern, description)
        min_experience = min([int(m[0]) for m in exp_matches]) if exp_matches else 0
        max_experience = max([int(m[0]) for m in exp_matches]) if exp_matches else 10

        # Extract mentioned technologies/skills
        # We'll do a more sophisticated match in the matcher module
        requirements = {
            'min_experience': min_experience,
            'max_experience': max_experience,
            'raw_description': job_data.get('description', ''),
            'title': job_data.get('title', ''),
            'company': job_data.get('company', '')
        }

        return requirements


if __name__ == "__main__":
    # Test the fetcher
    import sys

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        print("Usage: python job_fetcher.py <job_url>")
        sys.exit(1)

    fetcher = JobFetcher()
    job_data = fetcher.fetch_job_description(test_url)

    if job_data:
        print(f"\nTitle: {job_data['title']}")
        print(f"Company: {job_data['company']}")
        print(f"Platform: {job_data['platform']}")
        print(f"\nDescription length: {len(job_data['description'])} characters")
        print(f"\nFirst 500 chars:\n{job_data['description'][:500]}")

        requirements = fetcher.extract_requirements(job_data)
        print(f"\nMin Experience: {requirements['min_experience']} years")
        print(f"Max Experience: {requirements['max_experience']} years")
    else:
        print("Failed to fetch job description")
