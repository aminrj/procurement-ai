"""Simple chain orchestration for procurement workflow"""

from datetime import datetime

from ..models import Tender, ProcessedTender
from ..services.llm import LLMService
from ..agents.filter import FilterAgent
from ..agents.rating import RatingAgent
from ..agents.generator import DocumentGenerator
from ..config import Config


class ProcurementOrchestrator:
    """
    Main orchestration logic

    Concept: Sequential agent execution with conditional logic
    This is a simple linear workflow - later we'll compare with LangGraph
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.llm = LLMService(self.config)
        self.filter_agent = FilterAgent(self.llm, self.config)
        self.rating_agent = RatingAgent(self.llm, self.config)
        self.doc_generator = DocumentGenerator(self.llm, self.config)

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
                or result.filter_result.confidence < self.config.MIN_CONFIDENCE
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
            if result.rating_result.overall_score < self.config.MIN_SCORE_FOR_DOCUMENT:
                result.status = "rated_low"
                print(f"\n  → Skipping document generation (score < {self.config.MIN_SCORE_FOR_DOCUMENT})")
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
