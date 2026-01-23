"""
Quickstart Example - 5 Minute Demo
===================================

This demonstrates the core workflow in the simplest possible way.
Perfect for understanding the basics.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from procurement_ai import (
    Config,
    ProcurementOrchestrator,
)
from procurement_ai.models import Tender


async def main():
    """Run a simple demo"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         PROCUREMENT AI - QUICKSTART DEMO                     ║
║                                                              ║
║  Process a single tender in 3 steps:                         ║
║  1. Filter for relevance                                     ║
║  2. Rate the opportunity                                     ║
║  3. Generate bid document                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Make sure LM Studio is running on localhost:1234!
""")

    # Sample tender
    tender = Tender(
        id="DEMO-001",
        title="AI-Powered Threat Detection System",
        description="""
        Government agency seeks vendor to develop an AI-based cybersecurity
        platform for detecting threats in real-time across critical infrastructure.
        Must integrate with existing SIEM tools and handle 100TB+ daily data.
        """,
        organization="National Cybersecurity Agency",
        deadline="2026-06-30",
        estimated_value="€2,500,000",
    )

    # Process it!
    orchestrator = ProcurementOrchestrator()
    result = await orchestrator.process_tender(tender)

    # Show results
    print(f"\n{'=' * 60}")
    print("RESULT")
    print(f"{'=' * 60}\n")
    print(f"Status: {result.status}")
    print(f"Processing Time: {result.processing_time:.2f}s")
    
    if result.filter_result:
        print(f"\nRelevance: {result.filter_result.is_relevant} ({result.filter_result.confidence:.0%} confident)")
    
    if result.rating_result:
        print(f"Score: {result.rating_result.overall_score:.1f}/10")
        print(f"Recommendation: {result.rating_result.recommendation[:80]}...")
    
    if result.bid_document:
        print(f"\nExecutive Summary Generated:")
        print(result.bid_document.executive_summary[:200] + "...")


if __name__ == "__main__":
    asyncio.run(main())
