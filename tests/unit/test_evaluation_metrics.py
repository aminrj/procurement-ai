"""
Unit tests for evaluation metrics

Tests all metric calculations to ensure correctness.
"""

import pytest
from procurement_ai.evaluation.metrics import (
    FilterMetrics,
    CategoryMetrics,
    RatingMetrics,
    DocumentMetrics,
    ConfidenceCalibration,
)


class TestFilterMetrics:
    """Test filter agent metrics calculations"""
    
    def test_perfect_classifier(self):
        """Test metrics with perfect classification"""
        metrics = FilterMetrics()
        
        # Add perfect predictions
        metrics.add_prediction(True, True, 0.95)   # TP
        metrics.add_prediction(True, True, 0.92)   # TP
        metrics.add_prediction(False, False, 0.88)  # TN
        metrics.add_prediction(False, False, 0.90)  # TN
        
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
        assert metrics.accuracy == 1.0
        assert metrics.specificity == 1.0
    
    def test_all_false_positives(self):
        """Test metrics when predicting all positive"""
        metrics = FilterMetrics()
        
        # Predict everything as positive
        metrics.add_prediction(True, True, 0.85)   # TP
        metrics.add_prediction(True, False, 0.80)  # FP
        metrics.add_prediction(True, False, 0.75)  # FP
        
        assert metrics.precision == 1/3  # Only 1 of 3 positives was correct
        assert metrics.recall == 1.0     # Found the only true positive
        assert metrics.specificity == 0.0 # Didn't identify any true negatives
    
    def test_all_false_negatives(self):
        """Test metrics when predicting all negative"""
        metrics = FilterMetrics()
        
        # Predict everything as negative
        metrics.add_prediction(False, True, 0.40)   # FN
        metrics.add_prediction(False, True, 0.45)   # FN
        metrics.add_prediction(False, False, 0.92)  # TN
        
        assert metrics.precision == 0.0  # No positive predictions
        assert metrics.recall == 0.0     # Missed all true positives
        assert metrics.specificity == 1.0 # Correctly identified true negative
    
    def test_balanced_case(self):
        """Test realistic balanced scenario"""
        metrics = FilterMetrics()
        
        # Simulate realistic scenario
        # 2 TP, 1 FP, 3 TN, 1 FN
        metrics.add_prediction(True, True, 0.88)
        metrics.add_prediction(True, True, 0.91)
        metrics.add_prediction(True, False, 0.75)   # FP - mistake
        metrics.add_prediction(False, False, 0.85)
        metrics.add_prediction(False, False, 0.90)
        metrics.add_prediction(False, False, 0.88)
        metrics.add_prediction(False, True, 0.55)   # FN - missed one
        
        # Check calculations
        assert metrics.true_positives == 2
        assert metrics.false_positives == 1
        assert metrics.true_negatives == 3
        assert metrics.false_negatives == 1
        
        # Precision: 2 / (2 + 1) = 0.667
        assert abs(metrics.precision - 0.667) < 0.01
        
        # Recall: 2 / (2 + 1) = 0.667
        assert abs(metrics.recall - 0.667) < 0.01
        
        # F1: 2 * (0.667 * 0.667) / (0.667 + 0.667) = 0.667
        assert abs(metrics.f1_score - 0.667) < 0.01
        
        # Accuracy: (2 + 3) / 7 = 0.714
        assert abs(metrics.accuracy - 0.714) < 0.01
    
    def test_confusion_matrix(self):
        """Test confusion matrix export"""
        metrics = FilterMetrics()
        metrics.true_positives = 5
        metrics.false_positives = 2
        metrics.true_negatives = 8
        metrics.false_negatives = 1
        
        cm = metrics.get_confusion_matrix()
        assert cm["tp"] == 5
        assert cm["fp"] == 2
        assert cm["tn"] == 8
        assert cm["fn"] == 1
    
    def test_to_dict(self):
        """Test dictionary serialization"""
        metrics = FilterMetrics()
        metrics.add_prediction(True, True, 0.95)
        metrics.add_prediction(False, False, 0.92)
        
        d = metrics.to_dict()
        assert "precision" in d
        assert "recall" in d
        assert "f1_score" in d
        assert "accuracy" in d
        assert d["tp"] == 1
        assert d["tn"] == 1


