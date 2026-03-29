"""
eit_scorer/core/noise_handler.py
==================================
Noise and filler word detection and removal.

Handles:
- Transcription noise: [gibberish], XXX, [inaudible], etc.
- Filler words: eh, um, uh, este, mm, hmm, ah, eeh
- False starts and hesitations
- Repeated characters (aaaa, bbbb)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class NoiseConfig:
    """Configuration for noise detection and removal."""
    
    # Filler words to remove
    filler_words: set[str] = field(default_factory=lambda: {
        "eh", "um", "uh", "este", "mm", "mhm", "hmm", "ah", "eeh",
        "erm", "err", "uh-huh", "uhuh", "huh", "shh", "psst",
    })
    
    # Noise patterns (regex)
    noise_patterns: list[re.Pattern[str]] = field(default_factory=lambda: [
        re.compile(r'^\[.*\]$'),                    # [gibberish], [inaudible], [noise]
        re.compile(r'^x+$', re.IGNORECASE),         # xxx, xxxx
        re.compile(r'^[^a-záéíóúüñ\s]{3,}$'),       # all non-Spanish chars
        re.compile(r'^(\w)\1{3,}$'),                # aaaa, bbbb (repeated single char)
    ])
    
    # Known noise words that survive normalization
    noise_words: frozenset[str] = field(default_factory=lambda: frozenset({
        "gibberish", "inaudible", "noise", "unclear", "unintelligible",
        "xxx", "xx", "ininteligible", "ruido", "incomprehensible",
    }))


def is_noise_token(token: str, cfg: NoiseConfig) -> bool:
    """
    Check if a single token is noise.
    
    Returns True if token matches any noise pattern or is a known noise word.
    """
    if not token:
        return True
    
    # Check known noise words
    if token.lower() in cfg.noise_words:
        return True
    
    # Check noise patterns
    for pattern in cfg.noise_patterns:
        if pattern.match(token):
            return True
    
    return False


def is_gibberish(tokens: list[str], cfg: NoiseConfig | None = None) -> bool:
    """
    Return True if the entire response appears to be transcription noise.
    
    A response is gibberish only if ALL tokens match noise patterns/words.
    """
    if cfg is None:
        cfg = NoiseConfig()
    
    if not tokens:
        return True
    
    return all(is_noise_token(t, cfg) for t in tokens)


def remove_noise_tokens(tokens: list[str], cfg: NoiseConfig | None = None) -> list[str]:
    """
    Remove noise and filler tokens from a token list.
    
    Preserves order of remaining tokens.
    """
    if cfg is None:
        cfg = NoiseConfig()
    
    return [t for t in tokens if not is_noise_token(t, cfg) and t.lower() not in cfg.filler_words]


def remove_noise_text(text: str, cfg: NoiseConfig | None = None) -> str:
    """
    Remove noise and filler words from text.
    
    Handles:
    - Removes [gibberish], XXX, etc.
    - Removes filler words (eh, um, uh, este, etc.)
    - Preserves word order and spacing
    """
    if cfg is None:
        cfg = NoiseConfig()
    
    # Split into tokens
    tokens = text.split()
    
    # Remove noise tokens
    cleaned_tokens = remove_noise_tokens(tokens, cfg)
    
    # Rejoin
    return " ".join(cleaned_tokens)


def clean_response(text: str, cfg: NoiseConfig | None = None) -> tuple[str, bool]:
    """
    Clean a response by removing noise and filler words.
    
    Returns:
        (cleaned_text, is_gibberish)
    """
    if cfg is None:
        cfg = NoiseConfig()
    
    # Check if entire response is gibberish before cleaning
    tokens = text.split()
    gibberish = is_gibberish(tokens, cfg)
    
    # Remove noise
    cleaned = remove_noise_text(text, cfg)
    
    return cleaned, gibberish
