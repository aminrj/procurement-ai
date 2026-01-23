# experiments/02_temperature_impact.py
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procurement_mvp import *

async def test_temperature():
    """See how temperature affects document generation"""
    
    print("Starting temperature impact test...")
    
    try:
        tender = SAMPLE_TENDERS[0]
        llm = LLMService()
        doc_gen = DocumentGenerator(llm)
        
        temperatures = [0.1, 0.4, 0.7, 1.0]  # Four temperature points
        
        for temp in temperatures:
            print(f"\n{'='*60}")
            print(f"TEMPERATURE: {temp}")
            print(f"{'='*60}")
            
            try:
                # Override temperature
                Config.TEMPERATURE_CREATIVE = temp
                
                doc = await doc_gen.generate(
                    tender,
                    ["cybersecurity", "ai"],
                    ["Strong AI expertise", "Government experience", "Fast delivery"]
                )
                
                print(f"\nExecutive Summary:")
                print(doc.executive_summary[:300])
                print(f"\n[Length: {len(doc.executive_summary)} chars]")
                print(f"Technical Approach Length: {len(doc.technical_approach)} chars")
                print(f"Value Proposition Length: {len(doc.value_proposition)} chars")
                
                # Count unique words as creativity metric
                words = doc.executive_summary.lower().split()
                unique_words = len(set(words))
                print(f"Unique words: {unique_words} / {len(words)} = {unique_words/len(words):.2f} ratio")
                
            except Exception as e:
                print(f"Error at temperature {temp}: {e}")
                
    except Exception as e:
        print(f"Overall error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_temperature())