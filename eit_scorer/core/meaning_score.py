"""
eit_scorer/core/meaning_score.py
==================================
Meaning preservation scoring.

Computes features that measure how well the learner's response
preserves the meaning of the reference stimulus:
- Content overlap (multiset-based)
- Idea unit coverage (with near-synonym awareness)
- Word order penalty (LCS-based)
"""

from __future__ import annotations

from eit_scorer.core.idea_units import IdeaUnitConfig, extract_content_tokens, is_near_synonym


def content_overlap_ratio(
    ref_tokens: list[str],
    hyp_tokens: list[str],
    cfg: IdeaUnitConfig,
) -> float:
    """
    Multiset overlap restricted to content words only.
    
    This is the closest deterministic proxy for idea-unit coverage:
    content words carry the propositional meaning of the sentence.
    
    Returns 1.0 if all reference content words are reproduced.
    """
    ref_content = extract_content_tokens(ref_tokens, cfg)
    hyp_content = extract_content_tokens(hyp_tokens, cfg)
    
    if not ref_content:
        return 1.0
    
    # Build frequency maps
    ref_counts: dict[str, int] = {}
    for t in ref_content:
        ref_counts[t.lower()] = ref_counts.get(t.lower(), 0) + 1
    
    hyp_counts: dict[str, int] = {}
    for t in hyp_content:
        hyp_counts[t.lower()] = hyp_counts.get(t.lower(), 0) + 1
    
    # Multiset overlap
    matched = sum(min(ref_counts[t], hyp_counts.get(t, 0)) for t in ref_counts)
    return matched / len(ref_content)


def idea_unit_coverage(
    ref_tokens: list[str],
    hyp_tokens: list[str],
    cfg: IdeaUnitConfig,
) -> float:
    """
    Approximate idea-unit coverage as the proportion of reference content
    tokens that appear in the hypothesis (multiset-aware, near-synonym-aware).
    
    Ortega (2000) defines idea units as the meaningful propositional chunks
    of the stimulus. Without a formal IU parser, content-word coverage is
    the best deterministic proxy.
    
    Near-synonym awareness: if a reference content token is not present in
    the hypothesis but a near-synonym IS present, it counts as covered.
    This prevents morphological variants (tiene/tenía) from being penalized
    as missing idea units when meaning is preserved.
    
    Returns value in [0.0, 1.0].
    """
    ref_content = extract_content_tokens(ref_tokens, cfg)
    hyp_content_set = {t.lower() for t in extract_content_tokens(hyp_tokens, cfg)}
    
    if not ref_content:
        return 1.0
    
    # Build near-synonym lookup: token → set of synonyms
    syn_map: dict[str, set[str]] = {}
    for pair in cfg.near_synonym_pairs:
        pair_list = list(pair)
        for tok in pair_list:
            syn_map.setdefault(tok, set()).update(pair - {tok})
    
    covered = 0
    hyp_content_counts: dict[str, int] = {}
    for t in hyp_content_set:
        hyp_content_counts[t] = sum(1 for x in hyp_tokens if x.lower() == t and x.lower() not in cfg.function_words)
    
    # Multiset-aware coverage with near-synonym fallback
    ref_counts: dict[str, int] = {}
    for t in ref_content:
        t_lower = t.lower()
        ref_counts[t_lower] = ref_counts.get(t_lower, 0) + 1
    
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


def word_order_penalty(
    ref_tokens: list[str],
    hyp_tokens: list[str],
    cfg: IdeaUnitConfig,
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
    ref_content = extract_content_tokens(ref_tokens, cfg)
    hyp_content = extract_content_tokens(hyp_tokens, cfg)
    
    if not ref_content:
        return 0.0
    
    # Normalize to lowercase for comparison
    ref_content_lower = [t.lower() for t in ref_content]
    hyp_content_lower = [t.lower() for t in hyp_content]
    
    lcs_len = _lcs_length(ref_content_lower, hyp_content_lower)
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


def token_overlap_ratio(ref_tokens: list[str], hyp_tokens: list[str]) -> float:
    """
    Multiset-based token overlap: sum(min(ref_count, hyp_count)) / len(ref)
    
    Unlike set-based overlap, this correctly handles repeated content words.
    Example: ref=[gato, gato, come], hyp=[gato, come] → 2/3 not 2/2.
    
    Returns 1.0 for perfect recall, 0.0 for no overlap.
    """
    if not ref_tokens:
        return 0.0
    
    # Build frequency maps (case-insensitive)
    ref_counts: dict[str, int] = {}
    for t in ref_tokens:
        t_lower = t.lower()
        ref_counts[t_lower] = ref_counts.get(t_lower, 0) + 1
    
    hyp_counts: dict[str, int] = {}
    for t in hyp_tokens:
        t_lower = t.lower()
        hyp_counts[t_lower] = hyp_counts.get(t_lower, 0) + 1
    
    matched = sum(min(ref_counts[t], hyp_counts.get(t, 0)) for t in ref_counts)
    return matched / len(ref_tokens)
