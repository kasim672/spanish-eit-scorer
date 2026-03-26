"""
eit_scorer/evaluation/metrics.py
===================================
Agreement metrics for comparing automated scores to human rater scores.

Metrics computed:
  Sentence-level:
    accuracy         — exact match %
    cohens_kappa     — unweighted κ
    weighted_kappa   — quadratic-weighted κ (ordinal scores)

  Participant-level (total score):
    mae              — mean absolute error of total scores
    max_abs_diff     — worst-case total score difference
    pct_within_N     — % of participants within N points
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from sklearn.metrics import cohen_kappa_score
    _SKLEARN = True
except ImportError:
    _SKLEARN = False
    logger.warning("scikit-learn not installed — using built-in kappa computation")


# ─────────────────────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────────────────────

@dataclass
class SentenceAgreement:
    n:              int
    accuracy:       float    # Exact match percentage
    cohens_kappa:   float
    weighted_kappa: float
    mae:            float    # Mean absolute error at sentence level

    def summary(self) -> str:
        return (
            f"n={self.n}  accuracy={self.accuracy:.1f}%  "
            f"κ={self.cohens_kappa:.3f}  wκ={self.weighted_kappa:.3f}  "
            f"MAE={self.mae:.3f}"
        )

    @property
    def kappa_label(self) -> str:
        k = self.weighted_kappa
        if k >= 0.80: return "Strong"
        if k >= 0.60: return "Moderate"
        if k >= 0.40: return "Fair"
        if k >= 0.20: return "Slight"
        return "Poor"

    @property
    def meets_90pct_target(self) -> bool:
        return self.accuracy >= 90.0


@dataclass
class TotalAgreement:
    n_participants:  int
    mae:             float
    max_abs_diff:    float
    pct_within_n:    float     # % within the requested threshold
    within_points:   float     # the threshold used

    def summary(self) -> str:
        return (
            f"n_participants={self.n_participants}  "
            f"MAE={self.mae:.2f}  "
            f"max_diff={self.max_abs_diff:.1f}  "
            f"within_{self.within_points}pt={self.pct_within_n:.1f}%"
        )

    @property
    def meets_10pt_target(self) -> bool:
        return self.max_abs_diff < 10.0


# ─────────────────────────────────────────────────────────────
# BUILT-IN KAPPA (no sklearn)
# ─────────────────────────────────────────────────────────────

def _kappa_builtin(y_true: list, y_pred: list, weights: Optional[str] = None) -> float:
    cats = sorted(set(y_true) | set(y_pred))
    k    = len(cats)
    if k < 2:
        return 1.0
    ci   = {c: i for i, c in enumerate(cats)}
    n    = len(y_true)

    conf = [[0.0]*k for _ in range(k)]
    for a, b in zip(y_true, y_pred):
        conf[ci[a]][ci[b]] += 1.0

    rs = [sum(conf[i]) for i in range(k)]
    cs = [sum(conf[r][j] for r in range(k)) for j in range(k)]

    if weights == "quadratic":
        w = [[1 - ((i-j)**2) / max((k-1)**2, 1) for j in range(k)] for i in range(k)]
    elif weights == "linear":
        w = [[1 - abs(i-j) / max(k-1, 1) for j in range(k)] for i in range(k)]
    else:
        w = [[1.0 if i==j else 0.0 for j in range(k)] for i in range(k)]

    p_o = sum(w[i][j]*conf[i][j] for i in range(k) for j in range(k)) / n
    p_e = sum(w[i][j]*rs[i]*cs[j] for i in range(k) for j in range(k)) / (n*n)

    return 1.0 if p_e == 1.0 else (p_o - p_e) / (1.0 - p_e)


def _cohens_kappa(y_true: list, y_pred: list) -> float:
    if _SKLEARN:
        try: return cohen_kappa_score(y_true, y_pred)
        except Exception: pass
    return _kappa_builtin(y_true, y_pred)


def _weighted_kappa(y_true: list, y_pred: list) -> float:
    if _SKLEARN:
        try: return cohen_kappa_score(y_true, y_pred, weights="quadratic")
        except Exception: pass
    return _kappa_builtin(y_true, y_pred, weights="quadratic")


# ─────────────────────────────────────────────────────────────
# SENTENCE-LEVEL AGREEMENT
# ─────────────────────────────────────────────────────────────

def sentence_level_agreement(
    y_true: list[float],
    y_pred: list[float],
) -> SentenceAgreement:
    """
    Compute sentence-level agreement metrics.

    y_true: human adjudicated scores (ground truth)
    y_pred: automated scores
    """
    if not y_true or len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be non-empty lists of equal length")

    n    = len(y_true)
    acc  = sum(1 for a, b in zip(y_true, y_pred) if a == b) / n * 100
    mae  = sum(abs(a - b) for a, b in zip(y_true, y_pred)) / n

    # Convert to int for kappa (rounding to nearest int for ordinal)
    yt_int = [round(v) for v in y_true]
    yp_int = [round(v) for v in y_pred]

    ck  = _cohens_kappa(yt_int, yp_int)
    wk  = _weighted_kappa(yt_int, yp_int)

    return SentenceAgreement(
        n=n, accuracy=acc, cohens_kappa=ck, weighted_kappa=wk, mae=mae
    )


# ─────────────────────────────────────────────────────────────
# PARTICIPANT TOTALS
# ─────────────────────────────────────────────────────────────

def totals_by_participant(
    rows:       list[dict],
    true_field: str = "adjudicated",
    pred_field: str = "score",
) -> tuple[list[float], list[float]]:
    """
    Aggregate predicted and true scores per participant.
    Returns (pred_totals, true_totals) — one value per participant.
    """
    pred_acc: dict[str, float] = {}
    true_acc: dict[str, float] = {}

    for row in rows:
        pid  = row.get("participant_id", "unknown")
        pred = row.get(pred_field, 0)
        true = row.get(true_field, row.get("human_rater_a", 0))
        if true is None:
            continue
        pred_acc[pid] = pred_acc.get(pid, 0.0) + float(pred)
        true_acc[pid] = true_acc.get(pid, 0.0) + float(true)

    pids = sorted(set(pred_acc) & set(true_acc))
    return [pred_acc[p] for p in pids], [true_acc[p] for p in pids]


def total_score_agreement(
    pred_totals: list[float],
    true_totals: list[float],
    within_points: float = 10.0,
) -> TotalAgreement:
    """
    Compute participant-level total score agreement.
    within_points: threshold for the "% within N points" metric.
    """
    if not pred_totals:
        raise ValueError("pred_totals is empty")

    n    = len(pred_totals)
    diffs = [abs(p - t) for p, t in zip(pred_totals, true_totals)]
    mae   = sum(diffs) / n
    max_d = max(diffs)
    pct_w = sum(1 for d in diffs if d <= within_points) / n * 100

    return TotalAgreement(
        n_participants=n,
        mae=mae,
        max_abs_diff=max_d,
        pct_within_n=pct_w,
        within_points=within_points,
    )
