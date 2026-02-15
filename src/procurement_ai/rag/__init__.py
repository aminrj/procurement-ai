"""
RAG (Retrieval-Augmented Generation) Components

This module provides retrieval-augmented generation capabilities:
- Embedding service for text vectorization
- Vector store for similarity search  
- Document retriever for context augmentation
- Knowledge base management

Usage:
    from procurement_ai.rag import VectorStore, DocumentRetriever
    
    # Setup
    store = VectorStore(persist_directory="./kb_data")
    retriever = DocumentRetriever(store)
    
    # Add documents
    await store.add_documents([
        {"content": "...", "metadata": {"category": "cybersecurity"}}
    ])
    
    # Retrieve for RAG
    results = await retriever.retrieve("AI threat detection", k=2)
"""

from .embeddings import EmbeddingService
from .vector_store import VectorStore, Document
from .retriever import DocumentRetriever, RetrievalResult
from .knowledge_base import KnowledgeBase

__all__ = [
    "EmbeddingService",
    "VectorStore",
    "Document",
    "DocumentRetriever",
    "RetrievalResult",
    "KnowledgeBase",
]
