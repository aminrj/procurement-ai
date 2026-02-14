"""
Result reporters for evaluation output

Provides multiple output formats:
- Console: Human-readable terminal output
- JSON: Machine-readable format for tracking
- Markdown: Documentation and sharing
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime
from pathlib import Path

from .evaluator import EvaluationResult


class ConsoleReporter:
    """Human-readable console output"""
    
    @staticmethod
    def report(result: EvaluationResult, detailed: bool = False):
        """Print evaluation results to console"""
        
        print("\n" + "=" * 70)
        print(" EVALUATION RESULTS")
        print("=" * 70)
        
        print(f"\nTimestamp: {result.timestamp}")
        print(f"Test Cases: {result.test_cases_count}")
        print(f"Processing Time: {result.total_processing_time:.2f}s")
        if result.errors_count > 0:
            print(f"⚠️  Errors: {result.errors_count}")
        
        # Filter metrics
        print("\n" + "-" * 70)
        print("FILTER AGENT PERFORMANCE")
        print("-" * 70)
        fm = result.filter_metrics
        print(f"  Precision:    {fm.precision:6.2%}  (How many predicted-relevant are actually relevant?)")
        print(f"  Recall:       {fm.recall:6.2%}  (How many actual-relevant did we find?)")
        print(f"  F1 Score:     {fm.f1_score:6.2%}  (Harmonic mean of precision & recall)")
        print(f"  Accuracy:     {fm.accuracy:6.2%}  (Overall correctness)")
        print(f"  Specificity:  {fm.specificity:6.2%}  (True negative rate)")
        
        print("\n  Confusion Matrix:")
        print(f"                    Predicted Relevant  |  Predicted Irrelevant")
        print(f"  Actually Relevant        {fm.true_positives:3d}          |        {fm.false_negatives:3d}")
        print(f"  Actually Irrelevant      {fm.false_positives:3d}          |        {fm.true_negatives:3d}")
        
        # Category metrics
        print("\n" + "-" * 70)
        print("CATEGORY DETECTION")
        print("-" * 70)
        cm = result.category_metrics
        print(f"  Accuracy: {cm.accuracy:6.2%}")
        print(f"  Correct:  {cm.correct_categories}/{cm.total_predictions}")
        
        # Rating metrics
        print("\n" + "-" * 70)
        print("RATING AGENT PERFORMANCE")
        print("-" * 70)
        rm = result.rating_metrics
        if len(rm.errors) == 0:
            print("  No rating predictions evaluated")
        else:
            print(f"  MAE:         {rm.mae:6.2f}  (Mean Absolute Error)")
            print(f"  RMSE:        {rm.rmse:6.2f}  (Root Mean Squared Error)")
            print(f"  Correlation: {rm.correlation:6.2f}  (Pearson r)")
            if rm.total_recommendations > 0:
                print(f"  Rec. Accuracy: {rm.recommendation_accuracy:6.2%}")
        
        # Calibration
        print("\n" + "-" * 70)
        print("CONFIDENCE CALIBRATION")
        print("-" * 70)
        cal = result.confidence_calibration
        print(f"  ECE: {cal.expected_calibration_error:.4f}  (Expected Calibration Error)")
        print("       Lower is better. 0 = perfectly calibrated")
        
        # Detailed results
        if detailed:
            print("\n" + "-" * 70)
            print("DETAILED TEST RESULTS")
            print("-" * 70)
            
            # Group by category
            by_category = {}
            for tr in result.test_results:
                if tr.test_category not in by_category:
                    by_category[tr.test_category] = []
                by_category[tr.test_category].append(tr)
            
            for category, tests in by_category.items():
                print(f"\n  {category.upper().replace('_', ' ')}")
                for t in tests:
                    status = "✓" if t.is_correct else "✗"
                    print(f"    {status} {t.test_id}: {t.predicted_relevant} "
                          f"(conf: {t.predicted_confidence:.2f})")
                    if t.error:
                        print(f"       Error: {t.error}")
        
        print("\n" + "=" * 70 + "\n")


class JSONReporter:
    """JSON output for tracking over time"""
    
    @staticmethod
    def report(
        result: EvaluationResult,
        output_file: Optional[Path] = None
    ) -> str:
        """
        Convert results to JSON
        
        Args:
            result: Evaluation result
            output_file: Optional path to save JSON file
        
        Returns:
            JSON string
        """
        
        data = result.to_dict()
        json_str = json.dumps(data, indent=2)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json_str)
            print(f"Results saved to: {output_file}")
        
        return json_str


class MarkdownReporter:
    """Markdown output for documentation"""
    
    @staticmethod
    def report(
        result: EvaluationResult,
        output_file: Optional[Path] = None,
        title: str = "Evaluation Report"
    ) -> str:
        """
        Generate markdown report
        
        Args:
            result: Evaluation result
            output_file: Optional path to save markdown file
            title: Report title
        
        Returns:
            Markdown string
        """
        
        lines = [
            f"# {title}",
            "",
            f"**Generated:** {result.timestamp}",
            f"**Test Cases:** {result.test_cases_count}",
            f"**Processing Time:** {result.total_processing_time:.2f}s",
            "",
        ]
        
        if result.errors_count > 0:
            lines.extend([
                f"⚠️ **Errors:** {result.errors_count}",
                "",
            ])
        
        # Configuration
        lines.extend([
            "## Configuration",
            "",
            "```json",
            json.dumps(result.config, indent=2),
            "```",
            "",
        ])
        
        # Filter metrics
        fm = result.filter_metrics
        lines.extend([
            "## Filter Agent Performance",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Precision | {fm.precision:.2%} |",
            f"| Recall | {fm.recall:.2%} |",
            f"| F1 Score | {fm.f1_score:.2%} |",
            f"| Accuracy | {fm.accuracy:.2%} |",
            f"| Specificity | {fm.specificity:.2%} |",
            "",
            "### Confusion Matrix",
            "",
            "```",
            "                Predicted Relevant  |  Predicted Irrelevant",
            f"Actually Relevant      {fm.true_positives:3d}          |        {fm.false_negatives:3d}",
            f"Actually Irrelevant    {fm.false_positives:3d}          |        {fm.true_negatives:3d}",
            "```",
            "",
        ])
        
        # Category metrics
        cm = result.category_metrics
        lines.extend([
            "## Category Detection",
            "",
            f"- **Accuracy:** {cm.accuracy:.2%}",
            f"- **Correct:** {cm.correct_categories}/{cm.total_predictions}",
            "",
        ])
        
        # Rating metrics
        rm = result.rating_metrics
        lines.extend([
            "## Rating Agent Performance",
            "",
        ])
        
        if len(rm.errors) == 0:
            lines.append("*No rating predictions evaluated*")
        else:
            lines.extend([
                "| Metric | Value |",
                "|--------|-------|",
                f"| MAE | {rm.mae:.2f} |",
                f"| RMSE | {rm.rmse:.2f} |",
                f"| Correlation | {rm.correlation:.2f} |",
            ])
            
            if rm.total_recommendations > 0:
                lines.append(f"| Recommendation Accuracy | {rm.recommendation_accuracy:.2%} |")
        
        lines.append("")
        
        # Calibration
        cal = result.confidence_calibration
        lines.extend([
            "## Confidence Calibration",
            "",
            f"- **Expected Calibration Error:** {cal.expected_calibration_error:.4f}",
            "  - Lower is better (0 = perfectly calibrated)",
            "",
        ])
        
        # Test results summary
        lines.extend([
            "## Test Results by Category",
            "",
        ])
        
        by_category = {}
        for tr in result.test_results:
            if tr.test_category not in by_category:
                by_category[tr.test_category] = {"passed": 0, "failed": 0}
            if tr.is_correct:
                by_category[tr.test_category]["passed"] += 1
            else:
                by_category[tr.test_category]["failed"] += 1
        
        for category, counts in by_category.items():
            total = counts["passed"] + counts["failed"]
            pass_rate = counts["passed"] / total if total > 0 else 0
            lines.append(f"- **{category.replace('_', ' ').title()}:** "
                        f"{counts['passed']}/{total} passed ({pass_rate:.1%})")
        
        lines.append("")
        
        markdown = "\n".join(lines)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(markdown)
            print(f"Markdown report saved to: {output_file}")
        
        return markdown


class ComparisonReporter:
    """Compare two evaluation results"""
    
    @staticmethod
    def compare(
        baseline: EvaluationResult,
        comparison: EvaluationResult,
        baseline_name: str = "Baseline",
        comparison_name: str = "Current"
    ) -> str:
        """
        Generate comparison report
        
        Returns markdown formatted comparison
        """
        
        lines = [
            "# Evaluation Comparison",
            "",
            f"**{baseline_name}:** {baseline.timestamp}",
            f"**{comparison_name}:** {comparison.timestamp}",
            "",
            "## Filter Agent",
            "",
            "| Metric | Baseline | Current | Change |",
            "|--------|----------|---------|--------|",
        ]
        
        # Filter metrics comparison
        metrics = ["precision", "recall", "f1_score", "accuracy"]
        for metric in metrics:
            base_val = getattr(baseline.filter_metrics, metric)
            curr_val = getattr(comparison.filter_metrics, metric)
            delta = curr_val - base_val
            delta_str = f"{delta:+.2%}" if delta != 0 else "—"
            arrow = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
            
            lines.append(
                f"| {metric.replace('_', ' ').title()} | "
                f"{base_val:.2%} | {curr_val:.2%} | {arrow} {delta_str} |"
            )
        
        lines.extend(["", "## Rating Agent", ""])
        
        if len(baseline.rating_metrics.errors) > 0 and \
           len(comparison.rating_metrics.errors) > 0:
            base_mae = baseline.rating_metrics.mae
            curr_mae = comparison.rating_metrics.mae
            delta_mae = curr_mae - base_mae
            arrow = "📈" if delta_mae < 0 else "📉"  # Lower MAE is better
            
            lines.extend([
                "| Metric | Baseline | Current | Change |",
                "|--------|----------|---------|--------|",
                f"| MAE | {base_mae:.2f} | {curr_mae:.2f} | {arrow} {delta_mae:+.2f} |",
            ])
        else:
            lines.append("*Insufficient data for comparison*")
        
        lines.append("")
        
        return "\n".join(lines)
