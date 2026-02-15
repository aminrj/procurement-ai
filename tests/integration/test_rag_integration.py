"""
Test RAG integration with DocumentGenerator
"""

import pytest
from procurement_ai.agents.generator import DocumentGenerator, BidDocument
from procurement_ai.models import Tender
from procurement_ai.services.llm import LLMService
from procurement_ai.config import Config
from procurement_ai.rag import KnowledgeBase


@pytest.mark.asyncio
async def test_document_generator_without_rag():
    """Test DocumentGenerator works without RAG"""
    config = Config()
    llm = LLMService(config)
    generator = DocumentGenerator(llm, config)
    
    tender = Tender(
        title="AI Threat Detection System",
        description="Develop AI-powered cybersecurity threat detection",
        organization="Government Agency",
        category="Technology",
        deadline="2025-06-30"
    )
    
    result = await generator.generate(
        tender=tender,
        categories=["cybersecurity", "ai"],
        strengths=["20 years experience", "ISO 27001 certified"]
    )
    
    assert isinstance(result, BidDocument)
    assert len(result.executive_summary) > 50
    assert len(result.technical_approach) > 50
    assert generator.use_rag is False


@pytest.mark.asyncio
async def test_document_generator_with_rag():
    """Test DocumentGenerator with RAG enhancement"""
    config = Config()
    llm = LLMService(config)
    
    # Create knowledge base with example
    kb = KnowledgeBase(collection_name="test_doc_gen_rag")
    await kb.add_example(
        content="""## Executive Summary
Our AI-powered threat detection delivers 99% accuracy with real-time monitoring 
and automated response. We've deployed similar systems for 15+ government agencies.

## Technical Approach
Three-tier detection architecture using neural networks, behavioral analytics, 
and automated response integration with existing SIEM infrastructure.

## Value Proposition
ISO 27001 certified team, government clearance, on-premises deployment ensuring 
complete data sovereignty.

## Timeline
Phase 1 (Weeks 1-4): Infrastructure setup
Phase 2 (Weeks 5-8): Model training
Phase 3 (Weeks 9-12): Deployment""",
        category="cybersecurity",
        title="Example Cybersecurity Bid"
    )
    
    # Create generator with RAG
    generator = DocumentGenerator(llm, config, knowledge_base=kb)
    
    tender = Tender(
        title="AI Security Monitoring",
        description="Implement AI-based security threat monitoring for critical infrastructure",
        organization="National Infrastructure Agency",
        category="Cybersecurity",
        deadline="2025-08-15"
    )
    
    result = await generator.generate(
        tender=tender,
        categories=["cybersecurity"],
        strengths=["AI expertise", "Security clearance"]
    )
    
    assert isinstance(result, BidDocument)
    assert len(result.executive_summary) > 50
    assert len(result.technical_approach) > 50
    assert generator.use_rag is True
    
    # RAG version should ideally be more specific/detailed
    # (Can't easily assert this without manual comparison)


@pytest.mark.asyncio
async def test_document_generator_rag_no_matches():
    """Test DocumentGenerator when RAG finds no relevant examples"""
    config = Config()
    llm = LLMService(config)
    
    # Create KB with unrelated example
    kb = KnowledgeBase(collection_name="test_doc_gen_no_match")
    await kb.add_example(
        content="Office furniture procurement guidelines",
        category="facilities",
        title="Furniture Example"
    )
    
    generator = DocumentGenerator(llm, config, knowledge_base=kb)
    
    tender = Tender(
        title="AI Research Initiative",
        description="Advanced machine learning research collaboration",
        organization="University",
        category="Research",
        deadline="2025-12-31"
    )
    
    # Should still generate even without RAG matches
    result = await generator.generate(
        tender=tender,
        categories=["ai", "research"],
        strengths=["PhD researchers", "Published papers"]
    )
    
    assert isinstance(result, BidDocument)
    assert len(result.executive_summary) > 50
