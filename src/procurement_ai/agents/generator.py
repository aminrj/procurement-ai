"""Document Generator Agent for bid proposals"""

from typing import List, Optional
from pydantic import BaseModel, Field

from ..models import Tender
from ..services.llm import LLMService
from ..config import Config
from ..rag import KnowledgeBase


class BidDocument(BaseModel):
    """Output from Document Generator"""
    executive_summary: str = Field(description="2-3 paragraph summary")
    technical_approach: str = Field(description="How we'll solve it")
    value_proposition: str = Field(description="Why choose us")
    timeline_estimate: str = Field(description="Project timeline")


class DocumentGenerator:
    """
    Agent 3: Generate bid documents
    
    Supports RAG (Retrieval-Augmented Generation) for higher quality outputs.

    Concept: Creative generation with constraints
    Temperature: Higher (0.7) for variety while maintaining professionalism
    """

    def __init__(
        self,
        llm: LLMService,
        config: Config = None,
        knowledge_base: Optional[KnowledgeBase] = None
    ):
        self.llm = llm
        self.config = config or Config()
        self.knowledge_base = knowledge_base
        self.use_rag = knowledge_base is not None

    async def generate(
        self, tender: Tender, categories: List[str], strengths: List[str]
    ) -> BidDocument:
        """Generate professional bid document content"""

        # Build base prompt
        prompt_base = f"""Create compelling bid document content for this tender:

TENDER: {tender.title}
CLIENT: {tender.organization}
OUR EXPERTISE: {", ".join(categories)}
KEY STRENGTHS: {", ".join(strengths)}
REQUIREMENTS: {tender.description}"""

        # Augment with RAG if available
        if self.use_rag and self.knowledge_base:
            # Determine category from tender categories
            category = categories[0] if categories else None
            
            # Retrieve relevant examples
            context = await self.knowledge_base.get_context(
                query=tender.description,
                k=2,
                min_similarity=self.config.RAG_MIN_SIMILARITY,
                category=category
            )
            
            if context:
                # Add examples to prompt
                prompt = f"""{prompt_base}

---
HIGH-QUALITY EXAMPLES (for reference):

{context}
---

Using the quality and structure demonstrated in the examples above, generate:"""
            else:
                prompt = f"""{prompt_base}

Generate:"""
        else:
            prompt = f"""{prompt_base}

Generate:"""

        # Add generation instructions
        prompt += """
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
