"""
Knowledge Base Manager

High-level API for managing the procurement knowledge base.
"""

from typing import List, Dict, Optional
from pathlib import Path
import json

from .vector_store import VectorStore, Document
from .retriever import DocumentRetriever


class KnowledgeBase:
    """
    High-level knowledge base manager
    
    Provides easy-to-use API for managing procurement domain knowledge.
    
    Example:
        kb = KnowledgeBase(persist_directory="./data/knowledge_base")
        
        # Add documents
        await kb.add_example(
            content="AI threat detection system...",
            category="cybersecurity",
            title="Successful Security Bid 2025",
            metadata={"success_rate": 0.95, "year": 2025}
        )
        
        # Retrieve for RAG
        context = await kb.get_context("AI security tender", k=2)
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "procurement_knowledge_base"
    ):
        """
        Initialize knowledge base
        
        Args:
            persist_directory: Directory to persist data (None = in-memory)
            collection_name: Name of the collection
        """
        self.vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        self.retriever = DocumentRetriever(self.vector_store)
    
    async def add_example(
        self,
        content: str,
        category: str,
        title: str,
        metadata: Optional[Dict] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add a high-quality example document
        
        Args:
            content: Document text
            category: Category (e.g., "cybersecurity", "ai", "software")
            title: Document title
            metadata: Additional metadata (success_rate, year, etc.)
            doc_id: Optional document ID
        
        Returns:
            Document ID
        """
        meta = metadata or {}
        meta.update({
            "category": category,
            "title": title
        })
        
        doc = Document(
            content=content,
            metadata=meta,
            id=doc_id
        )
        
        return await self.vector_store.add_document(doc)
    
    async def add_examples_bulk(self, examples: List[Dict]) -> List[str]:
        """
        Add multiple examples at once
        
        Args:
            examples: List of dicts with keys: content, category, title, metadata (optional)
        
        Returns:
            List of document IDs
        """
        documents = []
        for ex in examples:
            meta = ex.get('metadata', {})
            meta.update({
                "category": ex['category'],
                "title": ex['title']
            })
            
            documents.append(Document(
                content=ex['content'],
                metadata=meta,
                id=ex.get('id')
            ))
        
        return await self.vector_store.add_documents(documents)
    
    async def get_context(
        self,
        query: str,
        k: int = 2,
        min_similarity: float = 0.6,
        category: Optional[str] = None
    ) -> str:
        """
        Get formatted context for RAG prompts
        
        Args:
            query: Query text (tender description, etc.)
            k: Number of examples to retrieve
            min_similarity: Minimum similarity threshold
            category: Optional category filter
        
        Returns:
            Formatted context string ready for prompt inclusion
        """
        filter_meta = {"category": category} if category else None
        
        return await self.retriever.retrieve_and_format(
            query=query,
            k=k,
            min_similarity=min_similarity,
            filter_metadata=filter_meta
        )
    
    async def search(
        self,
        query: str,
        k: int = 5,
        min_similarity: float = 0.5,
        category: Optional[str] = None
    ):
        """
        Search knowledge base
        
        Args:
            query: Search query
            k: Number of results
            min_similarity: Minimum similarity threshold
            category: Optional category filter
        
        Returns:
            List of RetrievalResult objects
        """
        filter_meta = {"category": category} if category else None
        
        results = await self.retriever.retrieve(
            query=query,
            k=k,
            min_similarity=min_similarity,
            filter_metadata=filter_meta
        )
        
        return results
    
    def count(self) -> int:
        """Get number of documents in knowledge base"""
        return self.vector_store.count()
    
    def get_statistics(self) -> Dict:
        """
        Get knowledge base statistics
        
        Returns:
            Dictionary with statistics
        """
        all_docs = self.vector_store.get_all_documents()
        
        if not all_docs['metadatas']:
            return {"total_documents": 0, "categories": []}
        
        categories = {}
        for meta in all_docs['metadatas']:
            cat = meta.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_documents": len(all_docs['ids']),
            "categories": categories
        }
    
    async def export_to_json(self, filepath: str):
        """
        Export knowledge base to JSON file
        
        Args:
            filepath: Path to save JSON file
        """
        all_docs = self.vector_store.get_all_documents()
        
        export_data = []
        for doc_id, content, metadata in zip(
            all_docs['ids'],
            all_docs['documents'],
            all_docs['metadatas']
        ):
            export_data.append({
                "id": doc_id,
                "content": content,
                "metadata": metadata
            })
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    async def import_from_json(self, filepath: str) -> int:
        """
        Import knowledge base from JSON file
        
        Args:
            filepath: Path to JSON file
        
        Returns:
            Number of documents imported
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            # Merge category and title into metadata (like add_example does)
            meta = item.get('metadata', {})
            meta.update({
                "category": item.get('category', 'unknown'),
                "title": item.get('title', 'Untitled')
            })
            
            documents.append(Document(
                content=item['content'],
                metadata=meta,
                id=item.get('id')
            ))
        
        await self.vector_store.add_documents(documents)
        return len(documents)
    
    def reset(self):
        """Clear all documents (for testing)"""
        self.vector_store.reset()
