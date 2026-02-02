"""
Tests for LLM service - basic functionality tests.
Since the LLM service is working with real service, these tests verify the interface.
"""
import pytest
from src.procurement_ai.services.llm import LLMService
from src.procurement_ai.config import Config
from pydantic import BaseModel, Field


class SampleOutput(BaseModel):
    """Sample structured output for testing"""
    message: str = Field(description="Test message")
    score: int = Field(description="Test score", ge=0, le=100)


class TestLLMService:
    """Test LLM service"""

    def test_llm_service_initialization(self):
        """Test that LLM service can be initialized"""
        config = Config()
        llm = LLMService(config)
        
        assert llm.config == config
        assert llm.base_url == config.LLM_BASE_URL

    def test_llm_service_with_custom_config(self):
        """Test LLM service with custom configuration"""
        config = Config()
        config.LLM_BASE_URL = "http://custom:8080/v1"
        
        llm = LLMService(config)
        assert llm.base_url == "http://custom:8080/v1"

    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="Requires live LLM service - run manually")
    async def test_generate_structured_with_live_service(self):
        """Test structured generation with real service (manual test)"""
        llm = LLMService()
        result = await llm.generate_structured(
            prompt="What is 2+2? Respond with: The answer is X.",
            response_model=SampleOutput,
            system_prompt="You are a helpful math assistant. The message should be 'The answer is 4' and score should be 100.",
            temperature=0.1,
        )

        assert isinstance(result, SampleOutput)
        assert "4" in result.message
        assert result.score > 0


        llm = LLMService()

        with pytest.raises(Exception) as exc_info:
            await llm.generate_structured(
                prompt="Test",
                response_model=SampleOutput,
                system_prompt="Test",
                max_retries=2,
            )

        assert "Persistent error" in str(exc_info.value)
        assert mock_client.post.call_count == 2

    def test_clean_json_removes_markdown(self):
        """Test JSON cleaning removes markdown code fences"""
        llm = LLMService()

        # Test with markdown code fence
        dirty = '```json\n{"message": "test", "score": 50}\n```'
        clean = llm._clean_json(dirty)
        assert clean == '{"message": "test", "score": 50}'

        # Test without markdown
        plain = '{"message": "test", "score": 50}'
        clean = llm._clean_json(plain)
        assert clean == plain

    def test_build_structured_prompt_includes_schema(self):
        """Test that structured prompt includes JSON schema"""
        llm = LLMService()

        prompt = llm._build_structured_prompt(
            "What is the score?",
            SampleOutput
        )

        assert "JSON" in prompt
        assert "schema" in prompt.lower() or "format" in prompt.lower()
        assert "What is the score?" in prompt


class TestLLMServiceConfiguration:
    """Test LLM service configuration"""

    def test_uses_config_values(self):
        """Test that service uses config values"""
        config = Config()
        llm = LLMService(config=config)

        assert llm.base_url == config.LLM_BASE_URL
        assert llm.model == config.LLM_MODEL

    def test_default_config(self):
        """Test service works with default config"""
        llm = LLMService()

        assert llm.base_url is not None
        assert llm.model is not None
