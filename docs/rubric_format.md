# Rubric Format Reference

The scoring rubric lives entirely in `eit_scorer/config/default_rubric.yaml`.
This file is the **single source of truth** — all rule changes happen here.

## Top-Level Schema

```yaml
rubric:
  name:    "My Rubric Name"
  version: "1.0"

  scale:
    max_points_per_item: 4    # 0–4 scale (change to 2 for 0–2 scale)

  rules:
    - id:  R4_perfect
      ...

  normalization: { ... }
  tokenization:  { ... }
  alignment:     { ... }
  error_labeling:
    function_words: [...]
```

## Rule Structure

```yaml
rules:
  - id:          R4_perfect          # Unique identifier (used in audit trail)
    description: "No edits — perfect match"
    when:
      max_edits: 0                   # All conditions must hold (AND)
    then:
      score: 4
```

Rules are evaluated **in order**. The **first** matching rule wins.
Put more specific rules before more general ones.

## Supported Condition Fields

| Field | Meaning | Example |
|-------|---------|---------|
| `max_edits` | `total_edits ≤ N` | `max_edits: 2` |
| `max_content_subs` | `content_subs ≤ N` | `max_content_subs: 1` |
| `min_token_overlap_ratio` | `overlap_ratio ≥ X` | `min_token_overlap_ratio: 0.5` |
| `hyp_min_tokens` | `len(hyp_tokens) ≥ N` | `hyp_min_tokens: 3` |
| `{field}_{op}: value` | Parametric operator | `total_edits_lt: 3` |

**Parametric operators:** `_eq` `_ne` `_lt` `_le` `_gt` `_ge`

Examples:
```yaml
when:
  total_edits_le: 2         # total_edits <= 2
  content_subs_eq: 0        # content_subs == 0
  overlap_ratio_ge: 0.6     # overlap_ratio >= 0.6
  hyp_min_tokens_lt: 2      # len(hyp) < 2
```

An empty `when: {}` always matches (use as catchall last rule).

## Complete Default Rubric Logic

| Rule ID | Condition | Score |
|---------|-----------|-------|
| `R0_empty_or_too_short` | `len(hyp) < 2` | 0 |
| `R4_perfect` | `total_edits == 0` | 4 |
| `R3_minor` | `total_edits ≤ 2 AND content_subs == 0` | 3 |
| `R3b_minor_with_function_sub` | `total_edits ≤ 2 AND content_subs == 0 AND overlap ≥ 0.75` | 3 |
| `R2_moderate` | `total_edits ≤ 4 AND content_subs ≤ 1 AND overlap ≥ 0.50` | 2 |
| `R2b_low_overlap_few_edits` | `total_edits ≤ 3 AND overlap ≥ 0.40` | 2 |
| `R1_heavy_but_some_overlap` | `overlap ≥ 0.25 AND len(hyp) ≥ 2` | 1 |
| `R0_other` | (catchall) | 0 |

## Changing the Scale (e.g., 0–2)

1. Change `scale.max_points_per_item: 2`
2. Adjust all `then.score:` values to 0, 1, or 2
3. Increment `version`
4. Add a changelog comment in the file
5. Re-run `eit-score eval` to verify agreement is maintained

## Adding a Custom Rule

```yaml
rules:
  # ... existing rules ...

  - id:          R2_custom_no_verb
    description: "No verb present (content_subs > 2 but overlap decent)"
    when:
      content_subs_gt:         2
      min_token_overlap_ratio: 0.30
    then:
      score: 1
```

## Versioning Policy

Every rubric change **must**:
1. Increment `rubric.version`
2. Add a YAML comment with date, author, and rationale
3. Be re-validated against the gold standard (run `eit-score eval`)
4. Have the new agreement metrics committed alongside the rubric change

```yaml
# CHANGELOG
# v1.1 — 2024-06-01 — Adjusted R2_moderate overlap threshold 0.45→0.50
#         Reason: Validation showed over-scoring at overlap=0.46-0.50
# v1.0 — 2024-01-01 — Initial release
```
