# Evaluation Framework

Comprehensive evaluation system for AI agents in the procurement pipeline.

## Overview

This framework provides professional-grade evaluation capabilities:

- **Quantitative Metrics** - Precision, recall, F1, MAE, correlation, calibration
- **High-Quality Test Set** - 18 carefully curated test cases covering all scenarios
- **Automated Evaluation** - Run complete evaluations with one command
- **Multiple Output Formats** - Console, JSON, Markdown reports
- **A/B Testing Support** - Compare different configurations scientifically
- **Regression Testing** - Ensure changes don't break existing functionality

## Quick Start

### Run Evaluation

```bash
# Simple console output
python -m procurement_ai.evaluation.run

# Save as baseline for future comparison
python -m procurement_ai.evaluation.run --save-baseline

# Custom output paths
python -m procurement_ai.evaluation.run \
    --output results/eval_20260214.json \
    --markdown results/eval_20260214.md

# Show detailed per-test results
python -m procurement_ai.evaluation.run --detailed
```

### Programmatic Usage

```python
from procurement_ai.evaluation import Evaluator, ConsoleReporter
from procurement_ai.config import Config
from tests.fixtures.evaluation_dataset import ALL_TEST_CASES

# Initialize
config = Config()
evaluator = Evaluator(config=config)

# Run evaluation
result = await evaluator.evaluate_dataset(ALL_TEST_CASES)

# Display results
ConsoleReporter.report(result, detailed=True)

# Access specific metrics
print(f"Filter F1 Score: {result.filter_metrics.f1_score:.2%}")
print(f"Rating MAE: {result.rating_metrics.mae:.2f}")
print(f"Calibration Error: {result.confidence_calibration.expected_calibration_error:.4f}")
```

## Test Dataset

The evaluation dataset contains 18 high-quality test cases:

### Categories

| Category | Count | Purpose |
|----------|-------|---------|
| **Clear Relevant** | 4 | Obvious matches - build confidence in true positives |
| **Clear Irrelevant** | 4 | Obvious rejections - test specificity |
| **Edge Cases** | 5 | Tricky scenarios - find weaknesses |
| **Rating Validation** | 3 | Test scoring accuracy and consistency |
| **Category Tests** | 2 | Challenge category detection logic |

### Example Test Cases

**EVAL-001: AI-Powered Threat Detection** (Clear Relevant)
- Combines AI + cybersecurity + software development
- Expected: Relevant with high confidence (>0.9)
- Tests: Core competency detection

**EVAL-009: Network Infrastructure with Software** (Edge Case)
- 80% hardware, 20% software
- Expected: Irrelevant (hardware-dominant)
- Tests: Can agent distinguish proportion vs presence?

**EVAL-011: AI-Enabled Cameras** (Edge Case)
- "AI" in title but actually hardware procurement
- Expected: Irrelevant
- Tests: Keyword-based false positives

See `tests/fixtures/evaluation_dataset.py` for complete dataset.

## Metrics Explained

### Filter Agent (Binary Classification)

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Precision** | TP / (TP + FP) | When we say "relevant", how often are we right? |
| **Recall** | TP / (TP + FN) | Of all relevant tenders, how many did we catch? |
| **F1 Score** | 2 × (P × R) / (P + R) | Balanced metric (harmonic mean) |
| **Accuracy** | (TP + TN) / Total | Overall correctness |
| **Specificity** | TN / (TN + FP) | How well do we reject irrelevant? |

