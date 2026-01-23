"""Configuration for Procurement AI system"""

import os
from typing import Optional


class Config:
    """Single place for all settings"""

    # LLM Configuration
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
    
    # Temperature settings
    TEMPERATURE_PRECISE: float = 0.1  # For filtering/rating
    TEMPERATURE_CREATIVE: float = 0.7  # For document generation
    
    # API Settings
    API_TIMEOUT: float = 120.0
    MAX_RETRIES: int = 3
    
    # Scoring thresholds
    MIN_CONFIDENCE: float = 0.6  # Minimum confidence to proceed
    MIN_SCORE_FOR_DOCUMENT: float = 7.0  # Minimum rating to generate docs
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables"""
        return cls()
    
    @classmethod
    def for_testing(cls, llm_url: Optional[str] = None) -> "Config":
        """Create config for testing"""
        config = cls()
        if llm_url:
            config.LLM_BASE_URL = llm_url
        return config
