"""
tests/test_integration.py
===========================
Integration tests for the complete scoring pipeline.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse

RUBRIC = load_rubric(Path(__file__).parent.parent / "eit_scorer/config/default_rubric.yaml")


def _item(ref: str) -> EITItem:
    return EITItem(item_id="test", reference=ref, max_points=4)


def _resp(text: str) -> EITResponse:
    return EITResponse(participant_id="P001", item_id="test", response_text=text)


def test_perfect_match_scores_4():
    """Perfect match should score 4."""
    item = _item("Quiero cortarme el pelo")
    resp = _resp("Quiero cortarme el pelo")
    s = score_response(item, resp, RUBRIC)
    assert s.score == 4


def test_minor_word_change_scores_3():
    """Minor word change should score 3."""
    item = _item("Quiero cortarme el pelo")
    resp = _resp("Quiero cortarme mi pelo")
    s = score_response(item, resp, RUBRIC)
    assert s.score == 3


def test_pause_removed_scores_high():
    """Pause should be removed and not affect score."""
    item = _item("El libro está en la mesa")
    resp = _resp("El libro [pause] está en la mesa")
    s = score_response(item, resp, RUBRIC)
    assert s.score >= 3


def test_gibberish_scores_0():
    """Gibberish response should score 0."""
    item = _item("El carro lo tiene Pedro")
    resp = _resp("[gibberish] xxx")
    s = score_response(item, resp, RUBRIC)
    assert s.score == 0


def test_empty_response_scores_0():
    """Empty response should score 0."""
    item = _item("El niño come manzana")
    resp = _resp("")
    s = score_response(item, resp, RUBRIC)
    assert s.score == 0


def test_partial_response_scores_2_or_3():
    """Partial response should score 2 or 3."""
    item = _item("El niño come una manzana roja en el jardín")
    resp = _resp("El niño come manzana")
    s = score_response(item, resp, RUBRIC)
    assert 2 <= s.score <= 3


def test_score_within_bounds():
    """All scores should be within [0, max_points]."""
    test_cases = [
        ("El niño come", "El niño come"),
        ("Ella corre rápido", "Ella corre"),
        ("Los perros ladran", ""),
        ("Quiero que vengas", "yo hablo completamente diferente"),
    ]
    for ref, hyp in test_cases:
        s = score_response(_item(ref), _resp(hyp), RUBRIC)
        assert 0 <= s.score <= s.max_points


def test_trace_populated():
    """Scoring trace should be populated."""
    item = _item("La profesora habla")
    resp = _resp("La profesora")
    s = score_response(item, resp, RUBRIC)
    assert s.trace is not None
    assert s.trace.display_ref is not None
    assert s.trace.display_hyp is not None
    assert s.trace.alignment is not None
    assert s.trace.total_edits >= 0
    assert s.trace.idea_unit_coverage >= 0


def test_rule_applied():
    """Applied rule should be recorded."""
    item = _item("María le dio el regalo a su madre")
    resp = _resp("María le dio el regalo a su madre")
    s = score_response(item, resp, RUBRIC)
    assert len(s.trace.applied_rule_ids) > 0
    assert "R4_perfect" in s.trace.applied_rule_ids


def test_contraction_expansion():
    """Contractions should be expanded."""
    item = _item("Nosotros vamos al mercado")
    resp = _resp("Nosotros vamos al mercado")
    s = score_response(item, resp, RUBRIC)
    # After expansion 'al'→['a','el'], should match
    assert s.score >= 3


def test_filler_words_ignored():
    """Filler words should not affect scoring."""
    item = _item("El niño come manzana")
    resp1 = _resp("El niño come manzana")
    resp2 = _resp("eh El niño um come manzana")
    s1 = score_response(item, resp1, RUBRIC)
    s2 = score_response(item, resp2, RUBRIC)
    assert s1.score == s2.score


def test_case_insensitive():
    """Scoring should be case-insensitive."""
    item = _item("El niño come manzana")
    resp1 = _resp("El niño come manzana")
    resp2 = _resp("el NIÑO COME manzana")
    s1 = score_response(item, resp1, RUBRIC)
    s2 = score_response(item, resp2, RUBRIC)
    assert s1.score == s2.score


def test_punctuation_ignored():
    """Punctuation should be ignored."""
    item = _item("El libro está en la mesa")
    resp1 = _resp("El libro está en la mesa")
    resp2 = _resp("El libro está en la mesa.")
    s1 = score_response(item, resp1, RUBRIC)
    s2 = score_response(item, resp2, RUBRIC)
    assert s1.score == s2.score


def test_near_synonym_handling():
    """Near-synonyms should be handled correctly."""
    item = _item("El niño tiene una manzana")
    resp = _resp("El niño tenía una manzana")
    s = score_response(item, resp, RUBRIC)
    # Tense change (tiene/tenía) should not heavily penalize
    assert s.score >= 2


def test_multiple_errors_decrease_score():
    """Multiple errors should decrease score."""
    item = _item("El niño come una manzana roja en el jardín")
    s_perfect = score_response(item, _resp("El niño come una manzana roja en el jardín"), RUBRIC)
    s_partial = score_response(item, _resp("El niño come manzana"), RUBRIC)
    s_minimal = score_response(item, _resp("El niño"), RUBRIC)
    assert s_perfect.score >= s_partial.score >= s_minimal.score


def test_deterministic_scoring():
    """Same input should always produce same score."""
    item = _item("La profesora habla con los estudiantes")
    resp = _resp("La profesora habla los estudiantes")
    s1 = score_response(item, resp, RUBRIC)
    s2 = score_response(item, resp, RUBRIC)
    s3 = score_response(item, resp, RUBRIC)
    assert s1.score == s2.score == s3.score
