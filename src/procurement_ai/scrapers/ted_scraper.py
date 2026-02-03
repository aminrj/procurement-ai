"""
TED Europa Tender Scraper

Fetches public procurement tenders from TED (Tenders Electronic Daily).
TED is the official EU portal for publishing public procurement notices.

API Documentation: https://docs.ted.europa.eu/api/latest/search.html
"""
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from bs4 import BeautifulSoup
import re

from procurement_ai.scrapers.exceptions import APIError, RateLimitError, ParseError


class TEDScraper:
    """
    Client for TED Europa API.
    
    Fetches tenders published in the European Union and EEA countries.
    Focuses on IT/Software/Cybersecurity categories (CPV codes 72000000, 48000000).
    """
    
    # TED API endpoint (POST to /v3/notices/search)
    BASE_URL = "https://api.ted.europa.eu"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TED scraper.
        
        Args:
            api_key: TED API key (if required, currently optional)
        """
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers=self._get_headers()
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "ProcurementAI/1.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type((RateLimitError, ParseError))  # Don't retry these
    )
    def search_tenders(
        self,
        days_back: int = 7,
        limit: int = 100,
        page: int = 1
    ) -> List[Dict]:
        """
        Search for recent tenders.
        
        Args:
            days_back: Number of days to look back (default: 7)
            limit: Maximum number of results per page (default: 100, max: 250)
            page: Page number for pagination (default: 1)
        
        Returns:
            List of tender dictionaries with basic info (id, date, country)
            Use get_tender_details(notice_id) to get full description for LLM analysis
        
        Raises:
            APIError: If API request fails
            RateLimitError: If rate limit is exceeded
            ParseError: If response parsing fails
        """
        # Build TED expert query - recent tenders sorted by date
        query = f"publication-date >= today(-{days_back}) SORT BY publication-date DESC"
        
        # Build request body for POST
        payload = {
            "query": query,
            "fields": ["ND", "PD", "OJ", "CY", "AA"],  # Simple fields that work
            "page": page,
            "limit": min(limit, 250),  # API max 250 per page
            "scope": "ACTIVE",
            "paginationMode": "PAGE_NUMBER",
            "onlyLatestVersions": False,
            "checkQuerySyntax": False,
        }
        
        try:
            response = self.client.post("/v3/notices/search", json=payload)
            
            # Handle rate limiting (don't retry, fail immediately)
            if response.status_code == 429:
                raise RateLimitError("TED API rate limit exceeded")
            
            # Handle errors
            if response.status_code >= 400:
                raise APIError(f"TED API error: {response.status_code} - {response.text[:500]}")
            
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            return self._parse_search_results(data)
            
        except RateLimitError:
            # Re-raise RateLimitError without retry
            raise
        except httpx.RequestError as e:
            raise APIError(f"Network error: {str(e)}")
        except ValueError as e:
            raise ParseError(f"Invalid JSON response: {str(e)}")
    
    def _parse_search_results(self, data: Dict) -> List[Dict]:
        """
        Parse TED API search results into simplified tender format.
        
        Args:
            data: Raw API response
        
        Returns:
            List of parsed tender dictionaries
        """
        try:
            # Extract notices from various possible response structures
            notices = []
            for key in ("notices", "results", "content", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    notices = value
                    break
            
            tenders = []
            
            for notice in notices:
                # Extract key fields from TED API response
                notice_id = notice.get("ND") or notice.get("publication-number", "")
                title = notice.get("TD") or notice.get("title", "Untitled Tender")
                buyer = notice.get("AA") or notice.get("buyer-name", "Unknown Buyer")
                cpv = notice.get("CPV") or ""
                pub_date = notice.get("PD") or notice.get("publication-date")
                
                tender = {
                    "external_id": notice_id,
                    "title": title[:500] if isinstance(title, str) else "Untitled",
                    "description": title,  # Use title as description for MVP
                    "buyer_name": buyer if isinstance(buyer, str) else "Unknown Buyer",
                    "cpv_codes": [cpv] if cpv else [],
                    "estimated_value": None,  # Not available in basic search
                    "deadline": None,  # Not in basic fields
                    "published_date": pub_date,
                    "source": "ted_europa",
                    "source_url": self._build_notice_url(notice_id),
                    "raw_data": notice,
                }
                
                # Only include tenders with essential fields
                if tender["external_id"] and tender["title"]:
                    tenders.append(tender)
            
            return tenders
            
        except (KeyError, TypeError) as e:
            raise ParseError(f"Failed to parse tender data: {str(e)}")
    
    def _build_notice_url(self, notice_id: str) -> Optional[str]:
        """Build URL to full tender notice."""
        if notice_id:
            return f"https://ted.europa.eu/udl?uri=TED:NOTICE:{notice_id}"
        return None
    
    def get_tender_details(self, notice_id: str) -> Optional[Dict]:
        """
        Fetch full tender details from HTML page - simple scraping approach.
        
        Args:
            notice_id: Notice ID from search results (e.g., "76154-2026")
            
        Returns:
            Dictionary with title, description, organization, deadline, value
            or None if failed
        """
        try:
            # Fetch HTML page
            html_url = f"https://ted.europa.eu/en/notice/{notice_id}/html"
            response = self.client.get(html_url, follow_redirects=True)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title from page title tag
            title = "Untitled Tender"
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
            
            # Extract description from main content
            description = title  # Default to title
            notice_div = soup.find('div', id='notice') or soup.find('div', id='summary')
            if notice_div:
                text = notice_div.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Has meaningful content
                    description = text[:1000]  # First 1000 chars
            
            # Try to find organization name
            organization = "Unknown Buyer"
            text_content = response.text
            org_patterns = [
                r'(?:Buyer|Organization|Authority|Contracting body)[:]\s*([^\n]{3,100})',
                r'Name[:]\s*([^\n]{3,100})',
            ]
            for pattern in org_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    org = match.group(1).strip()
                    if len(org) > 3:
                        organization = org[:255]
                        break
            
            return {
                'title': title[:500],
                'description': description,
                'organization': organization,
                'deadline': None,
                'estimated_value': None
            }
            
        except Exception as e:
            return None
    
    def _parse_tender_xml(self, xml_content: str, notice_id: str) -> Dict:
        """
        Parse TED XML to extract title, description, buyer, value.
        
        TED XML is complex with multiple namespaces. We try to extract
        the most common fields.
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Remove namespace prefixes for easier searching
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
            
            details = {
                'title': None,
                'description': None,
                'buyer_name': None,
                'estimated_value': None,
                'deadline': None
            }
            
            # Try to find title (multiple possible locations)
            title_paths = [
                './/TITLE',
                './/SHORT_DESCR',
                './/ML_TITLES/ML_TI_DOC',
            ]
            for path in title_paths:
                elem = root.find(path)
                if elem is not None and elem.text:
                    details['title'] = elem.text.strip()[:500]
                    break
            
            # Try to find description
            desc_paths = [
                './/OBJECT_DESCR',
                './/SHORT_DESCR',
                './/P[@TYPE="DESCRIPTION"]',
            ]
            for path in desc_paths:
                elem = root.find(path)
                if elem is not None and elem.text:
                    details['description'] = elem.text.strip()[:2000]
                    break
            
            # Try to find buyer/contracting authority
            buyer_paths = [
                './/OFFICIALNAME',
                './/ORGANISATION/OFFICIALNAME',
                './/ADDRESS_CONTRACTING_BODY/OFFICIALNAME',
            ]
            for path in buyer_paths:
                elem = root.find(path)
                if elem is not None and elem.text:
                    details['buyer_name'] = elem.text.strip()[:255]
                    break
            
            # Try to find estimated value
            value_elem = root.find('.//VAL_ESTIMATED_TOTAL')
            if value_elem is not None and value_elem.text:
                currency = value_elem.get('CURRENCY', '€')
                details['estimated_value'] = f"{currency} {value_elem.text}"
            
            # Try to find deadline
            deadline_elem = root.find('.//DATE_RECEIPT_TENDERS')
            if deadline_elem is not None and deadline_elem.text:
                details['deadline'] = deadline_elem.text.strip()
            
            return details
            
        except Exception as e:
            # Return empty dict if parsing fails
            return {}
    
    def close(self):
        """Close HTTP client connection."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
