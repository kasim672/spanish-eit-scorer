"""
tests/test_noise_handler.py
============================
Tests for noise and filler word detection and removal.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.noise_handler import (
    NoiseConfig, is_noise_token, is_gibberish, remove_noise_tokens,
    remove_noise_text, clean_response
)


def test_noise_token_detection():
    """Detect common noise patterns."""
    cfg = NoiseConfig()
    assert is_noise_token("[gibberish]", cfg)
    assert is_noise_token("xxx", cfg)
    assert is_noise_token("XXX", cfg)
    assert is_noise_token("[inaudible]", cfg)
    assert not is_noise_token("libro", cfg)


def test_filler_word_detection():
    """Filler words are removed by remove_noise_tokens."""
    cfg = NoiseConfig()
    # Filler words are in cfg.filler_words, not noise_words
    assert "eh" in cfg.filler_words
    assert "um" in cfg.filler_words
    assert "uh" in cfg.filler_words
    assert "hmm" in cfg.filler_words
    # Test removal
    tokens = ["eh", "um", "uh", "hmm"]
    cleaned = remove_noise_tokens(tokens, cfg)
    assert cleaned == []


def test_gibberish_detection():
    """Detect full gibberish responses."""
    cfg = NoiseConfig()
    assert is_gibberish(["[gibberish]"], cfg)
    assert is_gibberish(["xxx", "xxx"], cfg)
    assert is_gibberish(["[inaudible]", "xxx"], cfg)
    assert not is_gibberish(["el", "libro"], cfg)
    assert not is_gibberish(["el", "[gibberish]"], cfg)  # Mixed


def test_remove_noise_tokens():
    """Remove noise tokens from list."""
    cfg = NoiseConfig()
    tokens = ["el", "libro", "eh", "está", "um", "en", "la", "mesa"]
    cleaned = remove_noise_tokens(tokens, cfg)
    assert cleaned == ["el", "libro", "está", "en", "la", "mesa"]


def test_remove_noise_text():
    """Remove noise from text."""
    cfg = NoiseConfig()
    text = "el libro eh está um en la mesa"
    cleaned = remove_noise_text(text, cfg)
    assert cleaned == "el libro está en la mesa"


def test_clean_response_with_noise():
    """Clean response with noise detection."""
    cfg = NoiseConfig()
    text = "El libro [pause] está en la mesa"
    cleaned, is_gibberish_flag = clean_response(text, cfg)
    assert "[pause]" not in cleaned
    assert not is_gibberish_flag


def test_clean_response_gibberish():
    """Detect gibberish response."""
    cfg = NoiseConfig()
    text = "[gibberish] xxx [inaudible]"
    cleaned, is_gibberish_flag = clean_response(text, cfg)
    assert is_gibberish_flag


def test_repeated_chars_noise():
    """Detect repeated character patterns as noise."""
    cfg = NoiseConfig()
    assert is_noise_token("aaaa", cfg)
    assert is_noise_token("bbbb", cfg)
    assert not is_noise_token("aaa", cfg)  # Less than 4


def test_empty_after_noise_removal():
    """Handle case where all tokens are noise."""
    cfg = NoiseConfig()
    tokens = ["eh", "um", "uh", "hmm"]
    cleaned = remove_noise_tokens(tokens, cfg)
    assert cleaned == []


def test_preserve_content_words():
    """Ensure content words are preserved."""
    cfg = NoiseConfig()
    text = "El niño eh come una manzana roja"
    cleaned = remove_noise_text(text, cfg)
    assert "niño" in cleaned
    assert "come" in cleaned
    assert "manzana" in cleaned
    assert "roja" in cleaned
    assert "eh" not in cleaned
