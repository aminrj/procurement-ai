"""
Procurement Intelligence System - Complete MVP
Learn LLM engineering by building a real solution

This single file demonstrates:
1. LLM API calls (LM Studio)
2. Structured outputs with Pydantic
3. Prompt engineering patterns
4. Multi-agent orchestration
5. Real-world business logic

Fast.ai approach: Start with working code, understand later
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# CONFIGURATION
# ============================================================================


class Config:
    """Single place for all settings"""

    LLM_BASE_URL = "http://localhost:1234/v1"  # LM Studio
    LLM_MODEL = "openai/gpt-oss-20b"
    # LLM_MODEL = "llama-3.1-8b-instruct"
    TEMPERATURE_PRECISE = 0.1  # For filtering/rating
    TEMPERATURE_CREATIVE = 0.7  # For document generation


# ============================================================================
# DATA MODELS (Pydantic for validation)
# ============================================================================


class TenderCategory(str, Enum):
    CYBERSECURITY = "cybersecurity"
    ARTIFICIAL_INTELLIGENCE = "ai"
    SOFTWARE_DEVELOPMENT = "software"
    OTHER = "other"


class FilterResult(BaseModel):
    """Output from Filter Agent"""

    is_relevant: bool = Field(description="Is tender relevant?")
    confidence: float = Field(description="Confidence 0-1", ge=0, le=1)
    categories: List[TenderCategory] = Field(description="Detected categories")
    reasoning: str = Field(description="Explanation for decision")


class RatingResult(BaseModel):
    """Output from Rating Agent"""

    overall_score: float = Field(description="Score 0-10", ge=0, le=10)
    strategic_fit: float = Field(description="Fit score 0-10", ge=0, le=10)
    win_probability: float = Field(description="Win chance 0-10", ge=0, le=10)
    effort_required: float = Field(description="Effort 0-10", ge=0, le=10)
    strengths: List[str] = Field(description="Top 3 strengths")
    risks: List[str] = Field(description="Top 3 risks")
    recommendation: str = Field(description="Go/No-Go with reasoning")


class BidDocument(BaseModel):
    """Output from Document Generator"""

    executive_summary: str = Field(description="2-3 paragraph summary")
    technical_approach: str = Field(description="How we'll solve it")
    value_proposition: str = Field(description="Why choose us")
    timeline_estimate: str = Field(description="Project timeline")


class Tender(BaseModel):
    """Input tender data"""

    id: str
    title: str
    description: str
    organization: str
    deadline: str
    estimated_value: Optional[str] = None


class ProcessedTender(BaseModel):
    """Complete analysis result"""

    tender: Tender
    filter_result: Optional[FilterResult] = None
    rating_result: Optional[RatingResult] = None
    bid_document: Optional[BidDocument] = None
    processing_time: float = 0.0
    status: str = "pending"


# ============================================================================
# CORE LLM SERVICE
# ============================================================================


class LLMService:
    """
    Simple LLM service for LM Studio

    Key Concepts Demonstrated:
    - OpenAI-compatible API calls
    - Structured output with JSON schema
    - Error handling and retries
    - Temperature control
    """

    def __init__(self):
        self.base_url = Config.LLM_BASE_URL
        self.model = Config.LLM_MODEL

    async def generate_structured(
        self,
        prompt: str,
        response_model: BaseModel,
        system_prompt: str,
        temperature: float = 0.1,
        max_retries: int = 3,
    ) -> BaseModel:
        """
        Generate structured output matching Pydantic model

        This is the CORE pattern for LLM engineering:
        1. Define output schema with Pydantic
        2. Inject schema into prompt
        3. Parse and validate response
        """

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": self._build_structured_prompt(prompt, response_model),
            },
        ]

        # Retry logic for robustness
        for attempt in range(max_retries):
            try:
                response = await self._call_api(messages, temperature)
                cleaned = self._clean_json(response)

                # Debug output (can be removed later)
                if attempt > 0:  # Only show debug on retries
                    print(f"    Raw response: {response[:200]}...")
                    print(f"    Cleaned: {cleaned[:200]}...")

                # Additional validation - check if it looks like JSON
                if not cleaned.startswith("{") or not cleaned.endswith("}"):
                    raise ValueError(
                        f"Response doesn't look like JSON: {cleaned[:100]}..."
                    )

                # Try to parse first to give better error messages
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON structure: {e}. Content: {cleaned[:200]}..."
                    )

                return response_model.model_validate(parsed)
            except Exception as e:
                print(
                    f"    Attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}..."
                )
                if attempt == max_retries - 1:
                    raise Exception(f"Failed after {max_retries} attempts: {e}")
                await asyncio.sleep(2)  # Longer pause for retries

    def _build_structured_prompt(self, prompt: str, model: BaseModel) -> str:
        """Add schema to prompt for better structured output"""

        # Create a proper example with correct field types and values
        example_fields = {}
        for field_name, field_info in model.model_fields.items():
            if field_name == "confidence":
                example_fields[field_name] = 0.85
            elif field_name in [
                "overall_score",
                "strategic_fit",
                "win_probability",
                "effort_required",
            ]:
                example_fields[field_name] = 8.5
            elif field_name == "is_relevant":
                example_fields[field_name] = True
            elif field_name == "categories":
                # Use actual enum values
                if (
                    hasattr(model, "model_fields")
                    and "categories" in model.model_fields
                ):
                    example_fields[field_name] = ["cybersecurity", "ai", "software"]
                else:
                    example_fields[field_name] = ["example_category"]
            elif field_name in ["strengths", "risks"]:
                example_fields[field_name] = [
                    "Example strength 1",
                    "Example strength 2",
                    "Example strength 3",
                ]
            elif "reasoning" in field_name or "recommendation" in field_name:
                example_fields[field_name] = (
                    "Example reasoning or recommendation text here"
                )
            else:
                example_fields[field_name] = "Example text content"

        example_json = json.dumps(example_fields, indent=2)

        return f"""{prompt}

