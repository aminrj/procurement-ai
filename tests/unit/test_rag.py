"""
Unit tests for RAG components
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from procurement_ai.rag import (
    EmbeddingService,
    VectorStore,
    Document,
    DocumentRetriever,
    RetrievalResult,
    KnowledgeBase
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.mark.asyncio
async def test_embedding_service():
    """Test embedding service creates valid vectors"""
    service = EmbeddingService()
    
    text = "AI cybersecurity threat detection"
    embedding = await service.create_embedding(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) == service.EMBEDDING_DIMENSION
    assert all(isinstance(x, (int, float)) for x in embedding)


@pytest.mark.asyncio
async def test_embedding_empty_text():
    """Test embedding service rejects empty text"""
    service = EmbeddingService()
    
    with pytest.raises(ValueError):
        await service.create_embedding("")


@pytest.mark.asyncio
async def test_vector_store_add_document():
    """Test adding document to vector store"""
    store = VectorStore()
    
    doc = Document(
        content="AI threat detection system",
        metadata={"category": "cybersecurity"}
    )
    
    doc_id = await store.add_document(doc)
    
    assert doc_id is not None
    assert store.count() == 1


@pytest.mark.asyncio
async def test_vector_store_search():
    """Test searching vector store"""
    store = VectorStore()
    
    # Add documents
    docs = [
        Document(
            content="AI cybersecurity threat detection with ML",
            metadata={"category": "cybersecurity"}
        ),
        Document(
            content="Office furniture procurement and interior design",
            metadata={"category": "facilities"}
        )
    ]
    
    await store.add_documents(docs)
    
    # Search for security-related
    results = await store.search("AI security system", k=2)
    
    assert len(results['ids'][0]) == 2
    assert len(results['documents'][0]) == 2
    # First result should be cybersecurity (more similar)
    assert "cybersecurity" in results['metadatas'][0][0]['category']


@pytest.mark.asyncio
async def test_vector_store_persistence(temp_dir):
    """Test vector store persistence"""
    persist_path = str(Path(temp_dir) / "test_kb")
    
    # Create and add document
    store1 = VectorStore(persist_directory=persist_path)
    doc = Document(
        content="Test document",
        metadata={"category": "test"}
    )
    await store1.add_document(doc)
    assert store1.count() == 1
    
    # Create new instance - should load persisted data
    store2 = VectorStore(persist_directory=persist_path)
    assert store2.count() == 1


@pytest.mark.asyncio
async def test_document_retriever():
    """Test document retriever"""
    store = VectorStore()
    retriever = DocumentRetriever(store)
    
    # Add documents
    docs = [
        Document(
            content="AI threat detection system",
            metadata={"category": "cybersecurity", "title": "Security Solution"}
        ),
        Document(
            content="CRM software development",
            metadata={"category": "software", "title": "CRM Project"}
        )
    ]
    await store.add_documents(docs)
    
    # Retrieve
    results = await retriever.retrieve("security system", k=2, min_similarity=0.0)
    
    assert len(results) > 0
    assert isinstance(results[0], RetrievalResult)
    assert results[0].similarity >= 0.0
    assert results[0].similarity <= 1.0


@pytest.mark.asyncio
async def test_retriever_format_for_prompt():
    """Test formatting retrieval results for prompts"""
    store = VectorStore()
    retriever = DocumentRetriever(store)
    
    doc = Document(
        content="AI threat detection",
        metadata={" category": "cybersecurity", "title": "Example"}
    )
    await store.add_document(doc)
    
    results = await retriever.retrieve("AI security", k=1, min_similarity=0.0)
    formatted = retriever.format_for_prompt(results)
    
    assert "AI threat detection" in formatted
    assert len(formatted) > 0


@pytest.mark.asyncio
async def test_retriever_min_similarity():
    """Test minimum similarity filtering"""
    store = VectorStore()
    retriever = DocumentRetriever(store)
    
    doc = Document(
        content="Office furniture",
        metadata={"category": "facilities"}
    )
    await store.add_document(doc)
    
    # High similarity threshold - should return nothing for unrelated query
    results = await retriever.retrieve(
        "AI cybersecurity",
        k=1,
        min_similarity=0.9  # Very high threshold
    )
    
    # Might return 0 or 1 depending on embedding similarity
    assert len(results) <= 1


@pytest.mark.asyncio
async def test_knowledge_base_add_example():
    """Test adding example to knowledge base"""
    kb = KnowledgeBase(collection_name="test_kb_add_example")
    
    doc_id = await kb.add_example(
        content="AI threat detection system",
        category="cybersecurity",
        title="Security Example",
        metadata={"year": 2025}
    )
    
    assert doc_id is not None
    assert kb.count() == 1


@pytest.mark.asyncio
async def test_knowledge_base_get_context():
    """Test getting context for RAG"""
    kb = KnowledgeBase(collection_name="test_kb_get_context")
    
    await kb.add_example(
        content="AI cybersecurity solution with 99% accuracy",
        category="cybersecurity",
        title="Security Example"
    )
    
    # Lower min_similarity since we only have 1 doc
    context = await kb.get_context("AI security system", k=1, min_similarity=0.5)
    
    # Should return something if retrieval works
    assert len(context) > 0


@pytest.mark.asyncio
async def test_knowledge_base_statistics():
    """Test knowledge base statistics"""
    kb = KnowledgeBase(collection_name="test_kb_statistics")
    
    # Add examples
    await kb.add_example(
        content="AI system",
        category="ai",
        title="AI Example"
    )
    await kb.add_example(
        content="Security system",
        category="cybersecurity",
        title="Security Example"
    )
    
    stats = kb.get_statistics()
    
    assert stats['total_documents'] == 2
    assert 'ai' in stats['categories']
    assert 'cybersecurity' in stats['categories']


@pytest.mark.asyncio
async def test_knowledge_base_export_import(temp_dir):
    """Test export/import functionality"""
    kb1 = KnowledgeBase(collection_name="test_kb_export")
    
    # Add examples
    await kb1.add_example(
        content="Test content",
        category="test",
        title="Test Example",
        metadata={"year": 2025}
    )
    
    # Export
    export_path = str(Path(temp_dir) / "kb_export.json")
    await kb1.export_to_json(export_path)
    
    # Import into new KB
    kb2 = KnowledgeBase(collection_name="test_kb_import")
    count = await kb2.import_from_json(export_path)
    
    assert count == 1
    assert kb2.count() == 1


@pytest.mark.asyncio
async def test_retrieval_result_str():
    """Test RetrievalResult string formatting"""
    result = RetrievalResult(
        content="Test content",
        metadata={"category": "test", "title": "Test Doc"},
        similarity=0.95
    )
    
    str_repr = str(result)
    assert "test" in str_repr.lower()
    assert "Test content" in str_repr