**Good targets:**
- F1 > 0.85 (excellent), 0.75-0.85 (good)
- Precision > 0.85 (minimize wasted effort)
- Recall > 0.80 (don't miss opportunities)

### Category Detection

| Metric | Interpretation |
|--------|----------------|
| **Accuracy** | Exact category set match (order-independent) |

Requires exact match: `[cybersecurity, ai]` ≠ `[cybersecurity]`

### Rating Agent (Regression)

| Metric | Interpretation | Good Target |
|--------|----------------|-------------|
| **MAE** | Average prediction error | < 1.0 points |
| **RMSE** | Root mean squared error | < 1.5 points |
| **Correlation** | Pearson r between predicted and expected | > 0.70 |

### Confidence Calibration

| Metric | Interpretation | Good Target |
|--------|----------------|-------------|
| **ECE** | Expected Calibration Error | < 0.10 |

**Example:**
- Agent says 90% confident → Should be correct ~90% of time
- ECE measures average gap between confidence and actual accuracy
- High ECE = overconfident (dangerous!)

## Usage Patterns

### A/B Testing Prompts

```python
# 1. Establish baseline
baseline = await evaluator.evaluate_dataset(ALL_TEST_CASES)
baseline_f1 = baseline.filter_metrics.f1_score

# 2. Modify prompt in agents/filter.py

# 3. Re-evaluate
new_result = await evaluator.evaluate_dataset(ALL_TEST_CASES)
new_f1 = new_result.filter_metrics.f1_score

# 4. Decide based on data
improvement = new_f1 - baseline_f1
if improvement > 0.03:  # >3% improvement
    print(f"✅ Keep change! Improvement: {improvement:.2%}")
else:
    print(f"❌ Revert. No significant improvement.")
```

### Quick Iteration

```python
# Fast evaluation for rapid iteration
metrics = await evaluator.quick_eval(test_cases[:10])
print(f"Quick F1: {metrics['f1_score']:.2%}")
```

### Regression Testing

```bash
# Before changes
python -m procurement_ai.evaluation.run --save-baseline

# After changes
python -m procurement_ai.evaluation.run --output after_change.json

# Compare (manually or with script)
# Fail CI/CD if F1 drops > 2%
```

### Track Over Time

```python
from procurement_ai.evaluation import JSONReporter
from pathlib import Path
import json

# Save each evaluation
results_dir = Path("benchmarks/results")
timestamp = "20260214_1430"

JSONReporter.report(
    result,
    output_file=results_dir / f"eval_{timestamp}.json"
)

# Later: Load and compare
with open(results_dir / "eval_20260214_1430.json") as f:
    old_result = json.load(f)

print(f"F1 then: {old_result['metrics']['filter']['f1_score']:.2%}")
print(f"F1 now:  {result.filter_metrics.f1_score:.2%}")
```

## Architecture

```
src/procurement_ai/evaluation/
├── __init__.py          # Public API exports
├── metrics.py           # Core metric calculations
│   ├── FilterMetrics    # Precision, recall, F1
│   ├── CategoryMetrics  # Category detection accuracy
│   ├── RatingMetrics    # MAE, RMSE, correlation
│   ├── DocumentMetrics  # Quality scores (future: LLM-as-judge)
│   └── ConfidenceCalibration  # ECE calculation
├── evaluator.py         # Main evaluation orchestrator
│   ├── Evaluator        # Runs test cases through agents
│   ├── TestCaseResult   # Individual test result
│   └── EvaluationResult # Complete evaluation results
├── reporters.py         # Output formatting
│   ├── ConsoleReporter  # Human-readable terminal output
│   ├── JSONReporter     # Machine-readable for tracking
│   ├── MarkdownReporter # Documentation format
│   └── ComparisonReporter  # Before/after comparison
└── run.py              # CLI entry point

tests/fixtures/
└── evaluation_dataset.py  # 18 curated test cases
```

## Best Practices

### 1. Always Measure Before Changing

```python
# ❌ Bad: Change then hope
modify_prompt()
deploy()  # Did it help? Who knows!

# ✅ Good: Measure → Change → Measure
baseline = evaluate()
modify_prompt()
new_result = evaluate()
if improved(baseline, new_result):
    deploy()
```

### 2. Focus on Weakest Metrics First

```python
# Analyze where to improve
result = await evaluator.evaluate_dataset(ALL_TEST_CASES)

print(f"Precision: {result.filter_metrics.precision:.2%}")  # 0.92 ✅
print(f"Recall: {result.filter_metrics.recall:.2%}")        # 0.72 ⚠️

# → Focus on improving recall (catching more relevant tenders)
```

### 3. Use Edge Cases to Drive Improvements

```python
from tests.fixtures.evaluation_dataset import TestCaseCategory, get_test_cases_by_category

# Test on hardest cases
edge_cases = get_test_cases_by_category(TestCaseCategory.EDGE_CASE)
result = await evaluator.evaluate_dataset(edge_cases)

# Identify failures
failed = [r for r in result.test_results if not r.is_correct]
for failure in failed:
    print(f"Failed: {failure.test_id} - {failure.notes}")
    # Analyze why it failed → Update prompt/criteria
```

### 4. Set Quality Gates

```bash
# In CI/CD
python -m procurement_ai.evaluation.run --output ci_result.json

# Parse results
if F1 < 0.80:
    exit 1  # Block deployment

if F1_drop > 0.02 compared to baseline:
    exit 1  # Regression detected
```

### 5. Document Experiment Results

```python
# Use Markdown reports for documentation
MarkdownReporter.report(
    result,
    output_file=Path("docs/experiments/prompt_v2_evaluation.md"),
    title="Experiment: Few-Shot Prompting Impact"
)

# Commit to git for history
```

## Common Questions

### Q: My F1 is 0.80. Is that good?

**A:** Context-dependent:
- **0.90+:** Excellent (production-ready)
- **0.85-0.90:** Good (acceptable for most uses)
- **0.75-0.85:** Moderate (needs improvement)
- **< 0.75:** Poor (significant work needed)

Consider your use case:
- High precision needed? → Focus on reducing false positives
- High recall needed? → Focus on reducing false negatives

### Q: Should I optimize MAE or RMSE?

**A:** Both matter, but differently:
- **MAE:** Average error - easy to interpret ("off by 1.2 points")
- **RMSE:** Penalizes large errors more heavily

If occasional large errors are really bad → optimize RMSE
Otherwise → optimize MAE

### Q: How often should I run evaluations?

**A:**
- **Every significant change** (prompt, logic, model)
- **Before every release** (regression testing)
- **Weekly** during active development (trend tracking)
- **After production incidents** (identify issues)

### Q: Can I add my own test cases?

**A:** Absolutely! Edit `tests/fixtures/evaluation_dataset.py`:

```python
EVAL_019_CUSTOM = EvaluationTestCase(
    tender_id="EVAL-019",
    category=TestCaseCategory.EDGE_CASE,
    title="Your custom test case",
    description="...",
    organization="Test Org",
    expected_relevance=True,
    expected_categories=["cybersecurity"],
    notes="Why this case is important"
)

# Add to ALL_TEST_CASES list
ALL_TEST_CASES.append(EVAL_019_CUSTOM)
```

## Next Steps

1. **Run baseline evaluation**
   ```bash
   python -m procurement_ai.evaluation.run --save-baseline
   ```

2. **Analyze results** - What's the weakest area?

3. **Make targeted improvement** - Fix one thing at a time

4. **Re-evaluate** - Did it actually help?

5. **Iterate** - Repeat until metrics meet targets

6. **Move to next phase** - RAG, memory, advanced features

---

## References

- Learning notebook: `learn/08_evaluating_ai_agents.ipynb`
- Test dataset: `tests/fixtures/evaluation_dataset.py`
- Metrics implementation: `src/procurement_ai/evaluation/metrics.py`
- Unit tests: `tests/unit/test_evaluation_metrics.py`

**Remember:** You can't improve what you don't measure!
