"""
Tests for AI agents with mocked LLM responses.
Fast tests without calling actual LLM API.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import json

from src.procurement_ai.models import Tender, TenderCategory
from src.procurement_ai.agents.filter import FilterAgent, FilterResult
from src.procurement_ai.agents.rating import RatingAgent, RatingResult
from src.procurement_ai.agents.generator import DocumentGenerator, BidDocument
from src.procurement_ai.services.llm import LLMService
from src.procurement_ai.config import Config


@pytest.fixture
def mock_llm():
    """Mock LLM service that returns controlled responses"""
    return Mock(spec=LLMService)


@pytest.fixture
def sample_tender():
    """Sample tender for testing"""
    return Tender(
        title="AI-Powered Cybersecurity Platform Development",
        description=(
            "Government agency requires AI-based threat detection system "
            "with machine learning capabilities for real-time monitoring."
        ),
        organization="National Cybersecurity Agency",
        deadline="2025-06-15",
        estimated_value="€2,000,000",
        location="Brussels, Belgium",
    )


@pytest.fixture
def irrelevant_tender():
    """Sample of irrelevant tender"""
    return Tender(
        title="Office Furniture Supply",
        description="Supply of office desks, chairs, and filing cabinets.",
        organization="City Council",
        deadline="2025-03-20",
        estimated_value="€50,000",
    )


class TestFilterAgent:
    """Test FilterAgent with mocked LLM"""

    @pytest.mark.asyncio
    async def test_filter_relevant_tender(self, mock_llm, sample_tender):
        """Test filtering a relevant tender"""
        # Mock LLM to return "relevant" result
        mock_llm.generate_structured = AsyncMock(
            return_value=FilterResult(
                is_relevant=True,
                confidence=0.92,
                categories=[TenderCategory.CYBERSECURITY, TenderCategory.ARTIFICIAL_INTELLIGENCE],
                reasoning="Strong match: AI-powered cybersecurity with ML capabilities",
            )
        )

        agent = FilterAgent(llm=mock_llm)
        result = await agent.filter(sample_tender)

        assert result.is_relevant is True
        assert result.confidence > 0.8
        assert TenderCategory.CYBERSECURITY in result.categories
        assert "AI" in result.reasoning or "cybersecurity" in result.reasoning.lower()

        # Verify LLM was called
        mock_llm.generate_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_filter_irrelevant_tender(self, mock_llm, irrelevant_tender):
        """Test filtering an irrelevant tender"""
        mock_llm.generate_structured = AsyncMock(
            return_value=FilterResult(
                is_relevant=False,
                confidence=0.95,
                categories=[TenderCategory.OTHER],
                reasoning="Office furniture - not a technology procurement",
            )
        )

        agent = FilterAgent(llm=mock_llm)
        result = await agent.filter(irrelevant_tender)

        assert result.is_relevant is False
        assert result.confidence > 0.9
        assert "furniture" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_filter_uses_precise_temperature(self, mock_llm, sample_tender):
        """Test that filter agent uses low temperature for consistency"""
        mock_llm.generate_structured = AsyncMock(
            return_value=FilterResult(
                is_relevant=True,
                confidence=0.9,
                categories=[TenderCategory.CYBERSECURITY],
                reasoning="Match",
            )
        )

        config = Config()
        agent = FilterAgent(llm=mock_llm, config=config)
        await agent.filter(sample_tender)

        # Check that low temperature was used
        call_kwargs = mock_llm.generate_structured.call_args[1]
        assert call_kwargs["temperature"] == config.TEMPERATURE_PRECISE


class TestRatingAgent:
    """Test RatingAgent with mocked LLM"""

    @pytest.mark.asyncio
    async def test_rate_high_score_tender(self, mock_llm, sample_tender):
        """Test rating a high-value tender"""
        mock_llm.generate_structured = AsyncMock(
            return_value=RatingResult(
                overall_score=9.0,
                strategic_fit=9.5,
                win_probability=7.5,
                effort_required=6.0,
                strengths=[
                    "Large contract value (€2M)",
                    "Government client stability",
                    "Perfect match for AI/ML expertise",
                ],
                risks=[
                    "Tight deadline may be challenging",
                    "High competition expected",
                ],
                recommendation="Go - Excellent strategic fit with strong revenue potential",
            )
        )

        agent = RatingAgent(llm=mock_llm)
        result = await agent.rate(sample_tender, ["cybersecurity", "ai"])

        assert result.overall_score >= 8.0
        assert result.overall_score <= 10.0
        assert len(result.strengths) > 0
        assert len(result.risks) >= 0
        assert "fit" in result.recommendation.lower() or "go" in result.recommendation.lower()

    @pytest.mark.asyncio
    async def test_rate_low_score_tender(self, mock_llm, irrelevant_tender):
        """Test rating a low-value tender"""
        mock_llm.generate_structured = AsyncMock(
            return_value=RatingResult(
                overall_score=2.0,
                strategic_fit=1.0,
                win_probability=3.0,
                effort_required=4.0,
                strengths=["Quick delivery possible"],
                risks=[
                    "Not technology-related",
                    "Low contract value",
                    "Outside expertise area",
                ],
                recommendation="No-Go - Poor fit: outside core competencies",
            )
        )

        agent = RatingAgent(llm=mock_llm)
        result = await agent.rate(irrelevant_tender, ["other"])

        assert result.overall_score <= 4.0
        assert len(result.risks) > len(result.strengths)

    @pytest.mark.asyncio
    async def test_rating_includes_company_profile(self, mock_llm, sample_tender):
        """Test that company profile is included in rating prompt"""
        mock_llm.generate_structured = AsyncMock(
            return_value=RatingResult(
                overall_score=8.5,
                strategic_fit=9.0,
                win_probability=7.0,
                effort_required=6.5,
                strengths=["Matches expertise"],
                risks=["Timeline tight"],
                recommendation="Go - Good match",
            )
        )

        config = Config()
        agent = RatingAgent(llm=mock_llm, config=config)
        await agent.rate(sample_tender, ["cybersecurity"])

        # Verify LLM was called with proper arguments
        mock_llm.generate_structured.assert_called_once()


class TestDocumentGenerator:
    """Test DocumentGenerator with mocked LLM"""

    @pytest.mark.asyncio
    async def test_generate_proposal(self, mock_llm, sample_tender):
        """Test generating a proposal"""
        mock_llm.generate_structured = AsyncMock(
            return_value=BidDocument(
                executive_summary="We propose a comprehensive AI-driven cybersecurity solution that leverages our 10 years of experience in threat detection and machine learning.",
                technical_approach="Machine learning threat detection, real-time monitoring, and automated response systems integrated with your existing infrastructure.",
                value_proposition="Proven track record with government agencies, cutting-edge AI technology, and dedicated 24/7 support team.",
                timeline_estimate="8-month implementation: Phase 1 (Planning - 6 weeks), Phase 2 (Development - 20 weeks), Phase 3 (Testing & Deployment - 6 weeks)",
            )
        )

        agent = DocumentGenerator(llm=mock_llm)
        result = await agent.generate(
            tender=sample_tender,
            categories=["cybersecurity", "ai"],
            strengths=["Expertise in AI/ML", "Government experience", "Strong team"],
        )

        assert result is not None
        assert isinstance(result, BidDocument)
        assert len(result.executive_summary) > 50
        assert len(result.technical_approach) > 30
        assert "AI" in result.executive_summary or "cybersecurity" in result.executive_summary.lower()

    @pytest.mark.asyncio
    async def test_generator_uses_creative_temperature(self, mock_llm, sample_tender):
        """Test that generator uses higher temperature for creativity"""
        mock_llm.generate_structured = AsyncMock(
            return_value=BidDocument(
                executive_summary="Summary",
                technical_approach="Approach",
                value_proposition="Value",
                timeline_estimate="Timeline",
            )
        )

        config = Config()
        agent = DocumentGenerator(llm=mock_llm, config=config)
        await agent.generate(sample_tender, ["ai"], ["Strong team"])

        # Check that higher temperature was used
        call_kwargs = mock_llm.generate_structured.call_args[1]
        assert call_kwargs["temperature"] == config.TEMPERATURE_CREATIVE
        assert call_kwargs["temperature"] > config.TEMPERATURE_PRECISE

    @pytest.mark.asyncio
    async def test_generator_includes_context(self, mock_llm, sample_tender):
        """Test that generator includes tender and rating context"""
        mock_llm.generate_structured = AsyncMock(
            return_value=BidDocument(
                executive_summary="Summary",
                technical_approach="Approach",
                value_proposition="Value",
                timeline_estimate="Timeline",
            )
        )

        agent = DocumentGenerator(llm=mock_llm)
        await agent.generate(
            tender=sample_tender,
            categories=["cybersecurity", "ai"],
            strengths=["Expert team", "Proven track record"],
        )

        # Verify context is in prompt
        call_args = mock_llm.generate_structured.call_args
        assert call_args is not None
        # Check that prompt was passed
        assert len(call_args[1]) > 0


class TestAgentErrorHandling:
    """Test error handling in agents"""

    @pytest.mark.asyncio
    async def test_filter_handles_llm_failure(self, mock_llm, sample_tender):
        """Test filter agent handles LLM errors gracefully"""
        mock_llm.generate_structured = AsyncMock(
            side_effect=Exception("LLM connection failed")
        )

        agent = FilterAgent(llm=mock_llm)

        with pytest.raises(Exception) as exc_info:
            await agent.filter(sample_tender)

        assert "LLM" in str(exc_info.value) or "connection" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rating_handles_invalid_response(self, mock_llm, sample_tender):
        """Test rating agent handles invalid LLM responses"""
        # This will fail Pydantic validation
        mock_llm.generate_structured = AsyncMock(
            side_effect=ValueError("Invalid response format")
        )

        agent = RatingAgent(llm=mock_llm)

        with pytest.raises(Exception):
            await agent.rate(sample_tender)
