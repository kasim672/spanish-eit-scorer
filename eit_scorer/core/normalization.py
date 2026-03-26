"""
eit_scorer/core/normalization.py
==================================
Deterministic text normalization for Spanish EIT scoring.

Returns TWO normalized forms:
  display_normalized  — human-readable, used in trace output
  match_normalized    — used for token alignment (optionally accent-folded)

This separation means diacritics display correctly in reports
while still being handled consistently during alignment.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

@dataclass
class NormalizationConfig:
    lowercase:                   bool = True
    strip_punctuation:           bool = True
    normalize_whitespace:        bool = True
    fold_diacritics_for_matching:bool = False   # á→a, ñ→n etc. for alignment only
    expand_contractions:         bool = True
    strip_filler_words:          bool = True
    filler_words: list[str] = field(default_factory=lambda: [
        "eh", "um", "uh", "este", "mm", "mhm", "hmm", "ah", "eeh", "mmm"
    ])
    contraction_map: dict[str, list[str]] = field(default_factory=lambda: {
        "del": ["de", "el"],
        "al":  ["a",  "el"],
    })


# ─────────────────────────────────────────────────────────────
# NORMALIZATION
# ─────────────────────────────────────────────────────────────

# Spanish punctuation including inverted characters
_PUNCT_RE = re.compile(r'[¿¡.,!?;:\"\'\(\)\[\]{}<>…—–\-_/\\|@#$%^&*+=~`]')
_SPACE_RE = re.compile(r'\s+')


def _fold_diacritics(text: str) -> str:
    """Remove diacritical marks for matching (á→a, ñ→n, ü→u, etc.)."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def normalize_text(
    text: str,
    cfg: NormalizationConfig,
) -> tuple[str, str]:
    """
    Normalize text for EIT scoring.

    Returns:
        (display_normalized, match_normalized)
        display: for human-readable trace output
        match:   for alignment (optionally accent-folded)

    Both forms are deterministic and idempotent.
    """
    if not text:
        return "", ""

    # Unicode NFC normalization first (canonical composition)
    text = unicodedata.normalize("NFC", text.strip())

    if cfg.lowercase:
        text = text.lower()

    if cfg.strip_punctuation:
        text = _PUNCT_RE.sub(" ", text)

    # Remove filler words (whole-word match only)
    if cfg.strip_filler_words and cfg.filler_words:
        filler_pattern = r'\b(' + '|'.join(re.escape(f) for f in cfg.filler_words) + r')\b'
        text = re.sub(filler_pattern, ' ', text)

    if cfg.normalize_whitespace:
        text = _SPACE_RE.sub(" ", text).strip()

    display = text

    # Match form: optionally fold diacritics
    match = _fold_diacritics(text) if cfg.fold_diacritics_for_matching else text

    return display, match


# ─────────────────────────────────────────────────────────────
# CONTRACTION EXPANSION
# ─────────────────────────────────────────────────────────────

def expand_contractions_tokens(
    tokens: list[str],
    mapping: dict[str, list[str]],
) -> list[str]:
    """
    Expand Spanish contractions deterministically.
    "del" → ["de", "el"],  "al" → ["a", "el"]

    Applied after tokenization so word boundaries are respected.
    """
    result: list[str] = []
    for tok in tokens:
        expansion = mapping.get(tok)
        if expansion:
            result.extend(expansion)
        else:
            result.append(tok)
    return result
