"""
eit_scorer/core/error_labeling.py
===================================
Labels alignment operations and counts typed errors.

Distinguishes:
  function_sub  — substitution of a function word (articles, preps, conjunctions, clitics)
  content_sub   — substitution of a content word (nouns, verbs, adjectives, adverbs)

Also computes:
  token_overlap_ratio   — multiset-based recall (counts repeated tokens correctly)
  content_overlap_ratio — overlap restricted to content words only
  idea_unit_coverage    — proportion of reference content tokens reproduced
  is_gibberish          — detects noise-only responses ([gibberish], XXX, etc.)
  word_order_penalty    — fraction of content tokens present but misaligned
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from eit_scorer.data.models import AlignmentOp


# ─────────────────────────────────────────────────────────────
# GIBBERISH DETECTION
# ─────────────────────────────────────────────────────────────

# Patterns that indicate a transcription-level noise response
_GIBBERISH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'^\[.*\]$'),                    # [gibberish], [inaudible], [noise]
    re.compile(r'^x+$'),                        # xxx, xxxx
    re.compile(r'^[^a-záéíóúüñ\s]{3,}$'),      # all non-Spanish chars
    re.compile(r'^(\w)\1{3,}$'),                # aaaa, bbbb (repeated single char)
]

# Known noise words that survive normalization (brackets stripped)
_NOISE_WORDS: frozenset[str] = frozenset({
    "gibberish", "inaudible", "noise", "unclear", "unintelligible",
    "xxx", "xx", "ininteligible", "ruido",
})


def is_gibberish(tokens: list[str]) -> bool:
    """
    Return True if the entire response appears to be transcription noise.

    Checks each token against:
    1. Known noise patterns (regex)
    2. Known noise words that survive normalization (e.g. 'gibberish' after
       brackets are stripped by punctuation normalization)

    A response is gibberish only if ALL tokens match noise patterns/words.
    """
    if not tokens:
        return True
    return all(
        any(p.match(t) for p in _GIBBERISH_PATTERNS) or t in _NOISE_WORDS
        for t in tokens
    )


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
    # Morphological near-synonyms: pairs that should count as minor errors,
    # not full content substitutions. Stored as frozensets for O(1) lookup.
    near_synonym_pairs: list[frozenset[str]] = field(default_factory=lambda: [
        # Tense/aspect variants of common verbs
        frozenset({"tiene", "tenía"}),
        frozenset({"tiene", "tuvo"}),
        frozenset({"es", "era"}),
        frozenset({"es", "fue"}),
        frozenset({"está", "estaba"}),
        frozenset({"hace", "hacía"}),
        frozenset({"va", "iba"}),
        frozenset({"puede", "podía"}),
        frozenset({"quiere", "quería"}),
        frozenset({"sabe", "sabía"}),
        frozenset({"dice", "decía"}),
        frozenset({"viene", "venía"}),
        frozenset({"pone", "ponía"}),
        # Number variants (singular/plural)
        frozenset({"niño", "niños"}),
        frozenset({"niña", "niñas"}),
        frozenset({"libro", "libros"}),
        frozenset({"casa", "casas"}),
        frozenset({"amigo", "amigos"}),
        frozenset({"amiga", "amigas"}),
        frozenset({"ciudad", "ciudades"}),
        frozenset({"país", "países"}),
        # Gender variants
        frozenset({"bueno", "buena"}),
        frozenset({"malo", "mala"}),
        frozenset({"nuevo", "nueva"}),
        frozenset({"viejo", "vieja"}),
        frozenset({"pequeño", "pequeña"}),
        frozenset({"grande", "grandes"}),
        # Common lexical near-synonyms
        frozenset({"hablar", "decir"}),
        frozenset({"mirar", "ver"}),
        frozenset({"querer", "desear"}),
        frozenset({"empezar", "comenzar"}),
        frozenset({"terminar", "acabar"}),
        frozenset({"caminar", "andar"}),
        frozenset({"rápido", "rápidamente"}),
        frozenset({"lento", "lentamente"}),
    ])


# ─────────────────────────────────────────────────────────────
# TOKEN OVERLAP RATIO  (multiset-based)
# ─────────────────────────────────────────────────────────────

def token_overlap_ratio(ref_tokens: list[str], hyp_tokens: list[str]) -> float:
    """
    Multiset-based token overlap: sum(min(ref_count, hyp_count)) / len(ref)

    Unlike set-based overlap, this correctly handles repeated content words.
    Example: ref=[gato, gato, come], hyp=[gato, come] → 2/3 not 2/2.

    Returns 1.0 for perfect recall, 0.0 for no overlap.
    """
    if not ref_tokens:
        return 0.0

    # Build frequency maps
    ref_counts: dict[str, int] = {}
    for t in ref_tokens:
        ref_counts[t] = ref_counts.get(t, 0) + 1

    hyp_counts: dict[str, int] = {}
    for t in hyp_tokens:
        hyp_counts[t] = hyp_counts.get(t, 0) + 1

    matched = sum(min(ref_counts[t], hyp_counts.get(t, 0)) for t in ref_counts)
    return matched / len(ref_tokens)


def content_overlap_ratio(
    ref_tokens: list[str],
    hyp_tokens: list[str],
    function_words: set[str],
) -> float:
    """
    Multiset overlap restricted to content words only.

    This is the closest deterministic proxy for idea-unit coverage:
    content words carry the propositional meaning of the sentence.
    Returns 1.0 if all reference content words are reproduced.
    """
    ref_content = [t for t in ref_tokens if t not in function_words]
    hyp_content = [t for t in hyp_tokens if t not in function_words]
    return token_overlap_ratio(ref_content, hyp_content)


def idea_unit_coverage(
    ref_tokens: list[str],
    hyp_tokens: list[str],
    function_words: set[str],
    near_synonym_pairs: list[frozenset[str]] | None = None,
) -> float:
    """
    Approximate idea-unit coverage as the proportion of reference content
    tokens that appear in the hypothesis (multiset-aware, near-synonym-aware).

    Ortega (2000) defines idea units as the meaningful propositional chunks
    of the stimulus. Without a formal IU parser, content-word coverage is
    the best deterministic proxy: each unique content word in the reference
    represents one meaning-bearing element.

    Near-synonym awareness: if a reference content token is not present in
    the hypothesis but a near-synonym IS present, it counts as covered.
    This prevents morphological variants (tiene/tenía) from being penalized
    as missing idea units when meaning is preserved.

    Returns value in [0.0, 1.0].
    """
    ref_content = [t for t in ref_tokens if t not in function_words]
    hyp_content_set = {t for t in hyp_tokens if t not in function_words}

    if not ref_content:
        return 1.0  # no content words to cover → trivially covered

    # Build near-synonym lookup: token → set of synonyms
    syn_map: dict[str, set[str]] = {}
    if near_synonym_pairs:
        for pair in near_synonym_pairs:
            pair_list = list(pair)
            for tok in pair_list:
                syn_map.setdefault(tok, set()).update(pair - {tok})

    covered = 0
    hyp_content_counts: dict[str, int] = {}
    for t in hyp_content_set:
        hyp_content_counts[t] = sum(1 for x in hyp_tokens if x == t and x not in function_words)

    # Multiset-aware coverage with near-synonym fallback
    ref_counts: dict[str, int] = {}
    for t in ref_content:
        ref_counts[t] = ref_counts.get(t, 0) + 1

    for tok, needed in ref_counts.items():
        direct = hyp_content_counts.get(tok, 0)
        if direct >= needed:
            covered += needed
        else:
            covered += direct
            remaining = needed - direct
            # Try near-synonyms for the uncovered portion
            for syn in syn_map.get(tok, set()):
                syn_avail = hyp_content_counts.get(syn, 0)
                used = min(remaining, syn_avail)
                covered += used
                remaining -= used
                if remaining == 0:
                    break

    return covered / len(ref_content)


# ─────────────────────────────────────────────────────────────
# WORD ORDER PENALTY
# ─────────────────────────────────────────────────────────────

def word_order_penalty(
    ref_tokens: list[str],
    hyp_tokens: list[str],
    function_words: set[str],
) -> float:
    """
    Estimate the proportion of content tokens that are present in the
    hypothesis but appear in a different relative order than in the reference.

    Algorithm (deterministic):
      1. Extract content tokens from ref and hyp (preserving order).
      2. Find the Longest Common Subsequence (LCS) of content tokens.
      3. penalty = 1 - (LCS_length / max(ref_content_len, 1))

    A score of 0.0 means perfect order; 1.0 means completely reordered.
    This is used to distinguish genuine word-order errors from meaning loss.
    """
    ref_content = [t for t in ref_tokens if t not in function_words]
    hyp_content = [t for t in hyp_tokens if t not in function_words]

    if not ref_content:
        return 0.0

    lcs_len = _lcs_length(ref_content, hyp_content)
    return 1.0 - (lcs_len / len(ref_content))


def _lcs_length(a: list[str], b: list[str]) -> int:
    """Standard DP longest common subsequence length. O(n*m)."""
    n, m = len(a), len(b)
    # Use two-row rolling array for memory efficiency
    prev = [0] * (m + 1)
    curr = [0] * (m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (m + 1)
    return prev[m]


# ─────────────────────────────────────────────────────────────
# ERROR COUNTING
# ─────────────────────────────────────────────────────────────

def count_errors(
    alignment: list[AlignmentOp],
    cfg: ErrorLabelingConfig,
) -> tuple[dict[str, int], int, int]:
    """
    Count typed errors from the alignment.

    Substitution classification (in priority order):
      1. near_synonym_sub — ref/hyp token pair is in the near-synonym table
                            (morphological variant or lexical near-synonym)
                            → treated as minor error, NOT a content_sub
      2. function_sub     — ref token is a function word
      3. content_sub      — everything else (full meaning change)

    Returns:
        error_counts : dict with keys: match, sub, ins, del,
                       function_sub, content_sub, near_synonym_sub
        total_edits  : ins + del + sub (all non-match ops)
        content_subs : count of full content word substitutions only
                       (near_synonym_subs are excluded — they are minor)
    """
    counts: dict[str, int] = {
        "match":            0,
        "sub":              0,
        "ins":              0,
        "del":              0,
        "function_sub":     0,
        "content_sub":      0,
        "near_synonym_sub": 0,
    }

    # Build a fast lookup set from the near-synonym pairs
    near_synonym_set: set[frozenset[str]] = set(cfg.near_synonym_pairs)

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
            hyp_tok = (op.hyp_token or "").lower()
            pair = frozenset({ref_tok, hyp_tok})

            if pair in near_synonym_set:
                # Morphological variant or near-synonym — minor error
                counts["near_synonym_sub"] += 1
            elif ref_tok in cfg.function_words:
                counts["function_sub"] += 1
            else:
                counts["content_sub"] += 1

    total_edits  = counts["ins"] + counts["del"] + counts["sub"]
    content_subs = counts["content_sub"]   # near_synonym_subs excluded

    return counts, total_edits, content_subs
