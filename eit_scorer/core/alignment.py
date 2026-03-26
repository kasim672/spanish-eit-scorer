"""
eit_scorer/core/alignment.py
==============================
Global token-level sequence alignment using Needleman-Wunsch.

Key property: DETERMINISTIC tie-breaking.
When multiple traceback paths have equal cost, the algorithm always
chooses: diagonal (match/sub) > deletion > insertion.
This guarantees that the same input always produces the same alignment,
which is essential for reproducible scoring.

Returns:
    (list[AlignmentOp], alignment_cost: float)
"""

from __future__ import annotations

from dataclasses import dataclass

from eit_scorer.data.models import AlignmentOp


@dataclass
class AlignmentConfig:
    match_score:      float =  2.0
    mismatch_penalty: float = -1.0
    gap_penalty:      float = -1.0


def align_tokens(
    ref: list[str],
    hyp: list[str],
    cfg: AlignmentConfig,
) -> tuple[list[AlignmentOp], float]:
    """
    Align reference tokens to hypothesis tokens using Needleman-Wunsch.

    Tie-breaking rule (deterministic):
        diagonal (match/sub) > deletion (gap in hyp) > insertion (gap in ref)

    Returns:
        ops:  list[AlignmentOp] — the alignment operations
        cost: float             — total alignment score (higher = more similar)
    """
    n = len(ref)
    m = len(hyp)

    # Build DP matrix — indices: [ref_idx+1][hyp_idx+1]
    dp: list[list[float]] = [[0.0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i * cfg.gap_penalty
    for j in range(m + 1):
        dp[0][j] = j * cfg.gap_penalty

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            match_score = (
                cfg.match_score
                if ref[i - 1] == hyp[j - 1]
                else cfg.mismatch_penalty
            )
            # Tie-breaking: diagonal preferred, then deletion, then insertion
            diag = dp[i - 1][j - 1] + match_score
            dele = dp[i - 1][j] + cfg.gap_penalty   # delete from ref (miss in hyp)
            ins  = dp[i][j - 1] + cfg.gap_penalty   # insert into ref (extra in hyp)

            # Deterministic max: prefer diag > dele > ins
            dp[i][j] = max(diag, dele, ins)

    # Traceback — deterministic tie-breaking applied in same order
    ops: list[AlignmentOp] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            match_score = (
                cfg.match_score
                if ref[i - 1] == hyp[j - 1]
                else cfg.mismatch_penalty
            )
            diag = dp[i - 1][j - 1] + match_score
            dele = dp[i - 1][j]     + cfg.gap_penalty
            ins  = dp[i][j - 1]     + cfg.gap_penalty

            best = max(diag, dele, ins)

            # Prefer diagonal when tied
            if dp[i][j] == diag:
                op_type = "match" if ref[i - 1] == hyp[j - 1] else "sub"
                ops.append(AlignmentOp(
                    op=op_type,
                    ref_token=ref[i - 1],
                    hyp_token=hyp[j - 1],
                    ref_idx=i - 1,
                    hyp_idx=j - 1,
                ))
                i -= 1
                j -= 1
            elif dp[i][j] == dele:
                ops.append(AlignmentOp(
                    op="del",
                    ref_token=ref[i - 1],
                    hyp_token=None,
                    ref_idx=i - 1,
                    hyp_idx=None,
                ))
                i -= 1
            else:
                ops.append(AlignmentOp(
                    op="ins",
                    ref_token=None,
                    hyp_token=hyp[j - 1],
                    ref_idx=None,
                    hyp_idx=j - 1,
                ))
                j -= 1

        elif i > 0:
            ops.append(AlignmentOp(
                op="del",
                ref_token=ref[i - 1],
                hyp_token=None,
                ref_idx=i - 1,
                hyp_idx=None,
            ))
            i -= 1
        else:
            ops.append(AlignmentOp(
                op="ins",
                ref_token=None,
                hyp_token=hyp[j - 1],
                ref_idx=None,
                hyp_idx=j - 1,
            ))
            j -= 1

    ops.reverse()
    return ops, dp[n][m]
