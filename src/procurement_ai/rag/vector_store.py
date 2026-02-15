"""
Vector Store for Semantic Search

Wraps ChromaDB for efficient similarity search with embeddings.
"""

import chromadb
from chromadb.config import Settings
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

from .embeddings import EmbeddingService


@dataclass
class Document:
    """Document to store in vector database"""
    content: str
    metadata: Dict[str, any]
    id: Optional[str] = None


class VectorStore:
    """
    Vector database for semantic search
    
    Stores documents with their embeddings and enables similarity search.
    
    Example:
        store = VectorStore(persist_directory="./kb_data")
        
        # Add documents
        await store.add_documents([
            Document(
                content="AI threat detection system...",
                metadata={"category": "cybersecurity", "year": 2025}
            )
        ])
        
        # Search
        results = await store.search("security solutions", k=3)
    """
    
    def __init__(
        self,
        collection_name: str = "procurement_knowledge_base",
        persist_directory: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize vector store
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to store data (None = in-memory)
            embedding_service: Embedding service (creates one if not provided)
        """
        self.collection_name = collection_name
        self.embedding_service = embedding_service or EmbeddingService()
        
        # Initialize ChromaDB client
        if persist_directory:
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Knowledge base for RAG"}
        )
    
    async def add_document(self, document: Document) -> str:
        """
        Add a single document
        
        Args:
            document: Document to add
        
        Returns:
            Document ID
        """
        # Generate ID if not provided
        doc_id = document.id or f"doc_{self.collection.count() + 1}"
        
        # Create embedding
        embedding = await self.embedding_service.create_embedding(document.content)
        
        # Add to ChromaDB
        self.collection.add(
            documents=[document.content],
            embeddings=[embedding],
            metadatas=[document.metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add multiple documents
        
        Args:
            documents: List of documents to add
        
        Returns:
            List of document IDs
        """
        doc_ids = []
        for doc in documents:
            doc_id = await self.add_document(doc)
            doc_ids.append(doc_id)
        
        return doc_ids
    
    async def search(
        self,
        query: str,
        k: int = 3,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {"category": "cybersecurity"})
        
        Returns:
            Dictionary with:
                - ids: Document IDs
                - documents: Document contents
                - metadatas: Document metadata
                - distances: Similarity distances (lower = more similar)
        """
        # Create query embedding
        query_embedding = await self.embedding_service.create_embedding(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self.collection.count()),
            where=filter_metadata
        )
        
        return results
    
    def count(self) -> int:
        """Get number of documents in store"""
        return self.collection.count()
    
    def reset(self):
        """Delete all documents (for testing)"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Knowledge base for RAG"}
        )
    
    def get_all_documents(self) -> Dict:
        """
        Get all documents in the collection
        
        Returns:
            Dictionary with ids, documents, and metadatas
        """
        result = self.collection.get()
        return result
