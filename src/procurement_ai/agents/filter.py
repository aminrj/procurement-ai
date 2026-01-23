"""Filter Agent for tender relevance classification"""

from typing import List
from pydantic import BaseModel, Field

from ..models import Tender, TenderCategory
from ..services.llm import LLMService
from ..config import Config


class FilterResult(BaseModel):
    """Output from Filter Agent"""
    is_relevant: bool = Field(description="Is tender relevant?")
    confidence: float = Field(description="Confidence 0-1", ge=0, le=1)
    categories: List[TenderCategory] = Field(description="Detected categories")
    reasoning: str = Field(description="Explanation for decision")


class FilterAgent:
    """
    Agent 1: Filter tenders by relevance

    Concept: Use LLM for classification with reasoning
    Temperature: Low (0.1) for consistency
    """

    def __init__(self, llm: LLMService, config: Config = None):
        self.llm = llm
        self.config = config or Config()

    async def filter(self, tender: Tender) -> FilterResult:
        """Determine if tender is relevant"""

        prompt = f"""Analyze this procurement tender:

TITLE: {tender.title}

DESCRIPTION: {tender.description}

ORGANIZATION: {tender.organization}

CRITERIA FOR RELEVANCE:
A tender is relevant if it involves:
1. Cybersecurity (threat detection, pentesting, security audits, SIEM)
2. Artificial Intelligence/ML (AI solutions, automation, ML models)
3. Software Development (custom software, web/mobile apps, SaaS)

A tender is NOT relevant if it's only:
- Hardware procurement
- Physical infrastructure
- Non-technical services (facilities, catering, etc.)

Analyze carefully and provide your assessment."""

        system = "You are an expert procurement analyst specializing in technology tenders. Be precise and conservative."

        return await self.llm.generate_structured(
            prompt=prompt,
            response_model=FilterResult,
            system_prompt=system,
            temperature=self.config.TEMPERATURE_PRECISE,
        )
