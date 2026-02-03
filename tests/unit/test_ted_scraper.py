"""
Unit tests for TED Europa scraper

Tests use mocked HTTP responses to avoid actual API calls.
"""
import pytest
import httpx
import respx
from datetime import datetime, timedelta

from procurement_ai.scrapers import TEDScraper, APIError, RateLimitError, ParseError


@pytest.fixture
def scraper():
    """Create TEDScraper instance."""
    return TEDScraper()


@pytest.fixture
def mock_ted_response():
    """Sample TED API response structure."""
    return {
        "results": [
            {
                "noticeId": "123456-2026",
                "id": "TED-123456",
                "title": {"en": "Cloud Infrastructure Services"},
                "description": {"en": "Provision of cloud computing services including IaaS, PaaS, and SaaS solutions."},
                "buyer": {"name": {"en": "Ministry of Digital Affairs"}},
                "cpv": [{"code": "72000000"}, {"code": "72400000"}],
                "value": {"amount": 500000, "currency": "EUR"},
                "deadline": "2026-03-15T23:59:59",
                "publicationDate": "2026-02-01",
            },
            {
                "noticeId": "789012-2026",
                "title": {"en": "Cybersecurity Platform Development"},
                "shortDescription": {"en": "Development of advanced cybersecurity monitoring and threat detection platform."},
                "buyer": {"name": {"en": "National Security Agency"}},
                "cpv": [{"code": "72000000"}],
                "value": {"estimatedValue": 1200000},
                "tenderDeadline": "2026-04-01",
                "publicationDate": "2026-02-02",
            }
        ],
        "total": 2
    }


class TestTEDScraperInit:
    """Test scraper initialization."""
    
    def test_init_default(self):
        """Test scraper initializes with defaults."""
        scraper = TEDScraper()
        assert scraper.client is not None
        assert scraper.BASE_URL in str(scraper.client.base_url)
    
    def test_init_with_api_key(self):
        """Test scraper initializes with API key."""
        scraper = TEDScraper(api_key="test-key")
        assert "Authorization" in scraper.client.headers
        assert scraper.client.headers["Authorization"] == "Bearer test-key"
    
    def test_context_manager(self):
        """Test scraper works as context manager."""
        with TEDScraper() as scraper:
            assert scraper.client is not None


class TestTEDScraperSearch:
    """Test tender search functionality."""
    
    @respx.mock
    def test_search_tenders_success(self, scraper, mock_ted_response):
        """Test successful tender search."""
        # Mock API response
        respx.get("https://ted.europa.eu/api/v3.0/notices/search").mock(
            return_value=httpx.Response(200, json=mock_ted_response)
        )
        
        # Search tenders
        tenders = scraper.search_tenders(days_back=7, limit=100)
        
        # Verify results
        assert len(tenders) == 2
        assert tenders[0]["external_id"] == "123456-2026"
        assert tenders[0]["title"] == "Cloud Infrastructure Services"
        assert tenders[0]["source"] == "ted_europa"
        assert "72000000" in tenders[0]["cpv_codes"]
    
    @respx.mock
    def test_search_tenders_with_params(self, scraper):
        """Test search with custom parameters."""
        mock_response = {"results": [], "total": 0}
        route = respx.get("https://ted.europa.eu/api/v3.0/notices/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        scraper.search_tenders(days_back=14, cpv_codes=["72000000"], limit=50)
        
        # Verify request parameters
        assert route.called
        request = route.calls[0].request
        assert "pageSize=50" in str(request.url)
    
    @respx.mock
    def test_search_tenders_rate_limit(self, scraper):
        """Test handling of rate limit error."""
        respx.get("https://ted.europa.eu/api/v3.0/notices/search").mock(
            return_value=httpx.Response(429, text="Rate limit exceeded")
        )
        
        # RateLimitError should be raised without retry
        with pytest.raises(RateLimitError):
            scraper.search_tenders()
    
    @respx.mock
    def test_search_tenders_api_error(self, scraper):
        """Test handling of API errors (retries then fails)."""
        respx.get("https://ted.europa.eu/api/v3.0/notices/search").mock(
            return_value=httpx.Response(500, text="Internal server error")
        )
        
        # Should retry 3 times then raise RetryError wrapping APIError
        from tenacity import RetryError
        with pytest.raises(RetryError) as exc_info:
            scraper.search_tenders()
        # Check that the original exception was APIError with 500
        assert "APIError" in str(exc_info.value) or "500" in str(exc_info.value)
    
    @respx.mock
    def test_search_tenders_network_error(self, scraper):
        """Test handling of network errors (retries then fails)."""
        respx.get("https://ted.europa.eu/api/v3.0/notices/search").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )
        
        # Should retry 3 times then raise RetryError wrapping APIError
        from tenacity import RetryError
        with pytest.raises(RetryError) as exc_info:
            scraper.search_tenders()
        # Check that it retried and failed
        assert "APIError" in str(exc_info.value) or "Network error" in str(exc_info.value)
    
    @respx.mock
    def test_search_tenders_invalid_json(self, scraper):
        """Test handling of invalid JSON response."""
        respx.get("https://ted.europa.eu/api/v3.0/notices/search").mock(
            return_value=httpx.Response(200, text="not json")
        )
        
        with pytest.raises(ParseError):
            scraper.search_tenders()


