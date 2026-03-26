# System Architecture

## Overview

The Spanish EIT Automated Scorer is a deterministic, rubric-driven pipeline
that replaces inconsistent LLM-based or human scoring with rule-based logic
that always produces the same result for the same input.

```
┌────────────────────────────────────────────────────────────────────────┐
│                     END-TO-END PIPELINE                                 │
│                                                                          │
│  Input: EITItem (reference) + EITResponse (learner text)                │
│                         │                                                │
│  ┌──────────────────────▼───────────────────────────────────────────┐  │
│  │  1. NORMALIZATION (normalization.py)                              │  │
│  │     lowercase · strip punctuation · remove fillers               │  │
│  │     → display_normalized  (for reports)                          │  │
│  │     → match_normalized    (for alignment; optional accent fold)   │  │
│  └──────────────────────┬───────────────────────────────────────────┘  │
│                         │                                                │
│  ┌──────────────────────▼───────────────────────────────────────────┐  │
│  │  2. TOKENIZATION (tokenization.py)                                │  │
│  │     whitespace split · enclitic splitting (dímelo→[dime,lo])     │  │
│  │     + contraction expansion (al→[a,el], del→[de,el])             │  │
│  └──────────────────────┬───────────────────────────────────────────┘  │
│                         │                                                │
│  ┌──────────────────────▼───────────────────────────────────────────┐  │
│  │  3. ALIGNMENT (alignment.py)                                      │  │
│  │     Needleman-Wunsch global alignment                             │  │
│  │     Deterministic tie-breaking: diagonal > del > ins              │  │
│  │     → list[AlignmentOp]  (match / sub / ins / del)               │  │
│  └──────────────────────┬───────────────────────────────────────────┘  │
│                         │                                                │
│  ┌──────────────────────▼───────────────────────────────────────────┐  │
│  │  4. ERROR LABELING (error_labeling.py)                            │  │
│  │     count by type: match / sub / ins / del                        │  │
│  │     classify subs: function_sub vs content_sub                    │  │
│  │     compute overlap_ratio (set-based)                             │  │
│  └──────────────────────┬───────────────────────────────────────────┘  │
│                         │                                                │
│  ┌──────────────────────▼───────────────────────────────────────────┐  │
│  │  5. RULE ENGINE (scoring.py)                                      │  │
│  │     ScoreContext: {total_edits, content_subs, overlap_ratio,      │  │
│  │                    hyp_min_tokens}                                 │  │
│  │     Apply rules from rubric YAML in order                         │  │
│  │     First match wins · score clamped to [0, max_points]           │  │
│  └──────────────────────┬───────────────────────────────────────────┘  │
│                         │                                                │
│  ┌──────────────────────▼───────────────────────────────────────────┐  │
│  │  6. FINGERPRINT (scoring.py)                                      │  │
│  │     SHA-256 over: rubric identity + normalized texts +            │  │
│  │     tokens + alignment ops + rule IDs + score                     │  │
│  │     Proves: same input ↔ same fingerprint (always)                │  │
│  └──────────────────────┬───────────────────────────────────────────┘  │
│                         │                                                │
│                  ScoredSentence (output)                                 │
│                  + ScoringTrace (full audit)                             │
└────────────────────────────────────────────────────────────────────────┘
```

## Determinism Guarantees

| Property | How enforced |
|----------|-------------|
| Normalization | Pure functions, no randomness, regex-based |
| Tokenization | Whitespace split + deterministic longest-match enclitic peeling |
| Alignment | Needleman-Wunsch with explicit tie-breaking order |
| Rule evaluation | Rules applied in YAML file order; first match wins |
| Fingerprint | SHA-256 (not Python `hash()`) — seed-independent |
| No side effects | All pipeline functions are pure (no global state mutation) |

## Component Map

```
eit_scorer/
├── config/
│   └── default_rubric.yaml    ← SINGLE SOURCE OF TRUTH for all scoring rules
├── core/
│   ├── normalization.py        ← Stage 1: text cleaning
│   ├── tokenization.py         ← Stage 2: tokenization + enclitics
│   ├── alignment.py            ← Stage 3: Needleman-Wunsch
│   ├── error_labeling.py       ← Stage 4: error counting
│   ├── rubric.py               ← YAML → RubricConfig
│   └── scoring.py              ← Stage 5-6: rules + fingerprint
├── data/
│   └── models.py               ← Pydantic domain models
├── evaluation/
│   ├── metrics.py              ← Cohen's κ, accuracy, MAE
│   └── analysis.py             ← Grouped agreement reports
├── synthetic/
│   ├── stimuli.py              ← 60 EIT stimulus sentences
│   ├── errors.py               ← spaCy-powered error engine
│   └── generate.py             ← Large-scale dataset generator (500k+)
├── utils/
│   ├── io.py                   ← File loaders
│   ├── jsonl.py                ← JSONL read/write
│   └── stable_hash.py          ← SHA-256 fingerprinting
└── cli.py                      ← eit-score CLI (synth/score/eval)

apps/
└── api/
    └── main.py                 ← FastAPI REST API + browser UI
```

## Validation Workflow

```
1. Collect gold standard
   → Have human raters score N sentences (N ≥ 100 recommended)
   → Store as JSONL: {participant_id, item_id, response_text,
                      human_rater_a, human_rater_b}

2. Run automated scoring
   → eit-score score --items items.json --dataset dataset.jsonl

3. Evaluate agreement
   → eit-score eval --scored scored.jsonl --human adjudicated --group band

4. Check targets
   → Sentence accuracy ≥ 90%
   → Max participant total diff < 10pt

5. Diagnose gaps
   → Use --group item to find hard items
   → Use --group band to find struggling proficiency levels
   → Review audit trails for systematic rule failures

6. Refine rubric
   → Edit default_rubric.yaml (rules section only)
   → Re-run steps 2-4
   → Commit rubric version + record agreement metrics
```

## Reproducibility Checklist

For a publication-ready run, record and commit:
- `rubric.version` from the YAML
- Package version (`__version__`)
- Git commit hash
- `requirements.lock.txt` snapshot
- Evaluation report (JSON output from `eit-score eval`)
- Dataset fingerprints (from `metadata.json` after `eit-gen`)
