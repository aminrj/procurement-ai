"""Rating Agent for tender opportunity assessment"""

from typing import List
from pydantic import BaseModel, Field

from ..models import Tender
from ..services.llm import LLMService
from ..config import Config


class RatingResult(BaseModel):
    """Output from Rating Agent"""
    overall_score: float = Field(description="Score 0-10", ge=0, le=10)
    strategic_fit: float = Field(description="Fit score 0-10", ge=0, le=10)
    win_probability: float = Field(description="Win chance 0-10", ge=0, le=10)
    effort_required: float = Field(description="Effort 0-10", ge=0, le=10)
    strengths: List[str] = Field(description="Top 3 strengths")
    risks: List[str] = Field(description="Top 3 risks")
    recommendation: str = Field(description="Go/No-Go with reasoning")


class RatingAgent:
    """
    Agent 2: Rate tender opportunities

    Concept: Multi-dimensional scoring with reasoning
    Temperature: Low (0.1) for consistent evaluation
    """

    def __init__(self, llm: LLMService, config: Config = None):
        self.llm = llm
        self.config = config or Config()

    async def rate(self, tender: Tender, categories: List[str]) -> RatingResult:
        """Rate opportunity on multiple dimensions"""

        prompt = f"""Rate this tender opportunity for a small tech consultancy:

TENDER: {tender.title}
CLIENT: {tender.organization}
VALUE: {tender.estimated_value or "Not specified"}
CATEGORIES: {", ".join(categories)}
DESCRIPTION: {tender.description}

Evaluate on these dimensions:
1. STRATEGIC FIT: How well does this match our expertise in {", ".join(categories)}?
2. WIN PROBABILITY: Considering competition, requirements, and our capabilities
3. EFFORT REQUIRED: Complexity, timeline, resource needs

Provide realistic scores (0-10) with clear reasoning.
Identify top 3 strengths and top 3 risks.
Give a Go/No-Go recommendation."""

        system = "You are a business development expert evaluating tender opportunities. Be analytical and realistic, not optimistic."

        return await self.llm.generate_structured(
            prompt=prompt,
            response_model=RatingResult,
            system_prompt=system,
            temperature=self.config.TEMPERATURE_PRECISE,
        )
