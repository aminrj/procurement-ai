"""
Tests for orchestration (simple_chain).
"""
import pytest
from unittest.mock import AsyncMock, Mock

from src.procurement_ai.models import Tender, TenderCategory
from src.procurement_ai.orchestration.simple_chain import ProcurementOrchestrator
from src.procurement_ai.agents.filter import FilterResult
from src.procurement_ai.agents.rating import RatingResult
from src.procurement_ai.agents.generator import BidDocument
from src.procurement_ai.config import Config


@pytest.fixture
def sample_tender():
    """Sample tender for testing"""
    return Tender(
        title="AI Development Project",
        description="Need AI expertise for machine learning project",
        organization="Tech Company",
        deadline="2025-06-01",
        estimated_value="€500,000",
    )


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing orchestrator"""
    from unittest.mock import Mock, AsyncMock
    from src.procurement_ai.services.llm import LLMService
    
    mock_llm = Mock(spec=LLMService)
    mock_llm.generate_structured = AsyncMock()
    return mock_llm


class TestProcurementOrchestrator:
    """Test ProcurementOrchestrator orchestration"""

    @pytest.mark.asyncio
    async def test_process_relevant_tender(self, sample_tender):
        """Test processing a relevant tender through full pipeline"""
        from unittest.mock import patch, AsyncMock
        
        # Mock all three agent methods
        mock_filter_result = FilterResult(
            is_relevant=True,
            confidence=0.9,
            categories=[TenderCategory.ARTIFICIAL_INTELLIGENCE],
            reasoning="AI project match",
        )
        
        mock_rating_result = RatingResult(
            overall_score=8.5,
            strategic_fit=9.0,
            win_probability=7.5,
            effort_required=6.0,
            strengths=["Large contract", "AI focus"],
            risks=["Timeline tight"],
            recommendation="Go - Good fit",
        )
        
        mock_doc_result = BidDocument(
            executive_summary="We can deliver this solution",
            technical_approach="Using AI/ML technologies",
            value_proposition="Expert team with proven track record",
            timeline_estimate="6 months",
        )
        
        with patch('src.procurement_ai.orchestration.simple_chain.FilterAgent') as MockFilter, \
             patch('src.procurement_ai.orchestration.simple_chain.RatingAgent') as MockRating, \
             patch('src.procurement_ai.orchestration.simple_chain.DocumentGenerator') as MockGenerator:
            
            # Configure mocks
            mock_filter_instance = MockFilter.return_value
            mock_filter_instance.filter = AsyncMock(return_value=mock_filter_result)
            
            mock_rating_instance = MockRating.return_value
            mock_rating_instance.rate = AsyncMock(return_value=mock_rating_result)
            
            mock_doc_instance = MockGenerator.return_value
            mock_doc_instance.generate = AsyncMock(return_value=mock_doc_result)
            
            # Create orchestrator and process
            orchestrator = ProcurementOrchestrator()
            result = await orchestrator.process_tender(sample_tender)
            
            # Verify result
            assert result.status == "complete"
            assert result.filter_result.is_relevant is True
            assert result.rating_result.overall_score == 8.5
            assert result.bid_document is not None
            
            # Verify all agents were called
            mock_filter_instance.filter.assert_called_once()
            mock_rating_instance.rate.assert_called_once()
            mock_doc_instance.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_irrelevant_tender_stops_early(self, sample_tender):
        """Test that irrelevant tenders stop at filter stage"""
        from unittest.mock import patch, AsyncMock
        
        mock_filter_result = FilterResult(
            is_relevant=False,
            confidence=0.95,
            categories=[TenderCategory.OTHER],
            reasoning="Not technology-related",
        )
        
        with patch('src.procurement_ai.orchestration.simple_chain.FilterAgent') as MockFilter, \
             patch('src.procurement_ai.orchestration.simple_chain.RatingAgent') as MockRating, \
             patch('src.procurement_ai.orchestration.simple_chain.DocumentGenerator') as MockGenerator:
            
            mock_filter_instance = MockFilter.return_value
            mock_filter_instance.filter = AsyncMock(return_value=mock_filter_result)
            
            mock_rating_instance = MockRating.return_value
            mock_rating_instance.rate = AsyncMock()
            
            mock_doc_instance = MockGenerator.return_value
            mock_doc_instance.generate = AsyncMock()
            
            orchestrator = ProcurementOrchestrator()
            result = await orchestrator.process_tender(sample_tender)
            
            # Verify pipeline stopped after filter
            assert result.status == "filtered_out"
            assert result.filter_result.is_relevant is False
            assert result.rating_result is None
            assert result.bid_document is None
            
            # Verify only filter was called
            mock_filter_instance.filter.assert_called_once()
            mock_rating_instance.rate.assert_not_called()
            mock_doc_instance.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_low_score_tender_skips_proposal(self, sample_tender):
        """Test that low-scored tenders don't generate proposals"""
        from unittest.mock import patch, AsyncMock
        
        mock_filter_result = FilterResult(
            is_relevant=True,
            confidence=0.8,
            categories=[TenderCategory.SOFTWARE_DEVELOPMENT],
            reasoning="Software project",
        )
        
        mock_rating_result = RatingResult(
            overall_score=4.0,
            strategic_fit=5.0,
            win_probability=3.0,
            effort_required=7.0,
            strengths=["Some revenue"],
            risks=["Wrong domain", "Low value", "High risk"],
            recommendation="No-Go - Poor fit",
        )
        
        with patch('src.procurement_ai.orchestration.simple_chain.FilterAgent') as MockFilter, \
             patch('src.procurement_ai.orchestration.simple_chain.RatingAgent') as MockRating, \
             patch('src.procurement_ai.orchestration.simple_chain.DocumentGenerator') as MockGenerator:
            
            mock_filter_instance = MockFilter.return_value
            mock_filter_instance.filter = AsyncMock(return_value=mock_filter_result)
            
            mock_rating_instance = MockRating.return_value
            mock_rating_instance.rate = AsyncMock(return_value=mock_rating_result)
            
            mock_doc_instance = MockGenerator.return_value
            mock_doc_instance.generate = AsyncMock()
            
            config = Config()
            orchestrator = ProcurementOrchestrator(config=config)
            result = await orchestrator.process_tender(sample_tender)
            
            # Verify pipeline stopped after rating
            assert result.status == "rated_low"
            assert result.filter_result.is_relevant is True
            assert result.rating_result.overall_score == 4.0
            assert result.bid_document is None
            
            # Verify generator was not called
            mock_filter_instance.filter.assert_called_once()
            mock_rating_instance.rate.assert_called_once()
            mock_doc_instance.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_handles_filter_error(self, sample_tender):
        """Test error handling in filter stage"""
        from unittest.mock import patch, AsyncMock
        
        with patch('src.procurement_ai.orchestration.simple_chain.FilterAgent') as MockFilter:
            mock_filter_instance = MockFilter.return_value
            mock_filter_instance.filter = AsyncMock(
                side_effect=Exception("LLM connection failed")
            )
            
            orchestrator = ProcurementOrchestrator()
            result = await orchestrator.process_tender(sample_tender)
            
            # Error should be caught and recorded in status
            assert "error" in result.status.lower()
            assert "LLM" in result.status or "failed" in result.status

    @pytest.mark.asyncio
    async def test_process_respects_score_threshold(self, sample_tender):
        """Test that score threshold is respected"""
        from unittest.mock import patch, AsyncMock
        
        mock_filter_result = FilterResult(
            is_relevant=True,
            confidence=0.9,
            categories=[TenderCategory.CYBERSECURITY],
            reasoning="Match",
        )
        
        # Score exactly at threshold (default 7.0)
        mock_rating_result = RatingResult(
            overall_score=7.0,
            strategic_fit=7.0,
            win_probability=7.0,
            effort_required=7.0,
            strengths=["Meets criteria"],
            risks=[],
            recommendation="Go - Acceptable",
        )
        
        mock_doc_result = BidDocument(
            executive_summary="Proposal content",
            technical_approach="Our approach",
            value_proposition="Our value",
            timeline_estimate="6 months",
        )
        
        with patch('src.procurement_ai.orchestration.simple_chain.FilterAgent') as MockFilter, \
             patch('src.procurement_ai.orchestration.simple_chain.RatingAgent') as MockRating, \
             patch('src.procurement_ai.orchestration.simple_chain.DocumentGenerator') as MockGenerator:
            
            mock_filter_instance = MockFilter.return_value
            mock_filter_instance.filter = AsyncMock(return_value=mock_filter_result)
            
            mock_rating_instance = MockRating.return_value
            mock_rating_instance.rate = AsyncMock(return_value=mock_rating_result)
            
            mock_doc_instance = MockGenerator.return_value
            mock_doc_instance.generate = AsyncMock(return_value=mock_doc_result)
            
            orchestrator = ProcurementOrchestrator()
            result = await orchestrator.process_tender(sample_tender)
            
            # Score at threshold should generate proposal
            assert result.status == "complete"
            assert result.bid_document is not None
            mock_doc_instance.generate.assert_called_once()
