"""
eit_scorer/core/error_labeling.py
===================================
Labels alignment operations and counts typed errors.

Distinguishes:
  function_sub  — substitution of a function word (articles, preps, conjunctions, clitics)
  content_sub   — substitution of a content word (nouns, verbs, adjectives, adverbs)

Also computes token overlap ratio (set-based) used by rubric rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eit_scorer.data.models import AlignmentOp


# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

@dataclass
class ErrorLabelingConfig:
    function_words: set[str] = field(default_factory=lambda: {
        # Articles
        "el", "la", "los", "las", "un", "una", "unos", "unas",
        # Prepositions
        "a", "de", "en", "con", "por", "para", "sin", "sobre",
        "entre", "hasta", "desde", "hacia", "durante",
        # Contractions (pre-expansion)
        "del", "al",
        # Conjunctions
        "que", "y", "e", "o", "u", "pero", "sino", "si",
        "aunque", "cuando", "donde", "como", "porque",
        "mientras", "después", "antes", "para",
        # Clitics & pronouns
        "me", "te", "se", "lo", "la", "le", "nos", "os",
        "los", "las", "les",
        # Common determiners / quantifiers treated as function
        "este", "ese", "aquel", "esta", "esa", "aquella",
        "estos", "esos", "estos", "estas", "esas",
        # Auxiliaries
        "ha", "han", "he", "has", "había", "habían",
        "ser", "estar", "haber",
    })


# ─────────────────────────────────────────────────────────────
# TOKEN OVERLAP RATIO
# ─────────────────────────────────────────────────────────────

def token_overlap_ratio(ref_tokens: list[str], hyp_tokens: list[str]) -> float:
    """
    Set-based token overlap: |intersection| / |reference|

    Measures how many unique reference tokens appear anywhere in hypothesis.
    Returns 1.0 for perfect recall, 0.0 for no overlap.
    """
    if not ref_tokens:
        return 0.0
    ref_set = set(ref_tokens)
    hyp_set = set(hyp_tokens)
    return len(ref_set & hyp_set) / len(ref_set)


# ─────────────────────────────────────────────────────────────
# ERROR COUNTING
# ─────────────────────────────────────────────────────────────

def count_errors(
    alignment: list[AlignmentOp],
    cfg: ErrorLabelingConfig,
) -> tuple[dict[str, int], int, int]:
    """
    Count typed errors from the alignment.

    Returns:
        error_counts : dict with keys: match, sub, ins, del,
                       function_sub, content_sub
        total_edits  : ins + del + sub (all non-match ops)
        content_subs : count of content word substitutions
    """
    counts: dict[str, int] = {
        "match":        0,
        "sub":          0,
        "ins":          0,
        "del":          0,
        "function_sub": 0,
        "content_sub":  0,
    }

    for op in alignment:
        if op.op == "match":
            counts["match"] += 1
        elif op.op == "del":
            counts["del"] += 1
        elif op.op == "ins":
            counts["ins"] += 1
        elif op.op == "sub":
            counts["sub"] += 1
            ref_tok = (op.ref_token or "").lower()
            if ref_tok in cfg.function_words:
                counts["function_sub"] += 1
            else:
                counts["content_sub"] += 1

    total_edits  = counts["ins"] + counts["del"] + counts["sub"]
    content_subs = counts["content_sub"]

    return counts, total_edits, content_subs
