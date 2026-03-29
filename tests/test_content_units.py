"""
tests/test_content_units.py
=============================
Tests for content word extraction and idea unit analysis.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.idea_units import (
    IdeaUnitConfig, extract_content_tokens, extract_function_tokens,
    count_idea_units, is_near_synonym, get_near_synonyms
)


def test_extract_content_tokens():
    """Extract content words from sentence."""
    cfg = IdeaUnitConfig()
    tokens = ["el", "niño", "come", "una", "manzana", "roja"]
    content = extract_content_tokens(tokens, cfg)
    assert "niño" in content
    assert "come" in content
    assert "manzana" in content
    assert "roja" in content
    assert "el" not in content
    assert "una" not in content


def test_extract_function_tokens():
    """Extract function words from sentence."""
    cfg = IdeaUnitConfig()
    tokens = ["el", "niño", "come", "una", "manzana", "roja"]
    function = extract_function_tokens(tokens, cfg)
    assert "el" in function
    assert "una" in function
    assert "niño" not in function
    assert "come" not in function


def test_count_idea_units():
    """Count content tokens (idea units)."""
    cfg = IdeaUnitConfig()
    tokens = ["el", "niño", "come", "una", "manzana", "roja"]
    count = count_idea_units(tokens, cfg)
    assert count == 4  # niño, come, manzana, roja


def test_near_synonym_detection():
    """Detect near-synonyms (morphological variants)."""
    cfg = IdeaUnitConfig()
    assert is_near_synonym("tiene", "tenía", cfg)
    assert is_near_synonym("es", "era", cfg)
    assert is_near_synonym("niño", "niños", cfg)
    assert not is_near_synonym("libro", "casa", cfg)


def test_near_synonym_case_insensitive():
    """Near-synonym detection is case-insensitive."""
    cfg = IdeaUnitConfig()
    assert is_near_synonym("Tiene", "tenía", cfg)
    assert is_near_synonym("TIENE", "TENÍA", cfg)


def test_get_near_synonyms():
    """Get all near-synonyms of a token."""
    cfg = IdeaUnitConfig()
    syns = get_near_synonyms("tiene", cfg)
    assert "tenía" in syns
    assert "tuvo" in syns


def test_prepositions_are_function_words():
    """Prepositions are classified as function words."""
    cfg = IdeaUnitConfig()
    tokens = ["en", "con", "por", "para", "sin"]
    function = extract_function_tokens(tokens, cfg)
    assert len(function) == 5


def test_articles_are_function_words():
    """Articles are classified as function words."""
    cfg = IdeaUnitConfig()
    tokens = ["el", "la", "los", "las", "un", "una"]
    function = extract_function_tokens(tokens, cfg)
    assert len(function) == 6


def test_conjunctions_are_function_words():
    """Conjunctions are classified as function words."""
    cfg = IdeaUnitConfig()
    tokens = ["y", "o", "pero", "que", "porque"]
    function = extract_function_tokens(tokens, cfg)
    assert len(function) == 5


def test_content_extraction_preserves_order():
    """Content extraction preserves token order."""
    cfg = IdeaUnitConfig()
    tokens = ["el", "gato", "come", "la", "comida"]
    content = extract_content_tokens(tokens, cfg)
    assert content == ["gato", "come", "comida"]


def test_empty_token_list():
    """Handle empty token list."""
    cfg = IdeaUnitConfig()
    assert extract_content_tokens([], cfg) == []
    assert extract_function_tokens([], cfg) == []
    assert count_idea_units([], cfg) == 0