class TestCategoryMetrics:
    """Test category detection metrics"""
    
    def test_exact_match_required(self):
        """Category prediction requires exact set match"""
        metrics = CategoryMetrics()
        
        # Exact match - should be correct
        metrics.add_prediction(
            predicted=["cybersecurity", "ai"],
            expected=["cybersecurity", "ai"]
        )
        assert metrics.correct_categories == 1
        
        # Order shouldn't matter
        metrics.add_prediction(
            predicted=["ai", "cybersecurity"],
            expected=["cybersecurity", "ai"]
        )
        assert metrics.correct_categories == 2
        
        # Partial match - should be incorrect
        metrics.add_prediction(
            predicted=["cybersecurity"],
            expected=["cybersecurity", "ai"]
        )
        assert metrics.correct_categories == 2  # Still 2, not 3
        
        # Extra category - should be incorrect
        metrics.add_prediction(
            predicted=["cybersecurity", "ai", "software"],
            expected=["cybersecurity", "ai"]
        )
        assert metrics.correct_categories == 2  # Still 2, not 3
    
    def test_accuracy_calculation(self):
        """Test category accuracy"""
        metrics = CategoryMetrics()
        
        metrics.add_prediction(["ai"], ["ai"])  # Correct
        metrics.add_prediction(["ai"], ["software"])  # Wrong
        metrics.add_prediction(["cybersecurity"], ["cybersecurity"])  # Correct
        
        assert metrics.accuracy == 2/3


class TestRatingMetrics:
    """Test rating agent metrics"""
    
    def test_mae_calculation(self):
        """Test mean absolute error"""
        metrics = RatingMetrics()
        
        # Predicted: 8.0, Expected range: (7.0, 9.0), midpoint: 8.0
        metrics.add_prediction(8.0, (7.0, 9.0))
        # Error: 0.0
        
        # Predicted: 6.0, Expected range: (7.0, 9.0), midpoint: 8.0
        metrics.add_prediction(6.0, (7.0, 9.0))
        # Error: -2.0, abs: 2.0
        
        # Predicted: 9.0, Expected range: (7.0, 9.0), midpoint: 8.0
        metrics.add_prediction(9.0, (7.0, 9.0))
        # Error: +1.0, abs: 1.0
        
        # MAE: (0 + 2.0 + 1.0) / 3 = 1.0
        assert metrics.mae == 1.0
    
    def test_rmse_calculation(self):
        """Test root mean squared error"""
        metrics = RatingMetrics()
        
        metrics.add_prediction(8.0, (7.0, 9.0))  # Error: 0, squared: 0
        metrics.add_prediction(6.0, (7.0, 9.0))  # Error: -2, squared: 4
        metrics.add_prediction(10.0, (7.0, 9.0))  # Error: +2, squared: 4
        
        # RMSE: sqrt((0 + 4 + 4) / 3) = sqrt(8/3) = ~1.633
        assert abs(metrics.rmse - 1.633) < 0.01
    
    def test_recommendation_accuracy(self):
        """Test go/no-go recommendation accuracy"""
        metrics = RatingMetrics()
        
        metrics.add_recommendation("go", "go")  # Correct
        metrics.add_recommendation("no-go", "no-go")  # Correct
        metrics.add_recommendation("go", "no-go")  # Wrong
        
        assert metrics.recommendation_accuracy == 2/3
    
    def test_correlation_calculation(self):
        """Test score correlation"""
        metrics = RatingMetrics()
        
        # Perfect positive correlation
        metrics.add_prediction(2.0, (2.0, 2.0))
        metrics.add_prediction(4.0, (4.0, 4.0))
        metrics.add_prediction(6.0, (6.0, 6.0))
        metrics.add_prediction(8.0, (8.0, 8.0))
        
        # Should have perfect correlation (1.0)
        assert abs(metrics.correlation - 1.0) < 0.01


