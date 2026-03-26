# Spanish EIT Automated Scorer

**Deterministic · Rubric-driven · Reproducible · Research-grade**

Automated scoring system for the Spanish **Elicited Imitation Task (EIT)**.
Eliminates scoring variability by applying a formalized rubric through a
transparent, rule-based pipeline — producing the **same score** for the
**same input, every time**, with a cryptographic fingerprint to prove it.

> **New to the project? Start with [INSTALLATION.md](INSTALLATION.md)** for a
> step-by-step setup guide including virtual environment setup, spaCy model
> download, and verification commands.

---

## Table of Contents

1. [What it does](#what-it-does)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [CLI Reference](#cli-reference)
5. [Dataset Generation](#dataset-generation)
6. [API Server](#api-server)
7. [Scoring Pipeline](#scoring-pipeline)
8. [Rubric Format](#rubric-format)
9. [Validation Targets](#validation-targets)
10. [Project Structure](#project-structure)
11. [Running Tests](#running-tests)
12. [Reproducibility](#reproducibility)

---

## What It Does

Replaces manual, inconsistent human scoring of EIT transcriptions with a
deterministic pipeline that:

- **Normalizes** text (lowercase, strip punctuation, remove fillers like *eh*, *um*)
- **Tokenizes** with Spanish enclitic splitting (`dímelo` → `dime`, `lo`)
- **Aligns** learner response to target using Needleman-Wunsch global alignment
- **Counts** errors: insertions, deletions, substitutions (function vs. content words)
- **Applies** a YAML-configurable rubric (rule-based, first-match-wins)
- **Produces** a score + complete audit trail + SHA-256 fingerprint per sentence

---

## Installation

For full setup instructions including virtual environment creation, dependency
installation, spaCy model download, and troubleshooting, see:

**[→ INSTALLATION.md](INSTALLATION.md)**

### TL;DR (if you already have a venv active)

```bash
pip install -r requirements.lock.txt
pip install -e .
python -m spacy download es_core_news_sm
```

### Verify it works

```bash
python -c "
from eit_scorer.core.rubric  import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models  import EITItem, EITResponse

rubric = load_rubric('eit_scorer/config/default_rubric.yaml')
item   = EITItem(item_id='s01', reference='El niño come una manzana', max_points=4)
resp   = EITResponse(participant_id='P001', item_id='s01', response_text='El niño come manzana')
result = score_response(item, resp, rubric)
print('Score:', result.score)
print('Rule: ', result.trace.applied_rule_ids)
print('OK ✓')
"
```

Expected:
```
Score: 2
Rule:  ['R2_moderate']
OK ✓
```

---

## Quick Start

### Score a single sentence (Python)

```python
from eit_scorer.core.rubric  import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models  import EITItem, EITResponse

rubric = load_rubric("eit_scorer/config/default_rubric.yaml")

item = EITItem(item_id="s01",
               reference="El niño come una manzana roja",
               max_points=4)

resp = EITResponse(participant_id="P001",
                   item_id="s01",
                   response_text="El niño come manzana")

result = score_response(item, resp, rubric)

print(result.score)                           # → 2
print(result.trace.total_edits)               # → 2
print(result.trace.applied_rule_ids)          # → ['R2_moderate']
print(result.trace.deterministic_fingerprint) # → abc123… (reproducible)
print("\n".join(result.trace.audit()))        # → full audit trail
```

### Score multiple participants (Python)

```python
from collections import defaultdict
from eit_scorer.core.rubric  import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models  import EITItem, EITResponse, ParticipantSummary

rubric = load_rubric("eit_scorer/config/default_rubric.yaml")
items  = [
    EITItem(item_id="s01", reference="El niño come una manzana", max_points=4),
    EITItem(item_id="s02", reference="Ella corre rápidamente",   max_points=4),
]
responses = [
    EITResponse(participant_id="P001", item_id="s01", response_text="El niño come manzana"),
    EITResponse(participant_id="P001", item_id="s02", response_text="Ella corre"),
    EITResponse(participant_id="P002", item_id="s01", response_text="El niño come una manzana"),
    EITResponse(participant_id="P002", item_id="s02", response_text="Ella corre rápidamente"),
]

items_map = {it.item_id: it for it in items}
scored    = [score_response(items_map[r.item_id], r, rubric) for r in responses]

by_p = defaultdict(list)
for ss in scored:
    by_p[ss.participant_id].append(ss)

for pid, sents in by_p.items():
    s = ParticipantSummary.from_scored(pid, sents)
    print(f"{pid}: {s.total_score}/{s.max_possible} ({s.pct_max:.1f}%)")
```

---

## CLI Reference

All commands use the `eit-score` entry point (available after `pip install -e .`).

### Generate synthetic data

```bash
# 100 participants × 60 items = 6,000 responses
eit-score synth --out data/synth --participants 100 --seed 42

# Faster, no spaCy
eit-score synth --out data/synth --participants 100 --seed 42 --no-spacy
```

### Score a dataset

```bash
eit-score score \
  --items   data/synth/items.json \
  --dataset data/synth/dataset.jsonl \
  --out     data/synth/scored.jsonl
```

### Evaluate against human raters

```bash
# Basic
eit-score eval --scored data/synth/scored.jsonl

# Grouped by proficiency band
eit-score eval --scored data/synth/scored.jsonl --group band

# Grouped by EIT item
eit-score eval --scored data/synth/scored.jsonl --group item

# Custom human score field
eit-score eval --scored data/synth/scored.jsonl \
               --human human_rater_a \
               --within-points 8.0
```

---

## Dataset Generation

### Small / medium datasets

```bash
eit-score synth --out data/small --participants 50 --seed 42
# → 3,000 responses

eit-gen --n 100000 --out data/medium --seed 42
# → ~100,000 records, ~18 seconds
```

### Large dataset (500,000+ records)

```bash
eit-gen --n 500000 --out data/large --seed 42 --no-spacy
# → ~90 seconds

eit-gen --n 500000 --out data/large --seed 42
# → ~270 seconds with es_core_news_md
```

### Output files

| File | Description |
|------|-------------|
| `items.json` | 60 EIT stimulus sentences |
| `dataset.jsonl` | All learner responses (input) |
| `scored.jsonl` | All scored sentences (output) |
| `summary.csv` | Per-participant total scores |
| `metadata.json` | Generation parameters + score distribution |

### CEFR level distribution

| Level | % of participants | Typical score range |
|-------|-------------------|---------------------|
| A1    | 10%               | 0–1 per sentence    |
| A2    | 18%               | 0–2 per sentence    |
| B1    | 28%               | 1–3 per sentence    |
| B2    | 24%               | 2–4 per sentence    |
| C1    | 12%               | 3–4 per sentence    |
| C2    | 8%                | 4 per sentence      |

---

## API Server

### Start the server

```bash
eit-api                                    # localhost:8000
eit-api --host 0.0.0.0 --port 8080        # custom host/port
eit-api --rubric path/to/my_rubric.yaml   # custom rubric
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Browser UI — paste/upload JSON |
| GET | `/health` | Liveness check + rubric info |
| GET | `/rubric` | Current rubric as JSON |
| POST | `/score` | Score a JSON payload |
| POST | `/score_file` | Score a JSON file upload |
| GET | `/docs` | Interactive Swagger UI |

### POST /score — curl example

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d @examples/api_payload.json
```

### POST /score — example payload

```json
{
  "items": [
    {"item_id": "s01", "reference": "El niño come una manzana roja", "max_points": 4}
  ],
  "responses": [
    {"participant_id": "P001", "item_id": "s01", "response_text": "El niño come una manzana roja"},
    {"participant_id": "P002", "item_id": "s01", "response_text": "El niño come manzana"},
    {"participant_id": "P003", "item_id": "s01", "response_text": ""}
  ]
}
```

---

## Scoring Pipeline

```
raw text
   │
   ▼  normalize_text()
   │  lowercase · strip punctuation · remove fillers (eh, um, …)
   │
   ▼  tokenize()
   │  whitespace split · enclitic split (dímelo → [dime, lo])
   │  + expand contractions (al → [a, el])
   │
   ▼  align_tokens()  [Needleman-Wunsch]
   │  deterministic tie-breaking: diagonal > del > ins
   │  → list[AlignmentOp]: match / sub / ins / del
   │
   ▼  count_errors()
   │  total_edits, content_subs, function_subs
   │  + token_overlap_ratio (set-based)
   │
   ▼  rule engine  [rubric YAML]
   │  ScoreContext → first matching rule → score
   │  clamped to [0, max_points]
   │
   ▼  SHA-256 fingerprint
      rubric + normalized texts + tokens +
      alignment ops + rule IDs + score
      → deterministic_fingerprint
```

---

## Rubric Format

See [`docs/RUBRIC_FORMAT.md`](docs/RUBRIC_FORMAT.md) for full documentation.

Default 0–4 rubric summary:

| Rule | Condition | Score |
|------|-----------|-------|
| `R0_empty_or_too_short` | `< 2 tokens` | 0 |
| `R4_perfect` | `0 edits` | 4 |
| `R3_minor` | `≤2 edits, 0 content subs` | 3 |
| `R2_moderate` | `≤4 edits, ≤1 content sub, overlap≥0.5` | 2 |
| `R1_heavy_but_some_overlap` | `overlap≥0.25` | 1 |
| `R0_other` | catchall | 0 |

To change scoring rules, edit `eit_scorer/config/default_rubric.yaml`.
Never hardcode scoring values in Python.

---

## Validation Targets

| Metric | Target | Current (100p × 60i) |
|--------|--------|----------------------|
| Sentence accuracy | ≥ 90% | 88.1% |
| Weighted κ | ≥ 0.80 | 0.985 (Strong) |
| Max participant diff | < 10 pt | 6.0 pt |
| MAE per sentence | — | 0.059 pts |

---

## Project Structure

```
spanish-eit-scorer/
├── README.md                   ← You are here
├── INSTALLATION.md             ← Full setup guide
├── pyproject.toml              ← Build config + entry points
├── requirements.lock.txt       ← Pinned versions for reproducibility
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── RUBRIC_FORMAT.md
│
├── eit_scorer/
│   ├── config/
│   │   └── default_rubric.yaml ← SINGLE SOURCE OF TRUTH for scoring rules
│   ├── core/
│   │   ├── normalization.py
│   │   ├── tokenization.py
│   │   ├── alignment.py
│   │   ├── error_labeling.py
│   │   ├── rubric.py
│   │   └── scoring.py
│   ├── data/
│   │   └── models.py
│   ├── evaluation/
│   │   ├── metrics.py
│   │   └── analysis.py
│   ├── synthetic/
│   │   ├── stimuli.py
│   │   ├── errors.py
│   │   └── generate.py
│   ├── utils/
│   │   ├── io.py
│   │   ├── jsonl.py
│   │   └── stable_hash.py
│   └── cli.py
│
├── apps/
│   └── api/
│       └── main.py
│
├── examples/
│   ├── api_payload.json
│   └── synth_dataset/
│
└── tests/
    ├── test_alignment.py
    ├── test_determinism.py
    └── test_synth_pipeline.py
```

---

## Running Tests

```bash
# All tests (28 tests)
pytest tests/ -v

# With coverage report
pytest tests/ --cov=eit_scorer --cov-report=html

# Specific modules
pytest tests/test_determinism.py -v
pytest tests/test_alignment.py -v
pytest tests/test_synth_pipeline.py -v
```

---

## Reproducibility

Every scored sentence carries a full audit trail:

```python
result.trace.deterministic_fingerprint  # SHA-256: same input → same output
result.trace.applied_rule_ids           # which rules fired
result.trace.audit()                    # full human-readable decision log
```

For a reproducible research run, record:

```bash
python -c "import eit_scorer; print(eit_scorer.__version__)"
grep "version:" eit_scorer/config/default_rubric.yaml
git rev-parse HEAD
pip freeze > my_run_requirements.txt
```

---

## Citation

```bibtex
@software{spanish_eit_scorer,
  title  = {Spanish EIT Automated Scorer},
  year   = {2024},
  note   = {Deterministic, rubric-driven automated scoring for the
            Spanish Elicited Imitation Task. Version 1.0.0}
}
```
