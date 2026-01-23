"""
Batch Processing Example
========================

Process multiple tenders and generate a summary report.
This is closer to real-world usage.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from procurement_ai import ProcurementOrchestrator
from sample_data import SAMPLE_TENDERS


async def main():
    """Process multiple tenders"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         BATCH PROCESSING DEMO                                ║
║                                                              ║
║  Processing multiple tenders automatically                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    orchestrator = ProcurementOrchestrator()
    
    # Process all tenders
    results = []
    for tender in SAMPLE_TENDERS:
        result = await orchestrator.process_tender(tender)
        results.append(result)

    # Generate summary
    print(f"\n\n{'=' * 60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'=' * 60}\n")

    relevant = sum(
        1 for r in results if r.filter_result and r.filter_result.is_relevant
    )
    high_rated = sum(
        1 for r in results if r.rating_result and r.rating_result.overall_score >= 7.0
    )
    docs_generated = sum(1 for r in results if r.bid_document is not None)

    print(f"Total Tenders Processed: {len(results)}")
    print(f"Relevant Tenders: {relevant}")
    print(f"High-Rated (≥7.0): {high_rated}")
    print(f"Documents Generated: {docs_generated}")
    print(f"\nTotal Processing Time: {sum(r.processing_time for r in results):.2f}s")
    print(
        f"Average Time per Tender: {sum(r.processing_time for r in results) / len(results):.2f}s\n"
    )

    # Detailed breakdown
    for i, result in enumerate(results, 1):
        print(f"\n{'─' * 60}")
        print(f"TENDER {i}: {result.tender.title[:45]}...")
        print(f"{'─' * 60}")
        print(f"Status: {result.status}")

        if result.filter_result:
            print(
                f"Relevant: {result.filter_result.is_relevant} ({result.filter_result.confidence:.0%} confidence)"
            )

        if result.rating_result:
            print(f"Score: {result.rating_result.overall_score:.1f}/10")
            print(f"Recommendation: {result.rating_result.recommendation[:80]}...")


if __name__ == "__main__":
    asyncio.run(main())
