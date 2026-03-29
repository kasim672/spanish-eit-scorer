"""
eit_scorer/core/scoring.py
============================
End-to-end deterministic scoring pipeline for a single EIT sentence.

Pipeline:
  1. Normalize (display + match forms)
  2. Tokenize (with enclitic splitting)
  3. Expand contractions
  4. Align (Needleman-Wunsch, deterministic tie-breaking)
  5. Count errors + compute overlap ratio
  6. Build ScoreContext (feature vector for rules)
  7. Apply rules (first match wins)
  8. Clamp score to [0, max_points]
  9. Return ScoredSentence

Invariant: Same (item, response, rubric) → same score.
"""

from __future__ import annotations

from dataclasses import dataclass

from eit_scorer.core.alignment      import align_tokens
from eit_scorer.core.error_labeling import (
    count_errors, token_overlap_ratio,
    content_overlap_ratio, idea_unit_coverage,
    word_order_penalty, is_gibberish,
)
from eit_scorer.core.normalization  import normalize_text, expand_contractions_tokens, NormalizationConfig
from eit_scorer.core.noise_handler  import clean_response, NoiseConfig
from eit_scorer.core.rubric         import RubricConfig, RubricRule
from eit_scorer.core.tokenization   import tokenize
from eit_scorer.data.models         import (
    AlignmentOp, EITItem, EITResponse, ScoredSentence, ScoringTrace
)

# ─────────────────────────────────────────────────────────────
# SCORE CONTEXT (feature vector for rule evaluation)
# ─────────────────────────────────────────────────────────────

@dataclass
class ScoreContext:
    """Features extracted from the alignment — used by rule conditions."""
    hyp_tokens:          list[str]
    ref_tokens:          list[str]
    total_edits:         int
    content_subs:        int
    near_synonym_subs:   int
    overlap_ratio:       float
    content_overlap:     float   # overlap restricted to content words
    idea_unit_coverage:  float   # proportion of ref content tokens reproduced
    word_order_penalty:  float   # 0.0=perfect order, 1.0=fully reordered
    is_gibberish:        bool    # True if response is transcription noise

    @property
    def hyp_min_tokens(self) -> int:
        return len(self.hyp_tokens)

    @property
    def ref_len(self) -> int:
        return len(self.ref_tokens)

    @property
    def length_ratio(self) -> float:
        """hyp length / ref length — completeness proxy."""
        if not self.ref_tokens:
            return 0.0
        return len(self.hyp_tokens) / len(self.ref_tokens)


# ─────────────────────────────────────────────────────────────
# SCORE CONTEXT (feature vector for rule evaluation)
# ─────────────────────────────────────────────────────────────

_OPS = {
    "eq":  lambda a, b: a == b,
    "ne":  lambda a, b: a != b,
    "lt":  lambda a, b: a <  b,
    "le":  lambda a, b: a <= b,
    "gt":  lambda a, b: a >  b,
    "ge":  lambda a, b: a >= b,
}


def _rule_matches(rule_when: dict, ctx: ScoreContext) -> bool:
    """
    Evaluate a rule's `when` conditions against the score context.

    Supported condition fields:
        max_edits                  : total_edits <= value
        max_content_subs           : content_subs <= value
        min_token_overlap_ratio    : overlap_ratio >= value
        min_content_overlap        : content_overlap >= value
        min_idea_unit_coverage     : idea_unit_coverage >= value
        max_word_order_penalty     : word_order_penalty <= value
        min_length_ratio           : length_ratio >= value
        hyp_min_tokens             : len(hyp_tokens) >= value
        is_gibberish               : bool match
          (optional operator suffix, e.g. hyp_min_tokens_lt: 2)

    All conditions must hold (logical AND).
    """
    for key, value in rule_when.items():
        # Parse key into (field, operator)
        parts  = key.rsplit("_", 1)
        op_key = parts[-1] if parts[-1] in _OPS else None
        field  = "_".join(parts[:-1]) if op_key else key

        op_fn = _OPS.get(op_key, None)

        # Canonical conditions (with implicit operators)
        if key == "max_edits":
            if not (ctx.total_edits <= int(value)):
                return False
        elif key == "max_content_subs":
            if not (ctx.content_subs <= int(value)):
                return False
        elif key == "min_token_overlap_ratio":
            if not (ctx.overlap_ratio >= float(value)):
                return False
        elif key == "min_content_overlap":
            if not (ctx.content_overlap >= float(value)):
                return False
        elif key == "min_idea_unit_coverage":
            if not (ctx.idea_unit_coverage >= float(value)):
                return False
        elif key == "max_word_order_penalty":
            if not (ctx.word_order_penalty <= float(value)):
                return False
        elif key == "min_length_ratio":
            if not (ctx.length_ratio >= float(value)):
                return False
        elif key == "hyp_min_tokens":
            if not (ctx.hyp_min_tokens >= int(value)):
                return False
        elif key == "is_gibberish":
            if ctx.is_gibberish != bool(value):
                return False
        # Parametric conditions  e.g.  total_edits_lt: 3
        elif field == "total_edits" and op_fn:
            if not op_fn(ctx.total_edits, int(value)):
                return False
        elif field == "content_subs" and op_fn:
            if not op_fn(ctx.content_subs, int(value)):
                return False
        elif field == "overlap_ratio" and op_fn:
            if not op_fn(ctx.overlap_ratio, float(value)):
                return False
        elif field == "content_overlap" and op_fn:
            if not op_fn(ctx.content_overlap, float(value)):
                return False
        elif field == "idea_unit_coverage" and op_fn:
            if not op_fn(ctx.idea_unit_coverage, float(value)):
                return False
        elif field == "word_order_penalty" and op_fn:
            if not op_fn(ctx.word_order_penalty, float(value)):
                return False
        elif field == "length_ratio" and op_fn:
            if not op_fn(ctx.length_ratio, float(value)):
                return False
        elif field == "hyp_min_tokens" and op_fn:
            if not op_fn(ctx.hyp_min_tokens, int(value)):
                return False
        else:
            # Unknown condition — skip rather than crash (graceful degradation)
            pass

    return True


