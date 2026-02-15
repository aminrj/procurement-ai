"""
Embedding Service for Text Vectorization

Converts text into numerical vectors (embeddings) for semantic similarity search.
Uses LM Studio's embedding endpoint (Nomic Embed).
"""

import httpx
from typing import List

from ..config import Config


class EmbeddingService:
    """
    Service for creating text embeddings
    
    Embeddings are vector representations of text that capture semantic meaning.
    Similar texts have similar vectors, enabling semantic search.
    
    Example:
        service = EmbeddingService()
        embedding = await service.create_embedding("AI security system")
        # Returns: [0.23, -0.45, ..., 0.12] (768 dimensions)
    """
    
    # LM Studio embedding model
    EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5"
    EMBEDDING_DIMENSION = 768
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.base_url = self.config.LLM_BASE_URL
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for a single text
        
        Args:
            text: Input text to embed
        
        Returns:
            List of floats (768 dimensions)
        
        Raises:
            httpx.HTTPError: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={
                    "input": text,
                    "model": self.EMBEDDING_MODEL
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['data'][0]['embedding']
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        
        Note:
            Currently processes sequentially. Could be optimized with batching.
        """
        if not texts:
            return []
        
        embeddings = []
        for text in texts:
            emb = await self.create_embedding(text)
            embeddings.append(emb)
        
        return embeddings
    
    def get_dimensions(self) -> int:
        """Get embedding vector dimensions"""
        return self.EMBEDDING_DIMENSION