class TestTEDScraperParsing:
    """Test data parsing logic."""
    
    def test_parse_search_results(self, scraper, mock_ted_response):
        """Test parsing of search results."""
        tenders = scraper._parse_search_results(mock_ted_response)
        
        assert len(tenders) == 2
        
        # Check first tender
        tender1 = tenders[0]
        assert tender1["external_id"] == "123456-2026"
        assert tender1["title"] == "Cloud Infrastructure Services"
        assert tender1["buyer_name"] == "Ministry of Digital Affairs"
        assert tender1["estimated_value"] == 500000
        assert tender1["deadline"] == "2026-03-15T23:59:59"
        assert tender1["source"] == "ted_europa"
        assert "72000000" in tender1["cpv_codes"]
        
        # Check second tender
        tender2 = tenders[1]
        assert tender2["external_id"] == "789012-2026"
        assert "Cybersecurity" in tender2["title"]
    
    def test_parse_empty_results(self, scraper):
        """Test parsing of empty results."""
        empty_response = {"results": [], "total": 0}
        tenders = scraper._parse_search_results(empty_response)
        assert tenders == []
    
    def test_parse_missing_fields(self, scraper):
        """Test parsing handles missing fields gracefully."""
        minimal_response = {
            "results": [
                {
                    "noticeId": "MIN-001",
                    "title": {"en": "Minimal Tender"},
                    # Missing most other fields
                }
            ]
        }
        
        tenders = scraper._parse_search_results(minimal_response)
        assert len(tenders) == 1
        assert tenders[0]["external_id"] == "MIN-001"
        assert tenders[0]["buyer_name"] == "Unknown buyer"
    
    def test_extract_description(self, scraper):
        """Test description extraction from various fields."""
        notice1 = {"description": {"en": "Full description here"}}
        assert scraper._extract_description(notice1) == "Full description here"
        
        notice2 = {"shortDescription": {"en": "Short description here"}}
        assert scraper._extract_description(notice2) == "Short description here"
        
        # When no description/shortDescription, returns default
        notice3 = {"title": {"en": "Just a title"}}
        assert scraper._extract_description(notice3) == "No description available"
    
    def test_extract_buyer(self, scraper):
        """Test buyer extraction."""
        notice = {"buyer": {"name": {"en": "Test Ministry"}}}
        assert scraper._extract_buyer(notice) == "Test Ministry"
        
        empty_notice = {}
        assert scraper._extract_buyer(empty_notice) == "Unknown buyer"
    
    def test_extract_cpv_codes(self, scraper):
        """Test CPV code extraction."""
        notice = {"cpv": [{"code": "72000000"}, {"code": "48000000"}]}
        codes = scraper._extract_cpv_codes(notice)
        assert "72000000" in codes
        assert "48000000" in codes
    
    def test_extract_value(self, scraper):
        """Test value extraction."""
        notice1 = {"value": {"amount": 500000}}
        assert scraper._extract_value(notice1) == 500000
        
        notice2 = {"value": {"estimatedValue": 1000000}}
        assert scraper._extract_value(notice2) == 1000000
        
        notice3 = {}
        assert scraper._extract_value(notice3) is None
    
    def test_build_notice_url(self, scraper):
        """Test URL building."""
        url = scraper._build_notice_url("123456-2026")
        assert "ted.europa.eu" in url
        assert "123456-2026" in url


class TestCPVCodes:
    """Test CPV code constants."""
    
    def test_it_cpv_codes_defined(self):
        """Test IT CPV codes are defined."""
        assert len(TEDScraper.IT_CPV_CODES) > 0
        assert "72000000" in TEDScraper.IT_CPV_CODES
        assert "48000000" in TEDScraper.IT_CPV_CODES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
