"""
tests/test_meaning_score.py
=============================
Tests for meaning preservation scoring (coverage, overlap, word order).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.meaning_score import (
    content_overlap_ratio, idea_unit_coverage, word_order_penalty,
    token_overlap_ratio
)
from eit_scorer.core.idea_units import IdeaUnitConfig


def test_token_overlap_perfect():
    """Perfect token overlap."""
    ref = ["el", "niño", "come", "manzana"]
    hyp = ["el", "niño", "come", "manzana"]
    overlap = token_overlap_ratio(ref, hyp)
    assert overlap == 1.0


def test_token_overlap_partial():
    """Partial token overlap."""
    ref = ["el", "niño", "come", "manzana"]
    hyp = ["el", "niño", "come"]
    overlap = token_overlap_ratio(ref, hyp)
    assert overlap == 0.75  # 3/4


def test_token_overlap_empty_hyp():
    """Empty hypothesis."""
    ref = ["el", "niño", "come"]
    hyp = []
    overlap = token_overlap_ratio(ref, hyp)
    assert overlap == 0.0


def test_token_overlap_multiset():
    """Multiset overlap handles repeated tokens."""
    ref = ["gato", "gato", "come"]
    hyp = ["gato", "come"]
    overlap = token_overlap_ratio(ref, hyp)
    assert overlap == 2.0 / 3.0  # 2/3


def test_content_overlap_perfect():
    """Perfect content overlap."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "come", "manzana"]
    hyp = ["el", "niño", "come", "manzana"]
    overlap = content_overlap_ratio(ref, hyp, cfg)
    assert overlap == 1.0


def test_content_overlap_partial():
    """Partial content overlap."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "come", "manzana", "roja"]
    hyp = ["el", "niño", "come"]
    overlap = content_overlap_ratio(ref, hyp, cfg)
    # Content words: ref=[niño, come, manzana, roja], hyp=[niño, come]
    # Overlap: 2/4 = 0.5
    assert overlap == 0.5


def test_idea_unit_coverage_perfect():
    """Perfect idea unit coverage."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "come", "manzana"]
    hyp = ["el", "niño", "come", "manzana"]
    coverage = idea_unit_coverage(ref, hyp, cfg)
    assert coverage == 1.0


def test_idea_unit_coverage_partial():
    """Partial idea unit coverage."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "come", "manzana", "roja"]
    hyp = ["el", "niño", "come"]
    coverage = idea_unit_coverage(ref, hyp, cfg)
    # Content: ref=[niño, come, manzana, roja], hyp=[niño, come]
    # Coverage: 2/4 = 0.5
    assert coverage == 0.5


def test_idea_unit_coverage_with_near_synonyms():
    """Idea unit coverage with near-synonym awareness."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "tiene", "manzana"]
    hyp = ["el", "niño", "tenía", "manzana"]
    coverage = idea_unit_coverage(ref, hyp, cfg)
    # tiene/tenía are near-synonyms, so coverage should be 1.0
    assert coverage == 1.0


def test_word_order_penalty_perfect():
    """Perfect word order (no penalty)."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "come", "manzana"]
    hyp = ["el", "niño", "come", "manzana"]
    penalty = word_order_penalty(ref, hyp, cfg)
    assert penalty == 0.0


def test_word_order_penalty_reordered():
    """Reordered content words incur penalty."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "come", "manzana"]
    hyp = ["manzana", "come", "el", "niño"]
    penalty = word_order_penalty(ref, hyp, cfg)
    # Content: ref=[niño, come, manzana], hyp=[manzana, come, niño]
    # LCS length = 1 (only "come" is in same relative order)
    # Penalty = 1 - (1/3) = 0.667
    assert 0.6 < penalty < 0.7


def test_word_order_penalty_partial_reorder():
    """Partially reordered content."""
    cfg = IdeaUnitConfig()
    ref = ["el", "niño", "come", "manzana"]
    hyp = ["el", "manzana", "niño", "come"]
    penalty = word_order_penalty(ref, hyp, cfg)
    # Content: ref=[niño, come, manzana], hyp=[manzana, niño, come]
    # LCS = [niño, come] or [manzana] (length 2 or 1)
    # Penalty = 1 - (2/3) = 0.333
    assert 0.3 < penalty < 0.4


def test_content_overlap_empty_ref():
    """Empty reference (no content words)."""
    cfg = IdeaUnitConfig()
    ref = ["el", "la", "un"]  # All function words
    hyp = ["el", "niño", "come"]
    overlap = content_overlap_ratio(ref, hyp, cfg)
    assert overlap == 1.0  # Trivially satisfied


def test_idea_unit_coverage_empty_ref():
    """Empty reference (no content words)."""
    cfg = IdeaUnitConfig()
    ref = ["el", "la", "un"]  # All function words
    hyp = ["el", "niño", "come"]
    coverage = idea_unit_coverage(ref, hyp, cfg)
    assert coverage == 1.0  # Trivially satisfied
