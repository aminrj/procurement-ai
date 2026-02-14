"""
Main evaluator for running comprehensive system evaluations

This module orchestrates the evaluation of all agents against the test dataset,
collecting metrics and generating detailed reports.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import asyncio
import logging

from ..models import Tender
from ..agents.filter import FilterAgent
from ..agents.rating import RatingAgent
from ..config import Config
from ..services.llm import LLMService

from .metrics import (
    FilterMetrics,
    CategoryMetrics,
    RatingMetrics,
    DocumentMetrics,
    ConfidenceCalibration,
)

logger = logging.getLogger(__name__)


@dataclass
class TestCaseResult:
    """Result for a single test case"""
    # Required fields (no defaults)
    test_id: str
    test_category: str
    predicted_relevant: bool
    predicted_confidence: float
    predicted_categories: List[str]
    expected_relevant: bool
    
    # Optional fields (with defaults)
    predicted_score: Optional[float] = None
    predicted_recommendation: Optional[str] = None
    expected_categories: List[str] = field(default_factory=list)
    expected_score_range: Optional[tuple] = None
    is_correct: bool = False
    categories_correct: bool = False
    score_in_range: Optional[bool] = None
    processing_time: float = 0.0
    error: Optional[str] = None
    notes: str = ""


@dataclass
class EvaluationResult:
    """Complete evaluation results"""
    
    # Metadata
    timestamp: str
    config: Dict[str, Any]
    test_cases_count: int
    
    # Metrics
    filter_metrics: FilterMetrics
    category_metrics: CategoryMetrics
    rating_metrics: RatingMetrics
    confidence_calibration: ConfidenceCalibration
    
    # Individual results
    test_results: List[TestCaseResult] = field(default_factory=list)
    
    # Summary statistics
    total_processing_time: float = 0.0
    errors_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp,
            "config": self.config,
            "summary": {
                "test_cases": self.test_cases_count,
                "processing_time": round(self.total_processing_time, 2),
                "errors": self.errors_count,
            },
            "metrics": {
                "filter": self.filter_metrics.to_dict(),
                "categories": self.category_metrics.to_dict(),
                "rating": self.rating_metrics.to_dict(),
                "calibration": self.confidence_calibration.to_dict(),
            },
            "test_results": [asdict(r) for r in self.test_results],
        }


class Evaluator:
    """
    Main evaluator for AI agents
    
    Runs test cases through the agent pipeline and collects comprehensive metrics.
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        llm_service: Optional[LLMService] = None
    ):
        self.config = config or Config()
        self.llm = llm_service or LLMService(self.config)
        
        # Initialize agents
        self.filter_agent = FilterAgent(self.llm, self.config)
        self.rating_agent = RatingAgent(self.llm, self.config)
    
    async def evaluate_test_case(
        self,
        test_case: Any,  # EvaluationTestCase from dataset
    ) -> TestCaseResult:
        """Evaluate a single test case"""
        
        start_time = datetime.now()
        
        try:
            # Create tender from test case
            tender_dict = test_case.to_tender_dict()
            tender = Tender(**tender_dict)
            
            # Run filter agent
            filter_result = await self.filter_agent.filter(tender)
            
            # Determine correctness
            is_correct = (
                filter_result.is_relevant == test_case.expected_relevance
            )
            
            # Check categories
            predicted_cats = [c.value for c in filter_result.categories]
            categories_correct = set(predicted_cats) == set(test_case.expected_categories)
            
            # Run rating agent if relevant
            predicted_score = None
            predicted_recommendation = None
            score_in_range = None
            
            if filter_result.is_relevant and test_case.expected_score_range:
                try:
                    rating_result = await self.rating_agent.rate(
                        tender,
                        predicted_cats
                    )
                    predicted_score = rating_result.overall_score
                    predicted_recommendation = rating_result.recommendation
                    
                    # Check if score is in expected range
                    score_in_range = (
                        test_case.expected_score_range[0] <= predicted_score <= 
                        test_case.expected_score_range[1]
                    )
                except Exception as e:
                    logger.error(f"Rating failed for {test_case.tender_id}: {e}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return TestCaseResult(
                test_id=test_case.tender_id,
                test_category=test_case.category.value,
                predicted_relevant=filter_result.is_relevant,
                predicted_confidence=filter_result.confidence,
                predicted_categories=predicted_cats,
                predicted_score=predicted_score,
                predicted_recommendation=predicted_recommendation,
                expected_relevant=test_case.expected_relevance,
                expected_categories=test_case.expected_categories,
                expected_score_range=test_case.expected_score_range,
                is_correct=is_correct,
                categories_correct=categories_correct,
                score_in_range=score_in_range,
                processing_time=processing_time,
                notes=test_case.notes,
            )
        
        except Exception as e:
            logger.error(f"Evaluation failed for {test_case.tender_id}: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return TestCaseResult(
                test_id=test_case.tender_id,
                test_category=test_case.category.value,
                predicted_relevant=False,
                predicted_confidence=0.0,
                predicted_categories=[],
                expected_relevant=test_case.expected_relevance,
                expected_categories=test_case.expected_categories,
                processing_time=processing_time,
                error=str(e),
            )
    
    async def evaluate_dataset(
        self,
        test_cases: List[Any],
        max_concurrent: int = 3
    ) -> EvaluationResult:
        """
        Evaluate entire dataset
        
        Args:
            test_cases: List of EvaluationTestCase objects
            max_concurrent: Maximum concurrent evaluations
        
        Returns:
            EvaluationResult with comprehensive metrics
        """
        
        logger.info(f"Starting evaluation of {len(test_cases)} test cases")
        start_time = datetime.now()
        
        # Initialize metrics
        filter_metrics = FilterMetrics()
        category_metrics = CategoryMetrics()
        rating_metrics = RatingMetrics()
        calibration = ConfidenceCalibration()
        
        # Run evaluations with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def evaluate_with_semaphore(tc):
            async with semaphore:
                return await self.evaluate_test_case(tc)
        
        results = await asyncio.gather(*[
            evaluate_with_semaphore(tc) for tc in test_cases
        ])
        
        # Aggregate metrics
        errors_count = 0
        
        for result in results:
            if result.error:
                errors_count += 1
                continue
            
            # Filter metrics
            filter_metrics.add_prediction(
                predicted=result.predicted_relevant,
                expected=result.expected_relevant,
                confidence=result.predicted_confidence
            )
            
            # Confidence calibration
            calibration.add_prediction(
                confidence=result.predicted_confidence,
                is_correct=result.is_correct
            )
            
            # Category metrics (only for relevant tenders)
            if result.expected_relevant:
                category_metrics.add_prediction(
                    predicted=result.predicted_categories,
                    expected=result.expected_categories
                )
            
            # Rating metrics
            if result.predicted_score and result.expected_score_range:
                rating_metrics.add_prediction(
                    predicted_score=result.predicted_score,
                    expected_range=result.expected_score_range
                )
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Create evaluation result
        evaluation_result = EvaluationResult(
            timestamp=datetime.now().isoformat(),
            config={
                "llm_model": self.config.LLM_MODEL,
                "temperature_precise": self.config.TEMPERATURE_PRECISE,
                "min_confidence": self.config.MIN_CONFIDENCE,
            },
            test_cases_count=len(test_cases),
            filter_metrics=filter_metrics,
            category_metrics=category_metrics,
            rating_metrics=rating_metrics,
            confidence_calibration=calibration,
            test_results=results,
            total_processing_time=total_time,
            errors_count=errors_count,
        )
        
        logger.info(f"Evaluation complete in {total_time:.2f}s")
        logger.info(f"Filter F1: {filter_metrics.f1_score:.3f}")
        logger.info(f"Category Accuracy: {category_metrics.accuracy:.3f}")
        logger.info(f"Rating MAE: {rating_metrics.mae:.3f}")
        
        return evaluation_result
    
    async def quick_eval(
        self,
        test_cases: List[Any],
        categories_only: bool = False
    ) -> Dict[str, float]:
        """
        Quick evaluation returning only key metrics
        
        Useful for rapid iteration and A/B testing.
        """
        
        result = await self.evaluate_dataset(test_cases, max_concurrent=5)
        
        quick_metrics = {
            "f1_score": result.filter_metrics.f1_score,
            "precision": result.filter_metrics.precision,
            "recall": result.filter_metrics.recall,
            "accuracy": result.filter_metrics.accuracy,
        }
        
        if not categories_only:
            quick_metrics.update({
                "category_accuracy": result.category_metrics.accuracy,
                "rating_mae": result.rating_metrics.mae,
                "calibration_error": result.confidence_calibration.expected_calibration_error,
                "processing_time": result.total_processing_time,
            })
        
        return quick_metrics
