"""
Evaluation framework for AI agents

This module provides comprehensive evaluation capabilities for the procurement AI system:
- Filter agent accuracy metrics (precision, recall, F1)
- Rating agent consistency metrics (MAE, correlation)
- Document generator quality metrics (LLM-as-judge)
- Confidence calibration analysis
- Category detection accuracy
"""

from .metrics import (
    FilterMetrics,
    CategoryMetrics,
    RatingMetrics,
    DocumentMetrics,
    ConfidenceCalibration,
)
from .evaluator import Evaluator, EvaluationResult
from .reporters import ConsoleReporter, JSONReporter, MarkdownReporter, ComparisonReporter

__all__ = [
    "FilterMetrics",
    "CategoryMetrics",
    "RatingMetrics",
    "DocumentMetrics",
    "ConfidenceCalibration",
    "Evaluator",
    "EvaluationResult",
    "ConsoleReporter",
    "JSONReporter",
    "MarkdownReporter",
    "ComparisonReporter",
]
