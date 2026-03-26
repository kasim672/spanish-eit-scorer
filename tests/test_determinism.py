"""
tests/test_determinism.py
===========================
Guarantees that scoring is fully deterministic:
  - same input → same score
  - same input → same fingerprint
  - fingerprint changes if input changes
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.rubric    import load_rubric
from eit_scorer.core.scoring   import score_response
from eit_scorer.data.models    import EITItem, EITResponse

RUBRIC = load_rubric(Path(__file__).parent.parent / "eit_scorer/config/default_rubric.yaml")

def _item(ref: str) -> EITItem:
    return EITItem(item_id="test", reference=ref, max_points=4)

def _resp(text: str) -> EITResponse:
    return EITResponse(participant_id="P001", item_id="test", response_text=text)


def test_same_input_same_score():
    item = _item("El niño come una manzana roja")
    resp = _resp("El niño come manzana")
    s1 = score_response(item, resp, RUBRIC)
    s2 = score_response(item, resp, RUBRIC)
    s3 = score_response(item, resp, RUBRIC)
    assert s1.score == s2.score == s3.score


def test_same_input_same_fingerprint():
    item = _item("La profesora habla con los estudiantes")
    resp = _resp("La profesora habla los estudiantes")
    s1 = score_response(item, resp, RUBRIC)
    s2 = score_response(item, resp, RUBRIC)
    assert s1.trace.deterministic_fingerprint == s2.trace.deterministic_fingerprint


def test_different_input_different_fingerprint():
    item  = _item("El gato duerme mucho")
    resp1 = _resp("El gato duerme mucho")
    resp2 = _resp("El perro duerme mucho")
    s1 = score_response(item, resp1, RUBRIC)
    s2 = score_response(item, resp2, RUBRIC)
    assert s1.trace.deterministic_fingerprint != s2.trace.deterministic_fingerprint


def test_perfect_response_scores_max():
    item = _item("El niño come una manzana")
    resp = _resp("El niño come una manzana")
    s = score_response(item, resp, RUBRIC)
    assert s.score == 4
    assert s.trace.total_edits == 0


def test_empty_response_scores_zero():
    item = _item("El niño come una manzana")
    resp = _resp("")
    s = score_response(item, resp, RUBRIC)
    assert s.score == 0


def test_score_within_bounds():
    cases = [
        ("El niño come",      "El niño come"),
        ("Ella corre rápido", "Ella corre"),
        ("Los perros ladran", ""),
        ("Quiero que vengas", "yo hablo completamente diferente"),
    ]
    for ref, hyp in cases:
        s = score_response(_item(ref), _resp(hyp), RUBRIC)
        assert 0 <= s.score <= s.max_points, f"Score {s.score} out of bounds for '{hyp}'"


def test_audit_trail_populated():
    item = _item("La profesora habla")
    resp = _resp("La profesora")
    s = score_response(item, resp, RUBRIC)
    trail = s.trace.audit()
    assert any("REF" in line for line in trail)
    assert any("SCORE" in line for line in trail)
    assert any("FINGERPRINT" in line for line in trail)


def test_rule_r4_fires_on_perfect():
    item = _item("María le dio el regalo a su madre")
    resp = _resp("María le dio el regalo a su madre")
    s = score_response(item, resp, RUBRIC)
    assert "R4_perfect" in s.trace.applied_rule_ids


def test_rule_r0_fires_on_empty():
    item = _item("El gato duerme mucho")
    resp = _resp("")
    s = score_response(item, resp, RUBRIC)
    assert any("R0" in r for r in s.trace.applied_rule_ids)


def test_contraction_expansion():
    """'al' should expand to 'a el' before alignment."""
    item = _item("Nosotros vamos al mercado")
    resp = _resp("Nosotros vamos al mercado")
    s = score_response(item, resp, RUBRIC)
    # After expansion 'al'→['a','el'], perfect match should still fire
    assert s.score == 4


def test_filler_word_stripped():
    """Filler words (eh, um) should not affect scoring."""
    item  = _item("El niño come manzana")
    resp1 = _resp("El niño come manzana")
    resp2 = _resp("eh El niño um come manzana")
    s1 = score_response(item, resp1, RUBRIC)
    s2 = score_response(item, resp2, RUBRIC)
    assert s1.score == s2.score


def test_score_decreases_with_more_errors():
    item  = _item("El niño come una manzana roja en el jardín")
    s_perfect = score_response(item, _resp("El niño come una manzana roja en el jardín"), RUBRIC)
    s_partial  = score_response(item, _resp("El niño come manzana"), RUBRIC)
    s_empty    = score_response(item, _resp(""), RUBRIC)
    assert s_perfect.score >= s_partial.score >= s_empty.score
