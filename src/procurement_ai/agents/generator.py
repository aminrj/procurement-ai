"""Document Generator Agent for bid proposals"""

from typing import List
from pydantic import BaseModel, Field

from ..models import Tender
from ..services.llm import LLMService
from ..config import Config


class BidDocument(BaseModel):
    """Output from Document Generator"""
    executive_summary: str = Field(description="2-3 paragraph summary")
    technical_approach: str = Field(description="How we'll solve it")
    value_proposition: str = Field(description="Why choose us")
    timeline_estimate: str = Field(description="Project timeline")


class DocumentGenerator:
    """
    Agent 3: Generate bid documents

    Concept: Creative generation with constraints
    Temperature: Higher (0.7) for variety while maintaining professionalism
    """

    def __init__(self, llm: LLMService, config: Config = None):
        self.llm = llm
        self.config = config or Config()

    async def generate(
        self, tender: Tender, categories: List[str], strengths: List[str]
    ) -> BidDocument:
        """Generate professional bid document content"""

        prompt = f"""Create compelling bid document content for this tender:

TENDER: {tender.title}
CLIENT: {tender.organization}
OUR EXPERTISE: {", ".join(categories)}
KEY STRENGTHS: {", ".join(strengths)}
REQUIREMENTS: {tender.description}

Generate:
1. EXECUTIVE SUMMARY: 2-3 paragraphs highlighting our value proposition
2. TECHNICAL APPROACH: Our methodology and solution design
3. VALUE PROPOSITION: Why we're the best choice (unique differentiators)
4. TIMELINE ESTIMATE: Realistic project phases and milestones

Make it professional, specific to this tender, and compelling.
Use concrete language, avoid generic statements."""

        system = "You are an expert proposal writer with 15 years winning government contracts. Write persuasively but authentically."

        return await self.llm.generate_structured(
            prompt=prompt,
            response_model=BidDocument,
            system_prompt=system,
            temperature=self.config.TEMPERATURE_CREATIVE,
        )
