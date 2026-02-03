"""
Custom exceptions for web scraping operations
"""


class ScraperError(Exception):
    """Base exception for scraper errors"""
    pass


class APIError(ScraperError):
    """API request failed"""
    pass


class RateLimitError(APIError):
    """API rate limit exceeded"""
    pass


class ParseError(ScraperError):
    """Failed to parse response data"""
    pass
