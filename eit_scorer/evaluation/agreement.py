"""
eit_scorer/evaluation/agreement.py
====================================
Research-grade agreement evaluation layer.

Measures alignment between automated scoring and human judgment using:
- Cohen's Kappa (primary metric for inter-rater reliability)
- Accuracy (exact match rate)
- Mean Absolute Error (MAE)
- Weighted Kappa (for ordinal scores)

This module provides validation that the scoring system is reliable
and scientifically credible for research use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from sklearn.metrics import cohen_kappa_score
    _SKLEARN = True
except ImportError:
    _SKLEARN = False


# ─────────────────────────────────────────────────────────────
# KAPPA COMPUTATION (with/without sklearn)
# ─────────────────────────────────────────────────────────────

def _kappa_builtin(
    y_true: list[int],
    y_pred: list[int],
    weights: Optional[str] = None,
) -> float:
    """
    Compute Cohen's Kappa without sklearn.
    
    Supports:
    - Unweighted (nominal): κ = (p_o - p_e) / (1 - p_e)
    - Quadratic-weighted (ordinal): accounts for distance between categories
    - Linear-weighted: linear distance between categories
    """
    cats = sorted(set(y_true) | set(y_pred))
    k = len(cats)
    if k < 2:
        return 1.0
    
    ci = {c: i for i, c in enumerate(cats)}
    n = len(y_true)
    
    # Build confusion matrix
    conf = [[0.0] * k for _ in range(k)]
    for a, b in zip(y_true, y_pred):
        conf[ci[a]][ci[b]] += 1.0
    
    # Marginal totals
    rs = [sum(conf[i]) for i in range(k)]
    cs = [sum(conf[r][j] for r in range(k)) for j in range(k)]
    
    # Weight matrix
    if weights == "quadratic":
        w = [[1.0 - ((i - j) ** 2) / max((k - 1) ** 2, 1) for j in range(k)] for i in range(k)]
    elif weights == "linear":
        w = [[1.0 - abs(i - j) / max(k - 1, 1) for j in range(k)] for i in range(k)]
    else:
        w = [[1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
    
    # Observed agreement
    p_o = sum(w[i][j] * conf[i][j] for i in range(k) for j in range(k)) / n
    
    # Expected agreement
    p_e = sum(w[i][j] * rs[i] * cs[j] for i in range(k) for j in range(k)) / (n * n)
    
    # Cohen's Kappa
    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1.0 - p_e)


def compute_cohens_kappa(y_true: list[int], y_pred: list[int]) -> float:
    """Compute unweighted Cohen's Kappa."""
    if _SKLEARN:
        try:
            return cohen_kappa_score(y_true, y_pred)
        except Exception:
            pass
    return _kappa_builtin(y_true, y_pred)


def compute_weighted_kappa(y_true: list[int], y_pred: list[int]) -> float:
    """Compute quadratic-weighted Cohen's Kappa (for ordinal scores)."""
    if _SKLEARN:
        try:
            return cohen_kappa_score(y_true, y_pred, weights="quadratic")
        except Exception:
            pass
    return _kappa_builtin(y_true, y_pred, weights="quadratic")


# ─────────────────────────────────────────────────────────────
# INTERPRETATION HELPERS
# ─────────────────────────────────────────────────────────────

def interpret_kappa(kappa: float) -> str:
    """
    Interpret Cohen's Kappa value.
    
    Landis & Koch (1977) scale:
    < 0.0   → Poor (less than chance)
    0.0–0.2 → Slight agreement
    0.2–0.4 → Fair agreement
    0.4–0.6 → Moderate agreement
    0.6–0.8 → Substantial agreement
    0.8–1.0 → Almost perfect agreement
    """
    if kappa < 0.0:
        return "Poor (less than chance)"
    elif kappa < 0.2:
        return "Slight agreement"
    elif kappa < 0.4:
        return "Fair agreement"
    elif kappa < 0.6:
        return "Moderate agreement"
    elif kappa < 0.8:
        return "Substantial agreement"
    else:
        return "Almost perfect agreement"


