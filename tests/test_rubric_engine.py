"""
tests/test_rubric_engine.py
=============================
Tests for the rule-based rubric scoring engine.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.rubric_engine import (
    RubricRule, RubricEngine, create_ortega_2000_engine
)


def test_rubric_engine_creation():
    """Create Ortega 2000 rubric engine."""
    engine = create_ortega_2000_engine()
    assert engine.max_points == 4
    assert len(engine.rules) > 0


def test_rule_matching_exact():
    """Test exact condition matching."""
    rule = RubricRule(
        rule_id="test",
        description="Test rule",
        conditions={"max_total_edits": 0},
        score=4,
    )
    engine = RubricEngine(rules=[rule])
    
    features = {"total_edits": 0}
    score, rule_id = engine.score(features)
    assert score == 4
    assert rule_id == "test"


def test_rule_matching_threshold():
    """Test threshold-based condition matching."""
    rule = RubricRule(
        rule_id="test",
        description="Test rule",
        conditions={"min_idea_unit_coverage": 0.8},
        score=3,
    )
    engine = RubricEngine(rules=[rule])
    
    features = {"idea_unit_coverage": 0.85}
    score, rule_id = engine.score(features)
    assert score == 3


def test_rule_not_matching():
    """Test when rule conditions don't match."""
    rule = RubricRule(
        rule_id="test",
        description="Test rule",
        conditions={"max_total_edits": 0},
        score=4,
    )
    engine = RubricEngine(rules=[rule])
    
    features = {"total_edits": 5}
    score, rule_id = engine.score(features)
    assert score == 0  # Fallback score
    assert rule_id == "_no_match"


def test_first_rule_wins():
    """First matching rule wins (order matters)."""
    rule1 = RubricRule(
        rule_id="rule1",
        description="First rule",
        conditions={"min_idea_unit_coverage": 0.5},
        score=2,
    )
    rule2 = RubricRule(
        rule_id="rule2",
        description="Second rule",
        conditions={"min_idea_unit_coverage": 0.5},
        score=3,
    )
    engine = RubricEngine(rules=[rule1, rule2])
    
    features = {"idea_unit_coverage": 0.75}
    score, rule_id = engine.score(features)
    assert score == 2
    assert rule_id == "rule1"


def test_multiple_conditions_all_must_match():
    """All conditions must match (AND logic)."""
    rule = RubricRule(
        rule_id="test",
        description="Test rule",
        conditions={
            "max_total_edits": 3,
            "min_idea_unit_coverage": 0.8,
        },
        score=3,
    )
    engine = RubricEngine(rules=[rule])
    
    # Both conditions satisfied
    features = {"total_edits": 2, "idea_unit_coverage": 0.85}
    score, rule_id = engine.score(features)
    assert score == 3
    
    # One condition fails
    features = {"total_edits": 5, "idea_unit_coverage": 0.85}
    score, rule_id = engine.score(features)
    assert score == 0


def test_ortega_perfect_match():
    """Ortega engine: perfect match scores 4."""
    engine = create_ortega_2000_engine()
    features = {"total_edits": 0}
    score, rule_id = engine.score(features)
    assert score == 4
    assert "R4" in rule_id


def test_ortega_gibberish():
    """Ortega engine: gibberish scores 0."""
    engine = create_ortega_2000_engine()
    features = {"is_gibberish": True}
    score, rule_id = engine.score(features)
    assert score == 0
    assert "R0" in rule_id


def test_ortega_empty_response():
    """Ortega engine: empty response scores 0."""
    engine = create_ortega_2000_engine()
    features = {"hyp_min_tokens_lt": 2}
    score, rule_id = engine.score(features)
    assert score == 0


def test_ortega_meaning_preserved():
    """Ortega engine: meaning preserved scores 3."""
    engine = create_ortega_2000_engine()
    features = {
        "total_edits": 2,
        "content_subs": 0,
        "idea_unit_coverage": 0.85,
    }
    score, rule_id = engine.score(features)
    assert score == 3
    assert "R3" in rule_id


def test_ortega_partial_meaning():
    """Ortega engine: partial meaning (>50%) scores 2."""
    engine = create_ortega_2000_engine()
    features = {
        "idea_unit_coverage": 0.60,
        "content_subs": 1,
        "length_ratio": 0.50,
    }
    score, rule_id = engine.score(features)
    assert score == 2
    assert "R2" in rule_id


def test_ortega_minimal_meaning():
    """Ortega engine: minimal meaning (<50%) scores 1."""
    engine = create_ortega_2000_engine()
    features = {
        "idea_unit_coverage": 0.25,
        "content_overlap": 0.20,
        "hyp_min_tokens": 3,
    }
    score, rule_id = engine.score(features)
    assert score == 1
    assert "R1" in rule_id