You must respond with ACTUAL DATA in JSON format, not a schema.

Here's the expected format with CORRECT value types:
{example_json}

CRITICAL VALUE REQUIREMENTS:
- confidence: Use decimal 0-1 (like 0.95, not 9.5)
- Categories: Use EXACT enum values: "cybersecurity", "ai", "software", "other" (lowercase)
- Scores: Use numbers 0-10 (like 8.5)
- Arrays: Use actual lists with 3 items for strengths/risks
- All text fields: Provide meaningful actual content

FORMATTING RULES:
- Start with {{ and end with }}
- No explanations before or after JSON
- No code blocks or backticks"""

    def _clean_json(self, text: str) -> str:
        """Remove markdown artifacts and extract valid JSON from LLM response"""
        cleaned = text.strip()

        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Find the JSON object by looking for balanced braces
        start_idx = cleaned.find("{")
        if start_idx == -1:
            return cleaned

        brace_count = 0
        end_idx = -1

        for i, char in enumerate(cleaned[start_idx:], start_idx):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break

        if end_idx != -1:
            return cleaned[start_idx : end_idx + 1]

        return cleaned

    async def _call_api(self, messages: list, temperature: float) -> str:
        """Make API call to LM Studio"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 2000,
                },
            )

            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")

            return response.json()["choices"][0]["message"]["content"]


# ============================================================================
# AI AGENTS (The Business Logic)
# ============================================================================


class FilterAgent:
    """
    Agent 1: Filter tenders by relevance

    Concept: Use LLM for classification with reasoning
    Temperature: Low (0.1) for consistency
    """

    def __init__(self, llm: LLMService):
        self.llm = llm

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
            temperature=Config.TEMPERATURE_PRECISE,
        )


class RatingAgent:
    """
    Agent 2: Rate tender opportunities

    Concept: Multi-dimensional scoring with reasoning
    Temperature: Low (0.1) for consistent evaluation
    """

    def __init__(self, llm: LLMService):
        self.llm = llm

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
            temperature=Config.TEMPERATURE_PRECISE,
        )


class DocumentGenerator:
    """
    Agent 3: Generate bid documents

    Concept: Creative generation with constraints
    Temperature: Higher (0.7) for variety while maintaining professionalism
    """

    def __init__(self, llm: LLMService):
        self.llm = llm

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
            temperature=Config.TEMPERATURE_CREATIVE,
        )


# ============================================================================
# ORCHESTRATOR (Brings it all together)
# ============================================================================


class ProcurementOrchestrator:
    """
    Main orchestration logic

    Concept: Sequential agent execution with conditional logic
    This is a simple linear workflow - later we'll compare with LangGraph
    """

    def __init__(self):
        self.llm = LLMService()
        self.filter_agent = FilterAgent(self.llm)
        self.rating_agent = RatingAgent(self.llm)
        self.doc_generator = DocumentGenerator(self.llm)

    async def process_tender(self, tender: Tender) -> ProcessedTender:
        """Process a single tender through the full pipeline"""

        start_time = datetime.now()
        result = ProcessedTender(tender=tender)

        try:
            # STEP 1: Filter for relevance
            print(f"\n{'=' * 60}")
            print(f"Processing: {tender.title[:50]}...")
            print(f"{'=' * 60}")
            print("\n[1/3] Filtering for relevance...")

            result.filter_result = await self.filter_agent.filter(tender)

            print(f"  ✓ Relevant: {result.filter_result.is_relevant}")
            print(f"  ✓ Confidence: {result.filter_result.confidence:.2f}")
            print(
                f"  ✓ Categories: {', '.join([c.value for c in result.filter_result.categories])}"
            )

            # If not relevant, stop here
            if (
                not result.filter_result.is_relevant
                or result.filter_result.confidence < 0.6
            ):
                result.status = "filtered_out"
                print(f"\n  → Skipping (not relevant)")
                return result

            # STEP 2: Rate the opportunity
            print(f"\n[2/3] Rating opportunity...")

            categories = [c.value for c in result.filter_result.categories]
            result.rating_result = await self.rating_agent.rate(tender, categories)

            print(f"  ✓ Overall Score: {result.rating_result.overall_score:.1f}/10")
            print(f"  ✓ Win Probability: {result.rating_result.win_probability:.1f}/10")
            print(f"  ✓ Recommendation: {result.rating_result.recommendation[:100]}...")

            # If score is low, don't generate documents
            if result.rating_result.overall_score < 7.0:
                result.status = "rated_low"
                print(f"\n  → Skipping document generation (score < 7.0)")
                return result

            # STEP 3: Generate bid document
            print(f"\n[3/3] Generating bid document...")

            result.bid_document = await self.doc_generator.generate(
                tender, categories, result.rating_result.strengths
            )

            print(f"  ✓ Document generated")
            print(f"  ✓ Summary: {result.bid_document.executive_summary[:100]}...")

            result.status = "complete"

        except Exception as e:
            result.status = f"error: {str(e)}"
            print(f"\n  ✗ Error: {e}")

        finally:
            result.processing_time = (datetime.now() - start_time).total_seconds()
            print(f"\n  Processing time: {result.processing_time:.2f}s")

        return result


