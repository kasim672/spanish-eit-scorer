# Installation Guide

Complete setup instructions for the Spanish EIT Automated Scorer.

---

## Requirements

- Python 3.9 or higher
- pip
- ~200 MB disk space (+ ~13–560 MB for spaCy model, depending on size)

---

## Step 1 — Get the code

```bash
git clone https://github.com/your-lab/spanish-eit-scorer
cd spanish_eit_scorer
```

Or if you have the zip:

```bash
unzip spanish-eit-scorer.zip
cd spanish_eit_scorer
```

---

## Step 2 — Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

You should see `(.venv)` in your prompt.

> If the project already has a `.venv` folder (as distributed), just activate it:
> ```bash
> source .venv/bin/activate
> ```

---

## Step 3 — Install dependencies

### Option A — Exact pinned versions (recommended for reproducibility)

```bash
pip install -r requirements.lock.txt
```

### Option B — Latest compatible versions

```bash
pip install -e ".[dev]"
```

---

## Step 4 — Install the package in editable mode

```bash
pip install -e .
```

This registers the `eit-score`, `eit-api`, and `eit-gen` CLI commands.

> If you see `ModuleNotFoundError: No module named 'setuptools.backends'`,
> your setuptools is outdated. The `pyproject.toml` already uses the
> compatible `setuptools.build_meta` backend — just upgrade pip first:
> ```bash
> pip install --upgrade pip setuptools
> pip install -e .
> ```

---

## Step 5 — Install a spaCy Spanish model

The scorer uses spaCy for morphologically-aware error generation in the
synthetic dataset pipeline. It falls back gracefully without a model,
but installation is recommended for realistic outputs.

```bash
# Lightweight — 12 MB, fastest (good for testing)
python -m spacy download es_core_news_sm

# Recommended — 43 MB, good accuracy/speed balance
python -m spacy download es_core_news_md

# Highest accuracy — 560 MB (for production use)
python -m spacy download es_core_news_lg
```

The system auto-selects the best installed model: `lg > md > sm > rule-based fallback`.

---

## Step 6 — Install pytest (for running tests)

```bash
pip install pytest pytest-cov
```

---

## Step 7 — Verify everything works

Run this quick check:

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

Expected output:
```
Score: 2
Rule:  ['R2_moderate']
OK ✓
```

Then run the full test suite:

```bash
python -m pytest tests/ -v
```

Expected: `28 passed`

---

## Full pipeline walkthrough

Once installed, run the complete pipeline end-to-end:

```bash
# 1. Generate a synthetic dataset (100 participants × 60 items)
eit-score synth --out data/synth --participants 100 --seed 42

# 2. Score it
eit-score score \
  --items   data/synth/items.json \
  --dataset data/synth/dataset.jsonl \
  --out     data/synth/scored.jsonl

# 3. Evaluate agreement vs simulated human raters
eit-score eval \
  --scored data/synth/scored.jsonl \
  --human  adjudicated \
  --group  band

# 4. Start the web API
eit-api --host 0.0.0.0 --port 8000
# → open http://localhost:8000  (browser UI)
# → open http://localhost:8000/docs  (Swagger / interactive API)
```

---

## Troubleshooting

### `No module named 'setuptools.backends'`

Your setuptools version is < 68. Fixed in `pyproject.toml` already.
If it still occurs:

```bash
pip install --upgrade pip setuptools
pip install -e .
```

### `No module named pytest`

pytest is not installed in your active venv:

```bash
pip install pytest pytest-cov
```

### `No module named 'eit_scorer'`

The package isn't installed yet. Run:

```bash
pip install -e .
```

### `FileNotFoundError: Rubric not found`

You're running from the wrong directory. Always run commands from the
project root (`spanish_eit_scorer/`), not from a subdirectory.

### spaCy model not found

The scorer falls back to rule-based errors automatically. To install:

```bash
python -m spacy download es_core_news_sm
```

### Port 8000 already in use

```bash
eit-api --port 8001
```

---

## Dependencies overview

| Package | Version | Purpose |
|---------|---------|---------|
| pyyaml | ≥6.0 | Rubric YAML loading |
| pydantic | ≥2.0 | Data models + validation |
| numpy | ≥1.24 | Numerical operations |
| pandas | ≥2.0 | Data handling |
| scikit-learn | ≥1.3 | Cohen's κ metrics |
| tqdm | ≥4.65 | Progress bars |
| spacy | ≥3.5 | Spanish NLP (optional but recommended) |
| fastapi | ≥0.100 | REST API server |
| uvicorn | ≥0.22 | ASGI server |
| python-multipart | ≥0.0.6 | File upload support |

Full pinned versions: see [`requirements.lock.txt`](requirements.lock.txt)

---

## Environment summary (tested configuration)

```
Python        3.11.8
spaCy         3.7.2
es_core_news_sm  3.7.0
pydantic      2.5.3
fastapi       0.104.1
scikit-learn  1.3.2
OS            Linux (Ubuntu 24.04)
```