def interpret_accuracy(accuracy: float) -> str:
    """Interpret accuracy percentage."""
    if accuracy >= 90:
        return "Excellent (≥90%)"
    elif accuracy >= 80:
        return "Good (80–90%)"
    elif accuracy >= 70:
        return "Fair (70–80%)"
    elif accuracy >= 60:
        return "Acceptable (60–70%)"
    else:
        return "Poor (<60%)"


def interpret_mae(mae: float, max_score: int = 4) -> str:
    """Interpret Mean Absolute Error."""
    pct_of_scale = (mae / max_score) * 100
    if mae < 0.3:
        return f"Excellent ({mae:.2f}, {pct_of_scale:.1f}% of scale)"
    elif mae < 0.5:
        return f"Good ({mae:.2f}, {pct_of_scale:.1f}% of scale)"
    elif mae < 0.8:
        return f"Fair ({mae:.2f}, {pct_of_scale:.1f}% of scale)"
    else:
        return f"Poor ({mae:.2f}, {pct_of_scale:.1f}% of scale)"


# ─────────────────────────────────────────────────────────────
# AGREEMENT DATACLASS
# ─────────────────────────────────────────────────────────────

@dataclass
class AgreementMetrics:
    """Comprehensive agreement metrics between automated and human scores."""
    
    n_samples: int
    accuracy: float  # Exact match percentage
    cohens_kappa: float  # Unweighted
    weighted_kappa: float  # Quadratic-weighted (ordinal)
    mae: float  # Mean absolute error
    
    def summary(self) -> str:
        """Return a concise summary."""
        return (
            f"n={self.n_samples} | "
            f"Accuracy={self.accuracy:.1f}% | "
            f"κ={self.cohens_kappa:.3f} | "
            f"wκ={self.weighted_kappa:.3f} | "
            f"MAE={self.mae:.3f}"
        )
    
    def detailed_report(self) -> str:
        """Return a detailed, human-readable report."""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║           AGREEMENT EVALUATION REPORT                      ║",
            "╚════════════════════════════════════════════════════════════╝",
            "",
            f"Sample Size: {self.n_samples} responses",
            "",
            "─ ACCURACY (Exact Match Rate) ─",
            f"  {self.accuracy:.1f}%",
            f"  Interpretation: {interpret_accuracy(self.accuracy)}",
            "",
            "─ COHEN'S KAPPA (Unweighted) ─",
            f"  κ = {self.cohens_kappa:.3f}",
            f"  Interpretation: {interpret_kappa(self.cohens_kappa)}",
            "",
            "─ WEIGHTED KAPPA (Ordinal, Quadratic) ─",
            f"  wκ = {self.weighted_kappa:.3f}",
            f"  Interpretation: {interpret_kappa(self.weighted_kappa)}",
            "",
            "─ MEAN ABSOLUTE ERROR ─",
            f"  MAE = {self.mae:.3f}",
            f"  Interpretation: {interpret_mae(self.mae)}",
            "",
            "─ RESEARCH VALIDITY ─",
            self._validity_assessment(),
            "",
            "╚════════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)
    
    def _validity_assessment(self) -> str:
        """Assess research validity based on metrics."""
        criteria = []
        
        # Accuracy criterion
        if self.accuracy >= 85:
            criteria.append("✓ Accuracy ≥85% (strong)")
        elif self.accuracy >= 75:
            criteria.append("◐ Accuracy 75–85% (acceptable)")
        else:
            criteria.append("✗ Accuracy <75% (weak)")
        
        # Kappa criterion
        if self.weighted_kappa >= 0.70:
            criteria.append("✓ Weighted κ ≥0.70 (substantial)")
        elif self.weighted_kappa >= 0.50:
            criteria.append("◐ Weighted κ 0.50–0.70 (moderate)")
        else:
            criteria.append("✗ Weighted κ <0.50 (weak)")
        
        # MAE criterion
        if self.mae < 0.5:
            criteria.append("✓ MAE <0.5 (excellent)")
        elif self.mae < 0.8:
            criteria.append("◐ MAE 0.5–0.8 (good)")
        else:
            criteria.append("✗ MAE ≥0.8 (weak)")
        
        # Overall assessment
        strong_count = sum(1 for c in criteria if c.startswith("✓"))
        if strong_count == 3:
            overall = "RESEARCH-VALID: System demonstrates strong agreement with human raters"
        elif strong_count >= 2:
            overall = "ACCEPTABLE: System shows reasonable agreement; suitable for research with caveats"
        else:
            overall = "NEEDS IMPROVEMENT: System requires refinement before research use"
        
        return "\n".join(criteria) + f"\n\n  {overall}"