# ─────────────────────────────────────────────────────────────
# MAIN SCORING FUNCTION
# ─────────────────────────────────────────────────────────────

def score_response(
    item:   EITItem,
    resp:   EITResponse,
    rubric: RubricConfig,
) -> ScoredSentence:
    """
    Score one learner response against its target sentence.

    Fully deterministic: same (item, resp, rubric) always produces
    the same score and the same fingerprint.

    Returns:
        ScoredSentence with complete ScoringTrace
    """
    max_pts = item.max_points or rubric.max_points

    # ── 1. Normalize ──────────────────────────────────────────
    display_ref, match_ref = normalize_text(item.reference,       rubric.normalization)
    display_hyp, match_hyp = normalize_text(resp.response_text,   rubric.normalization)

    # ── 2. Tokenize ───────────────────────────────────────────
    ref_tokens_raw = tokenize(match_ref, rubric.tokenization)
    hyp_tokens_raw = tokenize(match_hyp, rubric.tokenization)

    # ── 3. Expand contractions ────────────────────────────────
    cmap = rubric.normalization.contraction_map
    ref_tokens = expand_contractions_tokens(ref_tokens_raw, cmap) if rubric.normalization.expand_contractions else ref_tokens_raw
    hyp_tokens = expand_contractions_tokens(hyp_tokens_raw, cmap) if rubric.normalization.expand_contractions else hyp_tokens_raw

    # ── 4. Align ─────────────────────────────────────────────
    alignment, alignment_cost = align_tokens(ref_tokens, hyp_tokens, rubric.alignment)

    # ── 5. Count errors + overlap ─────────────────────────────
    error_counts, total_edits, content_subs = count_errors(alignment, rubric.error_labeling)
    overlap = token_overlap_ratio(ref_tokens, hyp_tokens)

    # ── 5b. Compute enriched meaning features ─────────────────
    fw = rubric.error_labeling.function_words
    near_syns = rubric.error_labeling.near_synonym_pairs
    c_overlap  = content_overlap_ratio(ref_tokens, hyp_tokens, fw)
    iu_cov     = idea_unit_coverage(ref_tokens, hyp_tokens, fw, near_syns)
    wo_penalty = word_order_penalty(ref_tokens, hyp_tokens, fw)
    gibb       = is_gibberish(hyp_tokens)
    near_syn_subs = error_counts.get("near_synonym_sub", 0)
    
    # ── 5c. Detect noise in response ──────────────────────────
    # Note: noise detection is informational; we still score the response
    # even if it contains noise. The is_gibberish flag captures full-noise responses.
    noise_cfg = NoiseConfig()
    cleaned_hyp, is_full_noise = clean_response(display_hyp, noise_cfg)

    # ── 6. Build context ─────────────────────────────────────
    ctx = ScoreContext(
        hyp_tokens=hyp_tokens,
        ref_tokens=ref_tokens,
        total_edits=total_edits,
        content_subs=content_subs,
        near_synonym_subs=near_syn_subs,
        overlap_ratio=overlap,
        content_overlap=c_overlap,
        idea_unit_coverage=iu_cov,
        word_order_penalty=wo_penalty,
        is_gibberish=gibb,
    )

    # ── 7. Apply rules (first match wins) ────────────────────
    score:         int       = 0
    applied_rules: list[str] = []

    for rule in rubric.rules:
        if _rule_matches(rule.when, ctx):
            score = rule.score
            applied_rules.append(rule.rule_id)
            break   # First match wins — order in YAML matters

    if not applied_rules:
        # No rule matched — default to 0 with a sentinel rule ID
        applied_rules = ["_default_no_match_score_0"]

    # ── 8. Clamp ─────────────────────────────────────────────
    score = max(0, min(score, max_pts))

    # ── 9. Build trace + result ───────────────────────────────
    trace = ScoringTrace(
        display_ref=display_ref,
        display_hyp=display_hyp,
        match_ref=match_ref,
        match_hyp=match_hyp,
        ref_tokens=ref_tokens,
        hyp_tokens=hyp_tokens,
        alignment=alignment,
        alignment_cost=alignment_cost,
        error_counts=error_counts,
        total_edits=total_edits,
        content_subs=content_subs,
        overlap_ratio=overlap,
        content_overlap=c_overlap,
        idea_unit_coverage=iu_cov,
        word_order_penalty=wo_penalty,
        is_gibberish=gibb,
        near_synonym_subs=near_syn_subs,
        applied_rule_ids=applied_rules,
        score=score,
        max_points=max_pts,
    )

    # Adjudicate human scores if both available
    adjudicated: float | None = None
    if resp.human_rater_a is not None and resp.human_rater_b is not None:
        a, b = resp.human_rater_a, resp.human_rater_b
        if abs(a - b) <= 1.0:
            adjudicated = (a + b) / 2
        else:
            adjudicated = min(a, b)  # conservative
    elif resp.human_rater_a is not None:
        adjudicated = resp.human_rater_a

    return ScoredSentence(
        participant_id=resp.participant_id,
        item_id=resp.item_id,
        response_text=resp.response_text,
        score=score,
        max_points=max_pts,
        trace=trace,
        human_rater_a=resp.human_rater_a,
        human_rater_b=resp.human_rater_b,
        adjudicated=adjudicated,
        meta=resp.meta,
    )
