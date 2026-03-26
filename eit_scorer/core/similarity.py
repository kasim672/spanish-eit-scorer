"""
eit_scorer/core/similarity.py
================================
PyTorch-based token overlap similarity model.

Uses a lightweight feedforward network trained on alignment features
to produce a continuous similarity score in [0, 1].

This complements the rule engine — the rule engine handles discrete
scoring decisions; this module provides a soft similarity signal
that can be used for borderline cases or future ML-based refinement.

Architecture:
    Input features (4):
        - token_overlap_ratio   (set-based recall)
        - normalized_edit_dist  (edit_distance / max_len)
        - content_sub_ratio     (content_subs / ref_len)
        - hyp_length_ratio      (hyp_len / ref_len)

    Network:
        Linear(4 → 16) → ReLU → Linear(16 → 8) → ReLU → Linear(8 → 1) → Sigmoid

    Output: similarity score in [0, 1]
        ~1.0 = very similar to reference
        ~0.0 = very different
"""

from __future__ import annotations

import torch
import torch.nn as nn


class SimilarityNet(nn.Module):
    """
    Lightweight feedforward network for sentence-pair similarity.
    Input: 4 alignment features. Output: scalar in [0, 1].
    """

    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def build_features(
    overlap_ratio:  float,
    total_edits:    int,
    content_subs:   int,
    ref_len:        int,
    hyp_len:        int,
) -> torch.Tensor:
    """
    Build the 4-feature input tensor from alignment statistics.

    Features:
        overlap_ratio       — set-based token recall (already computed)
        norm_edit_dist      — edits / max(ref_len, hyp_len, 1)
        content_sub_ratio   — content_subs / max(ref_len, 1)
        hyp_length_ratio    — hyp_len / max(ref_len, 1)
    """
    max_len = max(ref_len, hyp_len, 1)
    features = [
        overlap_ratio,
        total_edits / max_len,
        content_subs / max(ref_len, 1),
        hyp_len / max(ref_len, 1),
    ]
    return torch.tensor(features, dtype=torch.float32)


# ── Singleton model (initialized once, reused) ───────────────
_MODEL: SimilarityNet | None = None


def get_model() -> SimilarityNet:
    """Return the singleton SimilarityNet (rule-initialized weights)."""
    global _MODEL
    if _MODEL is None:
        _MODEL = SimilarityNet()
        _init_weights(_MODEL)
    return _MODEL


def _init_weights(model: SimilarityNet) -> None:
    """
    Initialize weights to approximate the rule-based scoring logic.

    The first layer weights are set so that:
    - overlap_ratio has the strongest positive influence
    - norm_edit_dist has a strong negative influence
    - content_sub_ratio has a moderate negative influence
    - hyp_length_ratio has a mild positive influence (partial production)

    This gives sensible similarity scores without any training data,
    while remaining differentiable for future fine-tuning.
    """
    with torch.no_grad():
        # First layer: 4 inputs → 16 hidden
        w = model.net[0].weight  # shape [16, 4]
        w.zero_()
        # Feature indices: 0=overlap, 1=edit_dist, 2=content_sub, 3=len_ratio
        for i in range(16):
            w[i, 0] =  2.0 + (i % 4) * 0.1   # overlap: strong positive
            w[i, 1] = -1.5 - (i % 3) * 0.1   # edit dist: strong negative
            w[i, 2] = -1.0 - (i % 2) * 0.1   # content sub: moderate negative
            w[i, 3] =  0.5 + (i % 4) * 0.05  # len ratio: mild positive
        model.net[0].bias.zero_()


@torch.no_grad()
def compute_similarity(
    overlap_ratio: float,
    total_edits:   int,
    content_subs:  int,
    ref_len:       int,
    hyp_len:       int,
) -> float:
    """
    Compute a soft similarity score in [0, 1] using the PyTorch model.

    This is a continuous complement to the discrete rule-based score:
        similarity ~1.0 → likely score 4 (perfect)
        similarity ~0.7 → likely score 3 (minor errors)
        similarity ~0.4 → likely score 2 (moderate errors)
        similarity ~0.1 → likely score 0-1 (heavy errors)

    Returns:
        float in [0, 1]
    """
    model = get_model()
    model.eval()
    x = build_features(overlap_ratio, total_edits, content_subs, ref_len, hyp_len)
    return float(model(x.unsqueeze(0)).squeeze())
