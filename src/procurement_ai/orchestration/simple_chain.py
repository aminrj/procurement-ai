"""Simple chain orchestration for procurement workflow"""

from datetime import datetime
import logging

from ..models import Tender, ProcessedTender
from ..services.llm import LLMService
from ..agents.filter import FilterAgent
from ..agents.rating import RatingAgent
from ..agents.generator import DocumentGenerator
from ..config import Config

logger = logging.getLogger(__name__)


class ProcurementOrchestrator:
    """
    Main orchestration logic

    Concept: Sequential agent execution with conditional logic
    This is a simple linear workflow - later we'll compare with LangGraph
    """

    def __init__(self, config: Config = None, llm_service: LLMService = None):
        self.config = config or Config()
        self.llm = llm_service or LLMService(self.config)
        self.filter_agent = FilterAgent(self.llm, self.config)
        self.rating_agent = RatingAgent(self.llm, self.config)
        self.doc_generator = DocumentGenerator(self.llm, self.config)

    async def process_tender(self, tender: Tender) -> ProcessedTender:
        """Process a single tender through the full pipeline"""

        start_time = datetime.now()
        result = ProcessedTender(tender=tender)

        try:
            # STEP 1: Filter for relevance
            result.filter_result = await self.filter_agent.filter(tender)

            # If not relevant, stop here
            if (
                not result.filter_result.is_relevant
                or result.filter_result.confidence < self.config.MIN_CONFIDENCE
            ):
                result.status = "filtered_out"
                return result

            # STEP 2: Rate the opportunity

            categories = [c.value for c in result.filter_result.categories]
            result.rating_result = await self.rating_agent.rate(tender, categories)

            # If score is low, don't generate documents
            if result.rating_result.overall_score < self.config.MIN_SCORE_FOR_DOCUMENT:
                result.status = "rated_low"
                return result

            # STEP 3: Generate bid document

            result.bid_document = await self.doc_generator.generate(
                tender, categories, result.rating_result.strengths
            )

            result.status = "complete"

        except Exception as e:
            result.status = "error"
            result.error = str(e)
            logger.exception("Tender processing failed")

        finally:
            result.processing_time = (datetime.now() - start_time).total_seconds()
            logger.info("Tender processing time: %.2fs", result.processing_time)

        return result
