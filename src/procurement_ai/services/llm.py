"""LLM Service for structured output generation"""

import asyncio
import httpx
import json
from typing import Type, TypeVar
from pydantic import BaseModel

from ..config import Config

T = TypeVar('T', bound=BaseModel)


class LLMService:
    """
    Simple LLM service for LM Studio

    Key Concepts Demonstrated:
    - OpenAI-compatible API calls
    - Structured output with JSON schema
    - Error handling and retries
    - Temperature control
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.base_url = self.config.LLM_BASE_URL
        self.model = self.config.LLM_MODEL

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str,
        temperature: float = 0.1,
        max_retries: int = None,
    ) -> T:
        """
        Generate structured output matching Pydantic model

        This is the CORE pattern for LLM engineering:
        1. Define output schema with Pydantic
        2. Inject schema into prompt
        3. Parse and validate response
        """
        max_retries = max_retries or self.config.MAX_RETRIES

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
                
                # Additional validation - check if it looks like JSON
                if not cleaned.startswith('{') or not cleaned.endswith('}'):
                    raise ValueError(f"Response doesn't look like JSON: {cleaned[:100]}...")
                
                # Try to parse first to give better error messages
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON structure: {e}. Content: {cleaned[:200]}...")
                
                return response_model.model_validate(parsed)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed after {max_retries} attempts: {e}")
                await asyncio.sleep(2)  # Longer pause for retries

    def _build_structured_prompt(self, prompt: str, model: Type[BaseModel]) -> str:
        """Add schema to prompt for better structured output"""
        
        # Create a proper example with correct field types and values
        example_fields = {}
        for field_name, field_info in model.model_fields.items():
            if field_name == "confidence":
                example_fields[field_name] = 0.85
            elif field_name in ["overall_score", "strategic_fit", "win_probability", "effort_required"]:
                example_fields[field_name] = 8.5
            elif field_name == "is_relevant":
                example_fields[field_name] = True
            elif field_name == "categories":
                # Use actual enum values
                if hasattr(model, "model_fields") and "categories" in model.model_fields:
                    example_fields[field_name] = ["cybersecurity", "ai", "software"]
                else:
                    example_fields[field_name] = ["example_category"]
            elif field_name in ["strengths", "risks"]:
                example_fields[field_name] = ["Example strength 1", "Example strength 2", "Example strength 3"]
            elif "reasoning" in field_name or "recommendation" in field_name:
                example_fields[field_name] = "Example reasoning or recommendation text here"
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
        start_idx = cleaned.find('{')
        if start_idx == -1:
            return cleaned
            
        brace_count = 0
        end_idx = -1
        
        for i, char in enumerate(cleaned[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx != -1:
            return cleaned[start_idx:end_idx + 1]
        
        return cleaned

    async def _call_api(self, messages: list, temperature: float) -> str:
        """Make API call to LM Studio"""
        async with httpx.AsyncClient(timeout=self.config.API_TIMEOUT) as client:
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
