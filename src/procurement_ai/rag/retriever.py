"""
Document Retriever for RAG

Retrieves relevant documents and formats them for prompt augmentation.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict

from .vector_store import VectorStore


@dataclass
class RetrievalResult:
    """Single retrieval result"""
    content: str
    metadata: Dict
    similarity: float  # 0-1, higher is more similar
    
    def __str__(self):
        """Format for prompt inclusion"""
        title = self.metadata.get('title', 'Document')
        category = self.metadata.get('category', 'general')
        return f"[{category.upper()}] {title}\n\n{self.content}"


class DocumentRetriever:
    """
    Retrieves relevant documents for RAG
    
    Handles querying the vector store and formatting results for LLM consumption.
    
    Example:
        retriever = DocumentRetriever(vector_store)
        
        # Retrieve for prompt augmentation
        results = await retriever.retrieve(
            "AI cybersecurity solution",
            k=2,
            min_similarity=0.6
        )
        
        # Format for prompt
        context = retriever.format_for_prompt(results)
    """
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize retriever
        
        Args:
            vector_store: VectorStore instance
        """
        self.vector_store = vector_store
    
    async def retrieve(
        self,
        query: str,
        k: int = 3,
        min_similarity: float = 0.5,
        filter_metadata: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents
        
        Args:
            query: Search query (tender description, requirements, etc.)
            k: Maximum number of results
            min_similarity: Minimum similarity threshold (0-1)
            filter_metadata: Optional metadata filter
        
        Returns:
            List of RetrievalResult objects, sorted by similarity
        """
        # Search vector store
        raw_results = await self.vector_store.search(
            query=query,
            k=k,
            filter_metadata=filter_metadata
        )
        
        # Convert to RetrievalResult objects
        results = []
        
        if not raw_results['ids'] or not raw_results['ids'][0]:
            return results
        
        for doc_id, content, metadata, distance in zip(
            raw_results['ids'][0],
            raw_results['documents'][0],
            raw_results['metadatas'][0],
            raw_results['distances'][0]
        ):
            # Convert distance to similarity (ChromaDB returns L2 distance)
            # For normalized vectors: L2_distance = sqrt(2 * (1 - cosine_sim))
            # Therefore: cosine_sim = 1 - (L2_distance^2 / 2)
            similarity = max(0, min(1, 1 - (distance ** 2 / 2)))
            
            if similarity >= min_similarity:
                results.append(RetrievalResult(
                    content=content,
                    metadata=metadata,
                    similarity=similarity
                ))
        
        return results
    
    def format_for_prompt(
        self,
        results: List[RetrievalResult],
        include_metadata: bool = True
    ) -> str:
        """
        Format retrieval results for LLM prompt
        
        Args:
            results: List of retrieval results
            include_metadata: Whether to include metadata in formatted output
        
        Returns:
            Formatted string ready for prompt inclusion
        """
        if not results:
            return ""
        
        sections = []
        for i, result in enumerate(results, 1):
            if include_metadata:
                header = f"### Example {i}"
                if 'title' in result.metadata:
                    header += f": {result.metadata['title']}"
                if 'category' in result.metadata:
                    header += f" [{result.metadata['category']}]"
                
                sections.append(f"{header}\n\n{result.content}")
            else:
                sections.append(result.content)
        
        return "\n\n---\n\n".join(sections)
    
    async def retrieve_and_format(
        self,
        query: str,
        k: int = 2,
        min_similarity: float = 0.6,
        filter_metadata: Optional[Dict] = None
    ) -> str:
        """
        Convenience method: retrieve and format in one call
        
        Args:
            query: Search query
            k: Number of results
            min_similarity: Minimum similarity threshold
            filter_metadata: Optional metadata filter
        
        Returns:
            Formatted context string
        """
        results = await self.retrieve(
            query, 
            k=k, 
            min_similarity=min_similarity,
            filter_metadata=filter_metadata
        )
        return self.format_for_prompt(results)
    
    def get_statistics(self, results: List[RetrievalResult]) -> Dict:
        """
        Get statistics about retrieval quality
        
        Args:
            results: List of retrieval results
        
        Returns:
            Dictionary with statistics
        """
        if not results:
            return {
                "count": 0,
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "min_similarity": 0.0
            }
        
        similarities = [r.similarity for r in results]
        
        return {
            "count": len(results),
            "avg_similarity": sum(similarities) / len(similarities),
            "max_similarity": max(similarities),
            "min_similarity": min(similarities),
            "categories": list(set(r.metadata.get('category', 'unknown') for r in results))
        }
