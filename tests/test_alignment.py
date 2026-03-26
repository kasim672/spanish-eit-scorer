"""
tests/test_alignment.py
========================
Tests that alignment is fully reproducible (deterministic tie-breaking).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.alignment import align_tokens, AlignmentConfig

def test_alignment_reproducible_on_ties():
    """Same input must always produce identical ops and cost."""
    cfg = AlignmentConfig()
    ref = ["el","niño","come","una","manzana","roja"]
    hyp = ["el","niño","una","manzana"]
    r1_ops, r1_cost = align_tokens(ref, hyp, cfg)
    r2_ops, r2_cost = align_tokens(ref, hyp, cfg)
    r3_ops, r3_cost = align_tokens(ref, hyp, cfg)
    assert r1_cost == r2_cost == r3_cost
    assert [(o.op, o.ref_token, o.hyp_token) for o in r1_ops] == \
           [(o.op, o.ref_token, o.hyp_token) for o in r2_ops] == \
           [(o.op, o.ref_token, o.hyp_token) for o in r3_ops]

def test_perfect_match_no_gaps():
    cfg = AlignmentConfig()
    tokens = ["el","gato","duerme"]
    ops, cost = align_tokens(tokens, tokens, cfg)
    assert all(o.op == "match" for o in ops)
    assert cost == len(tokens) * cfg.match_score

def test_empty_hyp_all_deletions():
    cfg = AlignmentConfig()
    ref = ["el","gato"]
    ops, _ = align_tokens(ref, [], cfg)
    assert all(o.op == "del" for o in ops)
    assert len(ops) == len(ref)

def test_empty_ref_all_insertions():
    cfg = AlignmentConfig()
    hyp = ["el","gato"]
    ops, _ = align_tokens([], hyp, cfg)
    assert all(o.op == "ins" for o in ops)

def test_single_substitution():
    cfg = AlignmentConfig()
    ref = ["el","perro","corre"]
    hyp = ["el","gato","corre"]
    ops, _ = align_tokens(ref, hyp, cfg)
    sub_ops = [o for o in ops if o.op == "sub"]
    assert len(sub_ops) == 1
    assert sub_ops[0].ref_token == "perro"
    assert sub_ops[0].hyp_token == "gato"

def test_diagonal_preferred_over_gap():
    """Diagonal path is chosen when tied with gap paths."""
    cfg = AlignmentConfig(match_score=1.0, mismatch_penalty=-1.0, gap_penalty=-1.0)
    ref = ["a","b"]
    hyp = ["a","b"]
    ops, _ = align_tokens(ref, hyp, cfg)
    assert all(o.op == "match" for o in ops)
