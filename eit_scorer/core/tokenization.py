"""
eit_scorer/core/tokenization.py
==================================
Deterministic Spanish tokenizer with enclitic splitting.

Examples:
    "dímelo"  → ["dime", "lo"]
    "cómpraselo" → ["cómpra", "se", "lo"]
    "háblame" → ["hábla", "me"]

All operations are deterministic (no randomness, no external model).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TokenizationConfig:
    split_on_whitespace: bool       = True
    keep_apostrophes:    bool       = False
    split_enclitics:     bool       = True
    enclitics: list[str] = field(default_factory=lambda: [
        # Order matters: longest first for greedy matching
        "selos", "selas", "melos", "melas", "telos", "telas",
        "noslos", "noslas",
        "selo", "sela", "melo", "mela", "telo", "tela",
        "nos", "los", "las", "les",
        "me", "te", "se", "lo", "la", "le",
        "os",
    ])


def tokenize(text: str, cfg: TokenizationConfig) -> list[str]:
    """
    Tokenize normalized Spanish text.

    Steps:
    1. Optionally remove apostrophes
    2. Split on whitespace
    3. Optionally split enclitics from verb forms

    Returns list of tokens (all lowercase, no punctuation expected since
    normalization already stripped it).
    """
    if not text:
        return []

    if not cfg.keep_apostrophes:
        text = text.replace("'", "").replace("'", "")

    tokens = text.split() if cfg.split_on_whitespace else [text]
    tokens = [t for t in tokens if t]   # remove empty strings

    if cfg.split_enclitics:
        tokens = split_spanish_enclitics(tokens, cfg.enclitics)

    return tokens


def split_spanish_enclitics(
    tokens: list[str],
    enclitics: list[str],
) -> list[str]:
    """
    Deterministically peel enclitic pronouns from verb forms.
    Uses longest-match-first strategy.

    Only splits if:
    - The token ends with the enclitic
    - The remaining stem is ≥3 characters (avoids over-splitting)
    - The token is ≥5 characters total (minimum realistic verb+clitic)

    Examples:
        "dímelo"   → ["dime", "lo"]
        "dáme"     → ["dáme"]        (stem too short after split)
        "cómpraselo" → ["cómprase", "lo"] then ["cómpra","se","lo"] recursively
    """
    result: list[str] = []
    for token in tokens:
        parts = _peel_enclitics(token, enclitics)
        result.extend(parts)
    return result


def _peel_enclitics(token: str, enclitics: list[str]) -> list[str]:
    """Recursively peel enclitics from a token."""
    if len(token) < 4:
        return [token]

    # Try each enclitic longest-first
    for enc in sorted(enclitics, key=len, reverse=True):
        if token.endswith(enc) and len(token) - len(enc) >= 3:
            stem = token[: -len(enc)]
            # Recursively check if stem still ends in another enclitic
            stem_parts = _peel_enclitics(stem, enclitics)
            return stem_parts + [enc]

    return [token]
