# experiments/01_prompt_variations.py
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procurement_mvp import *

# Version A: Vague prompt
FILTER_PROMPT_V1 = "Is this tender relevant for a tech company? {title}"

# Version B: Specific criteria (current version)
FILTER_PROMPT_V2 = """Analyze this tender:
TITLE: {title}
DESCRIPTION: {description}

CRITERIA: Relevant if cybersecurity, AI, or software development.
NOT relevant if hardware, construction, or non-technical."""

# Version C: Examples-based (few-shot)
FILTER_PROMPT_V3 = """Analyze this tender using these examples:

RELEVANT EXAMPLES:
- "AI threat detection system" → RELEVANT (AI + Cybersecurity)
- "Custom CRM software" → RELEVANT (Software Development)

NOT RELEVANT EXAMPLES:
- "Office furniture supply" → NOT RELEVANT (Non-technical)
- "Building construction" → NOT RELEVANT (Physical infrastructure)

NOW ANALYZE:
TITLE: {title}
DESCRIPTION: {description}"""

async def test_prompt_variations():
    """Test different prompt styles on same tender"""
    
    print("Starting prompt variations test...")
    
    try:
        tender = SAMPLE_TENDERS[0]  # AI Cybersecurity tender
        llm = LLMService()
        
        prompts = {
            "V1_Vague": FILTER_PROMPT_V1,
            "V2_Criteria": FILTER_PROMPT_V2,
            "V3_Examples": FILTER_PROMPT_V3,
        }
        
        results = {}
        
        for version, template in prompts.items():
            print(f"\nTesting {version}...")
            
            try:
                # Manually call LLM with this prompt
                prompt = template.format(
                    title=tender.title,
                    description=tender.description
                )
                
                result = await llm.generate_structured(
                    prompt=prompt,
                    response_model=FilterResult,
                    system_prompt="You are a procurement analyst.",
                    temperature=0.1
                )
                
                results[version] = result
                print(f"  ✓ Relevant: {result.is_relevant}")
                print(f"  ✓ Confidence: {result.confidence:.2f}")
                print(f"  ✓ Reasoning: {result.reasoning[:100]}...")
                
            except Exception as e:
                print(f"  ✗ Error in {version}: {e}")
                results[version] = None
        
        # Compare
        print(f"\n{'='*60}")
        print("COMPARISON")
        print(f"{'='*60}")
        for version, result in results.items():
            if result:
                print(f"{version:15} | Relevant: {str(result.is_relevant):5} | Confidence: {result.confidence:.2f}")
            else:
                print(f"{version:15} | ERROR")
                
    except Exception as e:
        print(f"Overall error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prompt_variations())