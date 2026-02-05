"""Unit tests for TED Europa scraper."""

import json
import httpx
import pytest
import respx
from tenacity import RetryError

from procurement_ai.scrapers import APIError, ParseError, RateLimitError, TEDScraper


@pytest.fixture
def scraper():
    return TEDScraper()


@pytest.fixture
def mock_ted_response():
    return {
        "results": [
            {
                "noticeId": "123456-2026",
                "id": "TED-123456",
                "title": {"en": "Cloud Infrastructure Services"},
                "description": {
                    "en": "Provision of cloud computing services including IaaS, PaaS, and SaaS solutions."
                },
                "buyer": {"name": {"en": "Ministry of Digital Affairs"}},
                "cpv": [{"code": "72000000"}, {"code": "72400000"}],
                "value": {"amount": 500000, "currency": "EUR"},
                "deadline": "2026-03-15T23:59:59",
                "publicationDate": "2026-02-01",
            },
            {
                "noticeId": "789012-2026",
                "title": {"en": "Cybersecurity Platform Development"},
                "shortDescription": {
                    "en": "Development of advanced cybersecurity monitoring and threat detection platform."
                },
                "buyer": {"name": {"en": "National Security Agency"}},
                "cpv": [{"code": "72000000"}],
                "value": {"estimatedValue": 1200000},
                "tenderDeadline": "2026-04-01",
                "publicationDate": "2026-02-02",
            },
        ],
        "total": 2,
    }


class TestTEDScraperInit:
    def test_init_default(self):
        scraper = TEDScraper()
        assert scraper.client is not None
        assert scraper.BASE_URL in str(scraper.client.base_url)

    def test_init_with_api_key(self):
        scraper = TEDScraper(api_key="test-key")
        assert "Authorization" in scraper.client.headers
        assert scraper.client.headers["Authorization"] == "Bearer test-key"

    def test_context_manager(self):
        with TEDScraper() as scraper:
            assert scraper.client is not None


class TestTEDScraperSearch:
    @respx.mock
    def test_search_tenders_success(self, scraper, mock_ted_response):
        route = respx.post("https://api.ted.europa.eu/v3/notices/search").mock(
            return_value=httpx.Response(200, json=mock_ted_response)
        )

        tenders = scraper.search_tenders(days_back=7, limit=100)

        assert route.called
        assert len(tenders) == 2
        assert tenders[0]["external_id"] == "123456-2026"
        assert tenders[0]["title"] == "Cloud Infrastructure Services"
        assert tenders[0]["source"] == "ted_europa"
        assert "72000000" in tenders[0]["cpv_codes"]

    @respx.mock
    def test_search_tenders_with_params(self, scraper):
        route = respx.post("https://api.ted.europa.eu/v3/notices/search").mock(
            return_value=httpx.Response(200, json={"results": [], "total": 0})
        )

        scraper.search_tenders(days_back=14, cpv_codes=["72000000"], limit=50)

        assert route.called
        payload = json.loads(route.calls[0].request.read().decode("utf-8"))
        assert payload["limit"] == 50
        assert 'cpv="72000000"' in payload["query"]

    @respx.mock
    def test_search_tenders_rate_limit(self, scraper):
        respx.post("https://api.ted.europa.eu/v3/notices/search").mock(
            return_value=httpx.Response(429, text="Rate limit exceeded")
        )

        with pytest.raises(RateLimitError):
            scraper.search_tenders()

    @respx.mock
    def test_search_tenders_api_error(self, scraper):
        respx.post("https://api.ted.europa.eu/v3/notices/search").mock(
            return_value=httpx.Response(500, text="Internal server error")
        )

        with pytest.raises(RetryError):
            scraper.search_tenders()

    @respx.mock
    def test_search_tenders_network_error(self, scraper):
        respx.post("https://api.ted.europa.eu/v3/notices/search").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(RetryError):
            scraper.search_tenders()

    @respx.mock
    def test_search_tenders_invalid_json(self, scraper):
        respx.post("https://api.ted.europa.eu/v3/notices/search").mock(
            return_value=httpx.Response(200, text="not json")
        )

        with pytest.raises(ParseError):
            scraper.search_tenders()


class TestTEDScraperParsing:
    def test_parse_search_results(self, scraper, mock_ted_response):
        tenders = scraper._parse_search_results(mock_ted_response)

        assert len(tenders) == 2

        tender1 = tenders[0]
        assert tender1["external_id"] == "123456-2026"
        assert tender1["title"] == "Cloud Infrastructure Services"
        assert tender1["buyer_name"] == "Ministry of Digital Affairs"
        assert tender1["estimated_value"] == 500000.0
        assert tender1["deadline"] == "2026-03-15T23:59:59"
        assert "72000000" in tender1["cpv_codes"]

        tender2 = tenders[1]
        assert tender2["external_id"] == "789012-2026"
        assert "Cybersecurity" in tender2["title"]

    def test_parse_empty_results(self, scraper):
        tenders = scraper._parse_search_results({"results": [], "total": 0})
        assert tenders == []

    def test_parse_missing_fields(self, scraper):
        tenders = scraper._parse_search_results(
            {"results": [{"noticeId": "MIN-001", "title": {"en": "Minimal Tender"}}]}
        )
        assert len(tenders) == 1
        assert tenders[0]["external_id"] == "MIN-001"
        assert tenders[0]["buyer_name"] == "Unknown buyer"

    def test_extract_description(self, scraper):
        assert scraper._extract_description({"description": {"en": "Full description here"}}) == "Full description here"
        assert scraper._extract_description({"shortDescription": {"en": "Short description here"}}) == "Short description here"
        assert scraper._extract_description({"title": {"en": "Just a title"}}) == "No description available"

    def test_extract_buyer(self, scraper):
        assert scraper._extract_buyer({"buyer": {"name": {"en": "Test Ministry"}}}) == "Test Ministry"
        assert scraper._extract_buyer({}) == "Unknown buyer"

    def test_extract_cpv_codes(self, scraper):
        codes = scraper._extract_cpv_codes({"cpv": [{"code": "72000000"}, {"code": "48000000"}]})
        assert "72000000" in codes
        assert "48000000" in codes

    def test_extract_value(self, scraper):
        assert scraper._extract_value({"value": {"amount": 500000}}) == 500000.0
        assert scraper._extract_value({"value": {"estimatedValue": 1000000}}) == 1000000.0
        assert scraper._extract_value({}) is None

    def test_build_notice_url(self, scraper):
        url = scraper._build_notice_url("123456-2026")
        assert "ted.europa.eu" in url
        assert "123456-2026" in url


class TestCPVCodes:
    def test_it_cpv_codes_defined(self):
        assert len(TEDScraper.IT_CPV_CODES) > 0
        assert "72000000" in TEDScraper.IT_CPV_CODES
        assert "48000000" in TEDScraper.IT_CPV_CODES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
