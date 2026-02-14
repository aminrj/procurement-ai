"""
CLI runner for evaluation framework

Usage:
    python -m procurement_ai.evaluation.run
    python -m procurement_ai.evaluation.run --save-baseline
    python -m procurement_ai.evaluation.run --output results/my_eval.json
"""

import asyncio
import sys
from pathlib import Path
import argparse
import logging

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from procurement_ai.evaluation.evaluator import Evaluator
from procurement_ai.evaluation.reporters import ConsoleReporter, JSONReporter, MarkdownReporter
from procurement_ai.config import Config

# Import test dataset
from tests.fixtures.evaluation_dataset import ALL_TEST_CASES, DATASET_STATS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def run_evaluation(
    output_json: Path = None,
    output_markdown: Path = None,
    save_baseline: bool = False,
    detailed: bool = False
):
    """Run complete evaluation"""
    
    print("\n🔬 Starting Evaluation Framework")
    print(f"   Test cases: {DATASET_STATS['total_cases']}")
    print(f"   - Relevant: {DATASET_STATS['relevant_cases']}")
    print(f"   - Irrelevant: {DATASET_STATS['irrelevant_cases']}")
    print(f"   - Edge cases: {DATASET_STATS['edge_cases']}")
    print()
    
    # Initialize evaluator
    config = Config()
    evaluator = Evaluator(config=config)
    
    # Run evaluation
    result = await evaluator.evaluate_dataset(ALL_TEST_CASES, max_concurrent=3)
    
    # Console report
    ConsoleReporter.report(result, detailed=detailed)
    
    # Save outputs
    if save_baseline:
        baseline_dir = Path("benchmarks/results")
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = result.timestamp.replace(":", "-").split(".")[0]
        
        output_json = baseline_dir / f"baseline_{timestamp}.json"
        output_markdown = baseline_dir / f"baseline_{timestamp}.md"
        
        print(f"\n💾 Saving baseline results...")
    
    if output_json:
        JSONReporter.report(result, output_file=output_json)
    
    if output_markdown:
        title = "Baseline Evaluation Report" if save_baseline else "Evaluation Report"
        MarkdownReporter.report(result, output_file=output_markdown, title=title)
    
    return result


def main():
    """CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Run evaluation framework for procurement AI agents"
    )
    
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save results as baseline in benchmarks/results/"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Save JSON results to specified path"
    )
    
    parser.add_argument(
        "--markdown",
        type=Path,
        help="Save markdown report to specified path"
    )
    
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed test case results"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_evaluation(
            output_json=args.output,
            output_markdown=args.markdown,
            save_baseline=args.save_baseline,
            detailed=args.detailed
        ))
    except KeyboardInterrupt:
        print("\n\nEvaluation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