class TestDocumentMetrics:
    """Test document generator metrics"""
    
    def test_average_calculations(self):
        """Test average score calculations"""
        metrics = DocumentMetrics()
        
        # Add evaluations
        metrics.add_evaluation(
            completeness=8.0,
            relevance=7.5,
            professionalism=9.0,
            technical_depth=7.0,
            overall=8.0
        )
        
        metrics.add_evaluation(
            completeness=6.0,
            relevance=6.5,
            professionalism=7.0,
            technical_depth=5.0,
            overall=6.0
        )
        
        # Check averages
        assert metrics.avg_completeness == 7.0
        assert metrics.avg_relevance == 7.0
        assert metrics.avg_professionalism == 8.0
        assert metrics.avg_technical_depth == 6.0
        assert metrics.avg_overall == 7.0
    
    def test_empty_metrics(self):
        """Test metrics with no data"""
        metrics = DocumentMetrics()
        
        assert metrics.avg_completeness == 0.0
        assert metrics.avg_overall == 0.0


class TestConfidenceCalibration:
    """Test confidence calibration analysis"""
    
    def test_perfect_calibration(self):
        """Test well-calibrated predictions have lower ECE than overconfident"""
        calibration_good = ConfidenceCalibration()
        calibration_bad = ConfidenceCalibration()
        
        # Good calibration: 80% confident → 80% correct
        for _ in range(80):
            calibration_good.add_prediction(0.80, True)
        for _ in range(20):
            calibration_good.add_prediction(0.80, False)
        
        # Bad calibration: 80% confident → 50% correct
        for _ in range(50):
            calibration_bad.add_prediction(0.80, True)
        for _ in range(50):
            calibration_bad.add_prediction(0.80, False)
        
        # Well-calibrated should have lower ECE
        assert calibration_good.expected_calibration_error < calibration_bad.expected_calibration_error
    
    def test_overconfident(self):
        """Test overconfident predictions"""
        calibration = ConfidenceCalibration()
        
        # Says 95% confident but only right 60% of time
        for _ in range(60):
            calibration.add_prediction(0.95, True)
        for _ in range(40):
            calibration.add_prediction(0.95, False)
        
        # Should have high calibration error
        # ECE should be close to |0.95 - 0.60| = 0.35
        assert calibration.expected_calibration_error > 0.20
    
    def test_calibration_curve(self):
        """Test calibration curve generation"""
        calibration = ConfidenceCalibration()
        
        # Add varied predictions
        for i in range(100):
            conf = i / 100
            is_correct = i % 2 == 0  # 50% accuracy across all
            calibration.add_prediction(conf, is_correct)
        
        curve = calibration.get_calibration_curve(num_bins=5)
        
        # Should have multiple bins
        assert len(curve) > 0
        
        # Each bin should have required fields
        for bin_data in curve:
            assert "mean_confidence" in bin_data
            assert "accuracy" in bin_data
            assert "count" in bin_data
            assert "calibration_error" in bin_data


class TestMetricsEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_filter_metrics(self):
        """Test filter metrics with no data"""
        metrics = FilterMetrics()
        
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
        assert metrics.f1_score == 0.0
        assert metrics.accuracy == 0.0
    
    def test_zero_division_protection(self):
        """Ensure no division by zero errors"""
        metrics = FilterMetrics()
        
        # Only false positives (TP = 0)
        metrics.add_prediction(True, False)
        
        # Should not crash, should return 0
        assert metrics.recall == 0.0
    
    def test_rating_with_no_predictions(self):
        """Test rating metrics with empty data"""
        metrics = RatingMetrics()
        
        assert metrics.mae == 0.0
        assert metrics.rmse == 0.0
        assert metrics.correlation == 0.0
        assert metrics.recommendation_accuracy == 0.0
