"""Tests for LLM service behavior without live API calls."""

from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, Field

from procurement_ai.config import Config
from procurement_ai.services.llm import LLMService


class SampleOutput(BaseModel):
    message: str = Field(description="Test message")
    score: int = Field(description="Test score", ge=0, le=100)


class TestLLMService:
    def test_llm_service_initialization(self):
        config = Config()
        llm = LLMService(config)

        assert llm.config == config
        assert llm.base_url == config.LLM_BASE_URL

    def test_llm_service_with_custom_config(self):
        config = Config()
        config.LLM_BASE_URL = "http://custom:8080/v1"

        llm = LLMService(config)
        assert llm.base_url == "http://custom:8080/v1"

    @pytest.mark.asyncio
    async def test_generate_structured_success(self):
        llm = LLMService()
        llm._call_api = AsyncMock(return_value='{"message": "ok", "score": 80}')

        result = await llm.generate_structured(
            prompt="Test prompt",
            response_model=SampleOutput,
            system_prompt="Test system",
            max_retries=1,
        )

        assert isinstance(result, SampleOutput)
        assert result.message == "ok"
        assert result.score == 80

    @pytest.mark.asyncio
    async def test_generate_structured_retries(self):
        llm = LLMService()
        llm._call_api = AsyncMock(side_effect=[Exception("temporary"), '{"message": "ok", "score": 90}'])

        result = await llm.generate_structured(
            prompt="Test prompt",
            response_model=SampleOutput,
            system_prompt="Test system",
            max_retries=2,
        )

        assert result.score == 90
        assert llm._call_api.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_structured_fails_after_max_retries(self):
        llm = LLMService()
        llm._call_api = AsyncMock(side_effect=Exception("Persistent error"))

        with pytest.raises(Exception) as exc_info:
            await llm.generate_structured(
                prompt="Test",
                response_model=SampleOutput,
                system_prompt="Test",
                max_retries=2,
            )

        assert "Failed after 2 attempts" in str(exc_info.value)

    def test_clean_json_removes_markdown(self):
        llm = LLMService()

        dirty = '```json\n{"message": "test", "score": 50}\n```'
        clean = llm._clean_json(dirty)
        assert clean == '{"message": "test", "score": 50}'

        plain = '{"message": "test", "score": 50}'
        assert llm._clean_json(plain) == plain

    def test_build_structured_prompt_includes_format_examples(self):
        llm = LLMService()
        prompt = llm._build_structured_prompt("What is the score?", SampleOutput)

        assert "JSON" in prompt
        assert "format" in prompt.lower()
        assert "What is the score?" in prompt


class TestLLMServiceConfiguration:
    def test_uses_config_values(self):
        config = Config()
        llm = LLMService(config=config)

        assert llm.base_url == config.LLM_BASE_URL
        assert llm.model == config.LLM_MODEL

    def test_default_config(self):
        llm = LLMService()

        assert llm.base_url is not None
        assert llm.model is not None
