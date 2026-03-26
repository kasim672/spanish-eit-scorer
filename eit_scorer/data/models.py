"""
eit_scorer/data/models.py
==========================
Canonical Pydantic data models used throughout the entire system.
Every data boundary — CLI I/O, API I/O, scoring engine — uses these types.

Models:
    EITItem           : A single EIT stimulus sentence
    EITResponse       : A learner's response to one item
    AlignmentOp       : One operation in the token alignment (match/sub/ins/del)
    ScoringTrace      : Complete audit trail for one scoring decision
    ScoredSentence    : Final output from the scoring engine per response
    ParticipantSummary: Aggregated per-participant result
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────────────────────
# INPUT MODELS
# ─────────────────────────────────────────────────────────────

class EITItem(BaseModel):
    """One EIT stimulus sentence (the target / reference)."""
    item_id:    str   = Field(..., description="Unique item identifier, e.g. 'eit_01'")
    reference:  str   = Field(..., description="The target sentence learners must imitate")
    max_points: int   = Field(4,   description="Maximum score for this item (default 4)")
    level:      Optional[str] = Field(None, description="CEFR level: A1–C2")
    domain:     Optional[str] = Field(None, description="Thematic domain")
    meta:       dict[str, Any] = Field(default_factory=dict)


class EITResponse(BaseModel):
    """One learner's transcribed response to one EIT item."""
    participant_id:  str            = Field(..., description="Unique participant ID")
    item_id:         str            = Field(..., description="Which item this response is for")
    response_text:   str            = Field("",  description="Transcribed learner response")
    human_rater_a:   Optional[float] = Field(None, description="Score from human rater A")
    human_rater_b:   Optional[float] = Field(None, description="Score from human rater B")
    meta:            dict[str, Any]  = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# ALIGNMENT OPERATION
# ─────────────────────────────────────────────────────────────

AlignOpType = Literal["match", "sub", "ins", "del"]


class AlignmentOp(BaseModel):
    """One operation produced by the Needleman-Wunsch token aligner."""
    op:        AlignOpType
    ref_token: Optional[str] = None   # Token in reference (target)
    hyp_token: Optional[str] = None   # Token in hypothesis (learner response)
    ref_idx:   Optional[int] = None   # Index in reference token list
    hyp_idx:   Optional[int] = None   # Index in hypothesis token list

    @property
    def is_error(self) -> bool:
        return self.op in {"sub", "ins", "del"}


# ─────────────────────────────────────────────────────────────
# SCORING TRACE
# ─────────────────────────────────────────────────────────────

class ScoringTrace(BaseModel):
    """
    Complete, auditable record of a single scoring decision.
    Contains everything needed to reproduce and explain the score.
    """
    # Normalized text
    display_ref:  str  = Field(..., description="Display-normalized reference")
    display_hyp:  str  = Field(..., description="Display-normalized hypothesis")
    match_ref:    str  = Field(..., description="Matching-normalized reference (used in alignment)")
    match_hyp:    str  = Field(..., description="Matching-normalized hypothesis (used in alignment)")

    # Tokens after normalization + contraction expansion
    ref_tokens:   list[str]
    hyp_tokens:   list[str]

    # Alignment
    alignment:    list[AlignmentOp]
    alignment_cost: float

    # Error counts
    error_counts: dict[str, int]   # keys: match, sub, ins, del, function_sub, content_sub
    total_edits:  int
    content_subs: int
    overlap_ratio: float

    # Rule application
    applied_rule_ids: list[str]    # Rules that fired (first match wins)
    score:            int
    max_points:       int

    def audit(self) -> list[str]:
        """Return human-readable audit trail lines."""
        lines = [
            f"REF (display):  {self.display_ref}",
            f"HYP (display):  {self.display_hyp}",
            f"REF (match):    {self.match_ref}",
            f"HYP (match):    {self.match_hyp}",
            f"REF tokens:     {self.ref_tokens}",
            f"HYP tokens:     {self.hyp_tokens}",
            "ALIGNMENT:",
        ]
        for op in self.alignment:
            ref = op.ref_token or "—"
            hyp = op.hyp_token or "—"
            lines.append(f"  [{op.op:5s}]  ref='{ref}'  hyp='{hyp}'")
        lines += [
            f"ERRORS:         {self.error_counts}",
            f"TOTAL EDITS:    {self.total_edits}",
            f"CONTENT SUBS:   {self.content_subs}",
            f"OVERLAP RATIO:  {self.overlap_ratio:.3f}",
            f"RULE(S) FIRED:  {self.applied_rule_ids}",
            f"SCORE:          {self.score} / {self.max_points}",
        ]
        return lines


# ─────────────────────────────────────────────────────────────
# SCORED SENTENCE
# ─────────────────────────────────────────────────────────────

class ScoredSentence(BaseModel):
    """Final output from the scoring engine for one learner response."""
    participant_id:  str
    item_id:         str
    response_text:   str
    score:           int
    max_points:      int
    trace:           ScoringTrace
    human_rater_a:   Optional[float] = None
    human_rater_b:   Optional[float] = None
    adjudicated:     Optional[float] = None   # Averaged or adjudicated human score
    meta:            dict[str, Any] = Field(default_factory=dict)

    def to_jsonl_dict(self) -> dict:
        """Serialize for JSONL output."""
        d = self.model_dump()
        # Convert AlignmentOp list to plain dicts
        d["trace"]["alignment"] = [op.model_dump() for op in self.trace.alignment]
        return d


# ─────────────────────────────────────────────────────────────
# PARTICIPANT SUMMARY
# ─────────────────────────────────────────────────────────────

class ParticipantSummary(BaseModel):
    """Aggregated EIT result for one participant."""
    participant_id:   str
    n_items:          int
    total_score:      int
    max_possible:     int
    mean_score:       float
    pct_max:          float   # total_score / max_possible * 100
    pct_perfect:      float   # % sentences scored at max_points

    @classmethod
    def from_scored(cls, pid: str, sentences: list[ScoredSentence]) -> "ParticipantSummary":
        n = len(sentences)
        total = sum(s.score for s in sentences)
        max_p = sum(s.max_points for s in sentences)
        perfect = sum(1 for s in sentences if s.score == s.max_points)
        return cls(
            participant_id=pid,
            n_items=n,
            total_score=total,
            max_possible=max_p,
            mean_score=total / n if n else 0.0,
            pct_max=total / max_p * 100 if max_p else 0.0,
            pct_perfect=perfect / n * 100 if n else 0.0,
        )
