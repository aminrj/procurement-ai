"""Debug script for get_context issue"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from procurement_ai.rag import KnowledgeBase

async def debug_get_context():
    kb = KnowledgeBase(collection_name="debug_test")
    
    # Add example
    doc_id = await kb.add_example(
        content="AI cybersecurity solution with 99% accuracy",
        category="cybersecurity",
        title="Security Example"
    )
    
    print(f"Added document: {doc_id}")
    print(f"KB count: {kb.count()}")
    
    # Try searfing with NO threshold directly on vector store
    raw_results = await kb.vector_store.search("AI security system", k=1)
    print(f"\nRaw vector store results:")
    if raw_results['distances'] and raw_results['distances'][0]:
        for dist, doc, meta in zip(raw_results['distances'][0], raw_results['documents'][0], raw_results['metadatas'][0]):
            similarity = max(0, 1 - dist)
            print(f"  - Distance: {dist:.3f}, Similarity: {similarity:.3f}")
            print(f"  - Content: {doc[:50]}...")
    
    # Try searching with retriever (no threshold)
    search_results = await kb.search("AI security system", k=1, min_similarity=0.0)
    print(f"\nRetriever search results count: {len(search_results)}")
    if search_results:
        for r in search_results:
            print(f"  - Similarity: {r.similarity:.3f}")
            print(f"  - Content: {r.content[:50]}...")
    
    # Try get_context
    context = await kb.get_context("AI security system", k=1, min_similarity=0.5)
    print(f"\nContext length: {len(context)}")
    print(f"Context: '{context}'")

if __name__ == "__main__":
    asyncio.run(debug_get_context())
