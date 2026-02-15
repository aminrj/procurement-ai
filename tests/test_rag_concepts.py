"""
Test RAG concepts from the notebook with sample data.

This verifies the core RAG workflow works before production implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import numpy as np
from procurement_ai.config import Config
from procurement_ai.services.llm import LLMService


# Sample knowledge base documents
SAMPLE_KB = [
    {
        "category": "cybersecurity",
        "content": "AI-powered threat detection system with 99% accuracy, real-time monitoring, and automated response capabilities."
    },
    {
        "category": "software",
        "content": "Custom CRM development using React and FastAPI, cloud-native architecture with 99.9% uptime guarantee."
    },
    {
        "category": "ai",
        "content": "Predictive maintenance platform reducing downtime by 40%, using LSTM networks and ensemble models."
    }
]


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


class SimpleEmbeddingService:
    """Minimal embedding service for testing"""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm = LLMService(config)
    
    async def create_embedding(self, text: str) -> list[float]:
        """Create embedding using LLM service"""
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.config.LLM_BASE_URL}/embeddings",
                json={
                    "input": text,
                    "model": "text-embedding-nomic-embed-text-v1.5"  # Use embedding model
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['data'][0]['embedding']


@pytest.mark.asyncio
async def test_embedding_service():
    """Test that embedding service works"""
    config = Config()
    service = SimpleEmbeddingService(config)
    
    text = "AI cybersecurity threat detection"
    embedding = await service.create_embedding(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, (int, float)) for x in embedding)
    print(f"✅ Embedding service works! Dimension: {len(embedding)}")


@pytest.mark.asyncio
async def test_semantic_similarity():
    """Test that similar texts have similar embeddings"""
    config = Config()
    service = SimpleEmbeddingService(config)
    
    # Similar texts
    text1 = "AI cybersecurity threat detection"
    text2 = "ML-based security monitoring system"
    
    # Different text
    text3 = "Office furniture procurement"
    
    emb1 = await service.create_embedding(text1)
    emb2 = await service.create_embedding(text2)
    emb3 = await service.create_embedding(text3)
    
    sim_similar = cosine_similarity(emb1, emb2)
    sim_different = cosine_similarity(emb1, emb3)
    
    # Similar texts should have higher similarity
    assert sim_similar > sim_different, f"Expected {sim_similar} > {sim_different}"
    assert sim_similar > 0.6, f"Similar texts should have >0.6 similarity, got {sim_similar}"
    
    print(f"✅ Semantic similarity works!")
    print(f"   Similar texts: {sim_similar:.3f}")
    print(f"   Different texts: {sim_different:.3f}")


@pytest.mark.asyncio
async def test_retrieval_quality():
    """Test that retrieval finds relevant documents"""
    config = Config()
    service = SimpleEmbeddingService(config)
    
    # Create embeddings for knowledge base
    kb_embeddings = []
    for doc in SAMPLE_KB:
        emb = await service.create_embedding(doc['content'])
        kb_embeddings.append((doc, emb))
    
    # Query for cybersecurity
    query = "We need AI threat detection for government systems"
    query_emb = await service.create_embedding(query)
    
    # Calculate similarities
    similarities = []
    for doc, emb in kb_embeddings:
        sim = cosine_similarity(query_emb, emb)
        similarities.append((doc['category'], sim))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Top match should be cybersecurity
    top_category = similarities[0][0]
    top_sim = similarities[0][1]
    
    assert top_category == "cybersecurity", f"Expected 'cybersecurity', got '{top_category}'"
    assert top_sim > 0.6, f"Top match similarity should be >0.6, got {top_sim}"
    
    print(f"✅ Retrieval quality verified!")
    print(f"   Query: 'AI threat detection'")
    print(f"   Top match: {top_category} (similarity: {top_sim:.3f})")


@pytest.mark.asyncio
async def test_rag_generation_basic():
    """Test that RAG-enhanced generation includes context"""
    config = Config()
    llm = LLMService(config)
    
    # Example document
    example = """Our cybersecurity solution includes:
    - Real-time threat monitoring with 99% accuracy
    - Automated incident response
    - ISO 27001 compliance
    - 24/7 security operations center"""
    
    # Generate without RAG
    prompt_no_rag = "Generate a brief cybersecurity solution description (50 words)."
    response_no_rag = await llm.generate(prompt=prompt_no_rag, temperature=0.7, max_tokens=100)
    
    # Generate with RAG
    prompt_with_rag = f"""Here's an example of an excellent cybersecurity solution:
    
{example}

Now generate a similar cybersecurity solution description (50 words)."""
    
    response_with_rag = await llm.generate(prompt=prompt_with_rag, temperature=0.7, max_tokens=100)
    
    # Both should generate text
    assert len(response_no_rag) > 10
    assert len(response_with_rag) > 10
    
    print(f"✅ RAG generation works!")
    print(f"\n📄 Without RAG ({len(response_no_rag)} chars):\n{response_no_rag}\n")
    print(f"📄 With RAG ({len(response_with_rag)} chars):\n{response_with_rag}\n")
    
    # Note: We can't automatically verify quality, but manual inspection should show
    # the RAG version has more specific details similar to the example


if __name__ == "__main__":
    print("Running RAG concept tests...\n")
    
    async def run_all():
        await test_embedding_service()
        print()
        await test_semantic_similarity()
        print()
        await test_retrieval_quality()
        print()
        await test_rag_generation_basic()
        print("\n✅ All RAG concept tests passed!")
    
    asyncio.run(run_all())