# ============================================================================
# DEMO / TEST DATA
# ============================================================================

SAMPLE_TENDERS = [
    Tender(
        id="TED-2025-001",
        title="AI-Powered Cybersecurity Platform for Critical Infrastructure",
        description="""The National Cybersecurity Agency seeks a vendor to develop an 
        artificial intelligence-based threat detection and response system. The solution 
        must monitor network traffic across government infrastructure, identify anomalies 
        using machine learning, and provide automated incident response. Integration with 
        existing SIEM tools required. Must handle 100TB+ daily data volume with real-time 
        processing capabilities.""",
        organization="National Cybersecurity Agency",
        deadline="2025-04-15",
        estimated_value="€3,200,000",
    ),
    Tender(
        id="TED-2025-002",
        title="Office Furniture Procurement for New Government Building",
        description="""Supply and installation of ergonomic office furniture for 500 
        workstations including desks, chairs, storage cabinets, and meeting room furniture. 
        Must meet sustainability criteria and include 5-year warranty.""",
        organization="Ministry of Public Works",
        deadline="2025-03-01",
        estimated_value="€450,000",
    ),
    Tender(
        id="TED-2025-003",
        title="Custom CRM Software Development for Healthcare Network",
        description="""Healthcare network requires custom customer relationship management 
        software to manage patient interactions, appointment scheduling, and medical records 
        integration. Must be GDPR and HIPAA compliant, include mobile app, and integrate 
        with existing hospital management systems. Cloud-based SaaS solution preferred.""",
        organization="Regional Healthcare Authority",
        deadline="2025-05-30",
        estimated_value="€1,800,000",
    ),
]


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def main():
    """Run the complete demo"""

    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         PROCUREMENT INTELLIGENCE SYSTEM - MVP DEMO           ║
║                                                              ║
║  Learning LLM Engineering with Real-World Applications       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Make sure LM Studio is running on localhost:1234!
""")

    # Initialize orchestrator
    orchestrator = ProcurementOrchestrator()

    # Process all sample tenders
    results = []
    for tender in SAMPLE_TENDERS:
        result = await orchestrator.process_tender(tender)
        results.append(result)

    # Summary report
    print(f"\n\n{'=' * 60}")
    print("PROCESSING SUMMARY")
    print(f"{'=' * 60}\n")

    relevant = sum(
        1 for r in results if r.filter_result and r.filter_result.is_relevant
    )
    high_rated = sum(
        1 for r in results if r.rating_result and r.rating_result.overall_score >= 7.0
    )
    docs_generated = sum(1 for r in results if r.bid_document is not None)

    print(f"Total Tenders Processed: {len(results)}")
    print(f"Relevant Tenders: {relevant}")
    print(f"High-Rated (≥7.0): {high_rated}")
    print(f"Documents Generated: {docs_generated}")
    print(f"\nTotal Processing Time: {sum(r.processing_time for r in results):.2f}s")
    print(
        f"Average Time per Tender: {sum(r.processing_time for r in results) / len(results):.2f}s\n"
    )

    # Detailed results
    for i, result in enumerate(results, 1):
        print(f"\n{'─' * 60}")
        print(f"TENDER {i}: {result.tender.title[:45]}...")
        print(f"{'─' * 60}")
        print(f"Status: {result.status}")

        if result.filter_result:
            print(
                f"Relevant: {result.filter_result.is_relevant} ({result.filter_result.confidence:.0%} confidence)"
            )

        if result.rating_result:
            print(f"Score: {result.rating_result.overall_score:.1f}/10")
            print(f"Recommendation: {result.rating_result.recommendation[:80]}...")

        if result.bid_document:
            print(f"\nExecutive Summary:")
            print(f"{result.bid_document.executive_summary[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
