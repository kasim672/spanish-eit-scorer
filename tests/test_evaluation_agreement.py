"""
tests/test_evaluation_agreement.py
====================================
Tests for the evaluation agreement layer.

Validates Cohen's Kappa, Accuracy, MAE, and interpretation logic.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.evaluation.agreement import (
    evaluate_agreement, compute_cohens_kappa, compute_weighted_kappa,
    interpret_kappa, interpret_accuracy, interpret_mae,
    evaluate_batch, AgreementMetrics
)


def test_perfect_agreement():
    """Perfect agreement should give 100% accuracy and κ=1.0."""
    y_true = [4, 3, 2, 1, 0, 4, 3, 2]
    y_pred = [4, 3, 2, 1, 0, 4, 3, 2]
    
    metrics = evaluate_agreement(y_true, y_pred)
    assert metrics.accuracy == 100.0
    assert abs(metrics.cohens_kappa - 1.0) < 1e-9
    assert abs(metrics.weighted_kappa - 1.0) < 1e-9
    assert metrics.mae == 0.0


def test_no_agreement():
    """Completely opposite predictions."""
    y_true = [4, 4, 4, 4]
    y_pred = [0, 0, 0, 0]
    
    metrics = evaluate_agreement(y_true, y_pred)
    assert metrics.accuracy == 0.0
    assert metrics.mae == 4.0


def test_partial_agreement():
    """Partial agreement with some errors."""
    y_true = [4, 3, 2, 1, 0]
    y_pred = [4, 3, 2, 2, 0]  # One error (1→2)
    
    metrics = evaluate_agreement(y_true, y_pred)
    assert metrics.accuracy == 80.0  # 4/5
    assert metrics.mae == 0.2  # (0+0+0+1+0)/5


def test_mae_computation():
    """Mean Absolute Error computation."""
    y_true = [4.0, 3.0, 2.0, 1.0]
    y_pred = [4.0, 2.0, 2.0, 2.0]
    
    metrics = evaluate_agreement(y_true, y_pred)
    # Errors: 0, 1, 0, 1 → MAE = 2/4 = 0.5
    assert metrics.mae == 0.5


def test_cohens_kappa_perfect():
    """Cohen's Kappa for perfect agreement."""
    y_true = [1, 1, 2, 2, 3, 3]
    y_pred = [1, 1, 2, 2, 3, 3]
    
    kappa = compute_cohens_kappa(y_true, y_pred)
    assert abs(kappa - 1.0) < 1e-9


def test_cohens_kappa_chance():
    """Cohen's Kappa for chance agreement."""
    # Balanced distribution, random predictions
    y_true = [1, 1, 2, 2]
    y_pred = [1, 2, 1, 2]
    
    kappa = compute_cohens_kappa(y_true, y_pred)
    # Should be close to 0 (chance level)
    assert -0.1 < kappa < 0.1


def test_weighted_kappa():
    """Weighted Kappa for ordinal scores."""
    y_true = [4, 3, 2, 1, 0]
    y_pred = [4, 3, 2, 1, 0]
    
    wkappa = compute_weighted_kappa(y_true, y_pred)
    assert abs(wkappa - 1.0) < 1e-9


def test_interpret_kappa():
    """Kappa interpretation."""
    assert "perfect" in interpret_kappa(0.95).lower()
    assert "Substantial" in interpret_kappa(0.75)
    assert "Moderate" in interpret_kappa(0.55)
    assert "Fair" in interpret_kappa(0.35)
    assert "Slight" in interpret_kappa(0.15)
    assert "Poor" in interpret_kappa(-0.1)


def test_interpret_accuracy():
    """Accuracy interpretation."""
    assert "Excellent" in interpret_accuracy(95)
    assert "Good" in interpret_accuracy(85)
    assert "Fair" in interpret_accuracy(75)
    assert "Acceptable" in interpret_accuracy(65)
    assert "Poor" in interpret_accuracy(50)


def test_interpret_mae():
    """MAE interpretation."""
    assert "Excellent" in interpret_mae(0.2)
    assert "Good" in interpret_mae(0.4)
    assert "Fair" in interpret_mae(0.6)
    assert "Poor" in interpret_mae(1.0)


def test_agreement_metrics_summary():
    """AgreementMetrics summary generation."""
    metrics = AgreementMetrics(
        n_samples=100,
        accuracy=85.0,
        cohens_kappa=0.75,
        weighted_kappa=0.78,
        mae=0.35,
    )
    
    summary = metrics.summary()
    assert "100" in summary
    assert "85.0" in summary
    assert "0.75" in summary


def test_agreement_metrics_detailed_report():
    """AgreementMetrics detailed report generation."""
    metrics = AgreementMetrics(
        n_samples=100,
        accuracy=85.0,
        cohens_kappa=0.75,
        weighted_kappa=0.78,
        mae=0.35,
    )
    
    report = metrics.detailed_report()
    assert "AGREEMENT EVALUATION REPORT" in report
    assert "Accuracy" in report
    assert "KAPPA" in report
    assert "RESEARCH VALIDITY" in report


def test_evaluate_batch():
    """Batch evaluation across multiple datasets."""
    datasets = {
        "dataset1": ([4, 3, 2, 1], [4, 3, 2, 1]),
        "dataset2": ([4, 3, 2], [4, 3, 2]),
    }
    
    results = evaluate_batch(datasets)
    assert len(results.datasets) == 2
    assert results.overall.n_samples == 7
    assert results.overall.accuracy == 100.0


def test_error_handling_empty_lists():
    """Error handling for empty lists."""
    try:
        evaluate_agreement([], [])
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_error_handling_mismatched_lengths():
    """Error handling for mismatched lengths."""
    try:
        evaluate_agreement([1, 2, 3], [1, 2])
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_float_to_int_conversion():
    """Float scores should be rounded to integers for kappa."""
    y_true = [4.1, 3.2, 2.8, 1.1]
    y_pred = [4.0, 3.0, 3.0, 1.0]
    
    metrics = evaluate_agreement(y_true, y_pred)
    # After rounding: y_true=[4,3,3,1], y_pred=[4,3,3,1]
    assert metrics.accuracy == 100.0


def test_research_validity_assessment():
    """Research validity assessment in detailed report."""
    # Strong metrics
    strong_metrics = AgreementMetrics(
        n_samples=100,
        accuracy=90.0,
        cohens_kappa=0.80,
        weighted_kappa=0.82,
        mae=0.3,
    )
    
    report = strong_metrics.detailed_report()
    assert "RESEARCH-VALID" in report
    
    # Weak metrics
    weak_metrics = AgreementMetrics(
        n_samples=100,
        accuracy=60.0,
        cohens_kappa=0.30,
        weighted_kappa=0.32,
        mae=1.2,
    )
    
    report = weak_metrics.detailed_report()
    assert "NEEDS IMPROVEMENT" in report
