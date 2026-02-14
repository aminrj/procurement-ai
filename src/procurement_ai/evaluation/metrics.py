"""
Core evaluation metrics for AI agents

Implements standard classification and regression metrics for evaluating
filter accuracy, rating consistency, and overall system performance.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics


class MetricCategory(str, Enum):
    """Category of evaluation metric"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    QUALITY = "quality"
    CALIBRATION = "calibration"


@dataclass
class FilterMetrics:
    """Metrics for filter agent evaluation"""
    
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    # Confidence scores for calibration
    confident_correct: List[Tuple[float, bool]] = field(default_factory=list)
    
    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def f1_score(self) -> float:
        """F1 Score: Harmonic mean of precision and recall"""
        p = self.precision
        r = self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
    
    @property
    def accuracy(self) -> float:
        """Overall accuracy: (TP + TN) / Total"""
        total = self.true_positives + self.false_positives + \
                self.true_negatives + self.false_negatives
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total
    
    @property
    def specificity(self) -> float:
        """Specificity (True Negative Rate): TN / (TN + FP)"""
        denominator = self.true_negatives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_negatives / denominator
    
    def add_prediction(
        self, 
        predicted: bool, 
        expected: bool, 
        confidence: Optional[float] = None
    ):
        """Add a single prediction result"""
        if predicted and expected:
            self.true_positives += 1
        elif predicted and not expected:
            self.false_positives += 1
        elif not predicted and expected:
            self.false_negatives += 1
        else:
            self.true_negatives += 1
        
        if confidence is not None:
            is_correct = (predicted == expected)
            self.confident_correct.append((confidence, is_correct))
    
    def get_confusion_matrix(self) -> Dict[str, int]:
        """Get confusion matrix as dictionary"""
        return {
            "tp": self.true_positives,
            "fp": self.false_positives,
            "tn": self.true_negatives,
            "fn": self.false_negatives,
        }
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization"""
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "accuracy": round(self.accuracy, 4),
            "specificity": round(self.specificity, 4),
            **self.get_confusion_matrix(),
        }


@dataclass
class CategoryMetrics:
    """Metrics for category detection accuracy"""
    
    correct_categories: int = 0
    total_predictions: int = 0
    category_confusion: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    @property
    def accuracy(self) -> float:
        """Category detection accuracy"""
        if self.total_predictions == 0:
            return 0.0
        return self.correct_categories / self.total_predictions
    
    def add_prediction(
        self,
        predicted: List[str],
        expected: List[str]
    ):
        """Add category prediction result"""
        self.total_predictions += 1
        
        # Convert to sets for comparison
        pred_set = set(predicted)
        exp_set = set(expected)
        
        # Exact match required
        if pred_set == exp_set:
            self.correct_categories += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "accuracy": round(self.accuracy, 4),
            "correct": self.correct_categories,
            "total": self.total_predictions,
        }


@dataclass
class RatingMetrics:
    """Metrics for rating agent evaluation"""
    
    errors: List[float] = field(default_factory=list)
    actual_scores: List[float] = field(default_factory=list)
    predicted_scores: List[float] = field(default_factory=list)
    
    # Recommendation accuracy
    correct_recommendations: int = 0
    total_recommendations: int = 0
    
    @property
    def mae(self) -> float:
        """Mean Absolute Error"""
        if not self.errors:
            return 0.0
        return statistics.mean([abs(e) for e in self.errors])
    
    @property
    def rmse(self) -> float:
        """Root Mean Squared Error"""
        if not self.errors:
            return 0.0
        return (statistics.mean([e ** 2 for e in self.errors])) ** 0.5
    
    @property
    def correlation(self) -> float:
        """Pearson correlation coefficient between actual and predicted"""
        if len(self.actual_scores) < 2:
            return 0.0
        
        n = len(self.actual_scores)
        mean_actual = statistics.mean(self.actual_scores)
        mean_pred = statistics.mean(self.predicted_scores)
        
        numerator = sum(
            (a - mean_actual) * (p - mean_pred)
            for a, p in zip(self.actual_scores, self.predicted_scores)
        )
        
        denom_actual = sum((a - mean_actual) ** 2 for a in self.actual_scores)
        denom_pred = sum((p - mean_pred) ** 2 for p in self.predicted_scores)
        
        denominator = (denom_actual * denom_pred) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    @property
    def recommendation_accuracy(self) -> float:
        """Accuracy of go/no-go recommendations"""
        if self.total_recommendations == 0:
            return 0.0
        return self.correct_recommendations / self.total_recommendations
    
    def add_prediction(
        self,
        predicted_score: float,
        expected_range: Tuple[float, float]
    ):
        """Add a rating prediction"""
        # Use middle of expected range as "actual"
        actual = (expected_range[0] + expected_range[1]) / 2
        error = predicted_score - actual
        
        self.errors.append(error)
        self.actual_scores.append(actual)
        self.predicted_scores.append(predicted_score)
    
    def add_recommendation(
        self,
        predicted: str,
        expected: str
    ):
        """Add recommendation prediction"""
        self.total_recommendations += 1
        if predicted.lower() == expected.lower():
            self.correct_recommendations += 1
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "mae": round(self.mae, 4),
            "rmse": round(self.rmse, 4),
            "correlation": round(self.correlation, 4),
            "recommendation_accuracy": round(self.recommendation_accuracy, 4),
            "total_predictions": len(self.errors),
        }


@dataclass
class DocumentMetrics:
    """Metrics for document generator evaluation using LLM-as-judge"""
    
    completeness_scores: List[float] = field(default_factory=list)
    relevance_scores: List[float] = field(default_factory=list)
    professionalism_scores: List[float] = field(default_factory=list)
    technical_depth_scores: List[float] = field(default_factory=list)
    overall_scores: List[float] = field(default_factory=list)
    
    @property
    def avg_completeness(self) -> float:
        """Average completeness score"""
        return statistics.mean(self.completeness_scores) if self.completeness_scores else 0.0
    
    @property
    def avg_relevance(self) -> float:
        """Average relevance score"""
        return statistics.mean(self.relevance_scores) if self.relevance_scores else 0.0
    
    @property
    def avg_professionalism(self) -> float:
        """Average professionalism score"""
        return statistics.mean(self.professionalism_scores) if self.professionalism_scores else 0.0
    
    @property
    def avg_technical_depth(self) -> float:
        """Average technical depth score"""
        return statistics.mean(self.technical_depth_scores) if self.technical_depth_scores else 0.0
    
    @property
    def avg_overall(self) -> float:
        """Average overall quality score"""
        return statistics.mean(self.overall_scores) if self.overall_scores else 0.0
    
    def add_evaluation(
        self,
        completeness: float,
        relevance: float,
        professionalism: float,
        technical_depth: float,
        overall: float
    ):
        """Add document evaluation scores"""
        self.completeness_scores.append(completeness)
        self.relevance_scores.append(relevance)
        self.professionalism_scores.append(professionalism)
        self.technical_depth_scores.append(technical_depth)
        self.overall_scores.append(overall)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "completeness": round(self.avg_completeness, 2),
            "relevance": round(self.avg_relevance, 2),
            "professionalism": round(self.avg_professionalism, 2),
            "technical_depth": round(self.avg_technical_depth, 2),
            "overall_quality": round(self.avg_overall, 2),
            "total_evaluations": len(self.overall_scores),
        }


@dataclass
class ConfidenceCalibration:
    """Analyze confidence calibration of predictions"""
    
    predictions: List[Tuple[float, bool]] = field(default_factory=list)
    
    def add_prediction(self, confidence: float, is_correct: bool):
        """Add a prediction with confidence and correctness"""
        self.predictions.append((confidence, is_correct))
    
    def get_calibration_curve(
        self, 
        num_bins: int = 10
    ) -> List[Dict[str, float]]:
        """
        Get calibration curve data
        
        Returns list of bins with:
        - mean_confidence: average confidence in bin
        - accuracy: actual accuracy in bin
        - count: number of predictions in bin
        """
        if not self.predictions:
            return []
        
        # Sort by confidence
        sorted_preds = sorted(self.predictions, key=lambda x: x[0])
        
        # Calculate bin size
        bin_size = len(sorted_preds) // num_bins
        if bin_size == 0:
            bin_size = 1
        
        bins = []
        for i in range(0, len(sorted_preds), bin_size):
            bin_preds = sorted_preds[i:i + bin_size]
            if not bin_preds:
                continue
            
            confidences = [p[0] for p in bin_preds]
            corrects = [p[1] for p in bin_preds]
            
            bins.append({
                "mean_confidence": statistics.mean(confidences),
                "accuracy": sum(corrects) / len(corrects),
                "count": len(bin_preds),
                "calibration_error": abs(
                    statistics.mean(confidences) - (sum(corrects) / len(corrects))
                ),
            })
        
        return bins
    
    @property
    def expected_calibration_error(self) -> float:
        """
        Calculate Expected Calibration Error (ECE)
        
        Measures average difference between confidence and accuracy
        across bins. Lower is better (perfectly calibrated = 0).
        """
        bins = self.get_calibration_curve()
        if not bins:
            return 0.0
        
        total_predictions = sum(b["count"] for b in bins)
        
        ece = sum(
            (b["count"] / total_predictions) * b["calibration_error"]
            for b in bins
        )
        
        return ece
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "expected_calibration_error": round(self.expected_calibration_error, 4),
            "total_predictions": len(self.predictions),
            "calibration_curve": self.get_calibration_curve(),
        }