# ─────────────────────────────────────────────────────────────
# MAIN EVALUATION FUNCTION
# ─────────────────────────────────────────────────────────────

def evaluate_agreement(
    y_true: list[int | float],
    y_pred: list[int | float],
) -> AgreementMetrics:
    """
    Evaluate agreement between human and automated scores.
    
    Args:
        y_true: Human-assigned scores (ground truth)
        y_pred: Automated scores
    
    Returns:
        AgreementMetrics with comprehensive agreement statistics
    
    Raises:
        ValueError: If inputs are invalid or mismatched
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred must be non-empty")
    
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")
    
    n = len(y_true)
    
    # Convert to integers for kappa computation
    y_true_int = [int(round(v)) for v in y_true]
    y_pred_int = [int(round(v)) for v in y_pred]
    
    # Compute metrics
    accuracy = sum(1 for a, b in zip(y_true_int, y_pred_int) if a == b) / n * 100
    mae = sum(abs(a - b) for a, b in zip(y_true, y_pred)) / n
    kappa = compute_cohens_kappa(y_true_int, y_pred_int)
    weighted_kappa = compute_weighted_kappa(y_true_int, y_pred_int)
    
    return AgreementMetrics(
        n_samples=n,
        accuracy=accuracy,
        cohens_kappa=kappa,
        weighted_kappa=weighted_kappa,
        mae=mae,
    )


# ─────────────────────────────────────────────────────────────
# BATCH EVALUATION (for multiple datasets)
# ─────────────────────────────────────────────────────────────

@dataclass
class BatchEvaluationResults:
    """Results from evaluating multiple datasets."""
    
    datasets: dict[str, AgreementMetrics]
    overall: AgreementMetrics
    
    def summary(self) -> str:
        """Return summary of all datasets."""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║           BATCH EVALUATION SUMMARY                         ║",
            "╚════════════════════════════════════════════════════════════╝",
            "",
        ]
        
        for name, metrics in self.datasets.items():
            lines.append(f"{name}:")
            lines.append(f"  {metrics.summary()}")
            lines.append("")
        
        lines.append("OVERALL:")
        lines.append(f"  {self.overall.summary()}")
        lines.append("")
        
        return "\n".join(lines)


def evaluate_batch(
    datasets: dict[str, tuple[list[int | float], list[int | float]]],
) -> BatchEvaluationResults:
    """
    Evaluate agreement across multiple datasets.
    
    Args:
        datasets: Dict mapping dataset_name → (y_true, y_pred)
    
    Returns:
        BatchEvaluationResults with per-dataset and overall metrics
    """
    results = {}
    all_true = []
    all_pred = []
    
    for name, (y_true, y_pred) in datasets.items():
        metrics = evaluate_agreement(y_true, y_pred)
        results[name] = metrics
        all_true.extend(y_true)
        all_pred.extend(y_pred)
    
    overall = evaluate_agreement(all_true, all_pred)
    
    return BatchEvaluationResults(datasets=results, overall=overall)
