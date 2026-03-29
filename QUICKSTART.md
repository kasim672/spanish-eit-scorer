# Quick Start Guide

Get started with the Spanish EIT Scorer in 2 minutes.

---

## Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.lock.txt

# Verify installation
python -m pytest tests/ -q
```

**Expected**: `108 passed in ~2.5s`

---

## Usage

### Score Excel File

```bash
python scripts/score_excel.py "AutoEIT Sample Transcriptions for Scoring.xlsx" "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"
```

**Input**: Excel with columns A=ID, B=Stimulus, C=Transcription, D=Score (optional)  
**Output**: Scored Excel + evaluation metrics (if human scores present)

### Run Demo

```bash
python scripts/demo_evaluation.py
```

**Shows**: 10 sample scores + evaluation metrics (κ = 0.851)

### Run Tests

```bash
python -m pytest tests/ -v
```

**Shows**: All 108 tests with detailed output

---

## Quick Validation

```bash
# Complete validation (one command)
python -m pytest tests/ -q && \
python scripts/demo_evaluation.py | tail -30 && \
echo "✅ SYSTEM VALIDATED"
```

---

## Python API

```python
from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse

# Load rubric
rubric = load_rubric("eit_scorer/config/default_rubric.yaml")

# Score a response
item = EITItem(item_id="1", reference="Quiero cortarme el pelo", max_points=4)
response = EITResponse(participant_id="P001", item_id="1", response_text="Quiero cortarme el pelo")
scored = score_response(item, response, rubric)

print(f"Score: {scored.score}/4")
```

---

## Evaluation

```python
from eit_scorer.evaluation.agreement import evaluate_agreement

metrics = evaluate_agreement(
    y_true=[4, 3, 2, 1],  # Human scores
    y_pred=[4, 3, 2, 0],  # Auto scores
)

print(metrics.detailed_report())
```

---

## Optional: DataBuilder

```bash
# Install spaCy model (one-time)
python -m spacy download es_core_news_sm

# Generate synthetic data
python scripts/databuilder.py --count 100 --output data/synth/dataset.jsonl
```

---

## Documentation

- **[README.md](README.md)** - Complete overview
- **[INSTALLATION.md](INSTALLATION.md)** - Detailed setup
- **[docs/architecture.md](docs/architecture.md)** - System design
- **[docs/scoring_logic.md](docs/scoring_logic.md)** - Scoring methodology
- **[docs/evaluation.md](docs/evaluation.md)** - Evaluation metrics

---

## Support

### Common Issues

**"ModuleNotFoundError: No module named 'eit_scorer'"**
```bash
source .venv/bin/activate
pip install -e .
```

**"No module named 'openpyxl'"**
```bash
pip install -r requirements.lock.txt
```

**Tests fail**
```bash
python -m pytest tests/ -v --tb=short
```

---

## Next Steps

1. Read [README.md](README.md) for complete overview
2. Check [docs/architecture.md](docs/architecture.md) for system design
3. Review [docs/scoring_logic.md](docs/scoring_logic.md) for methodology
4. Explore the code in `eit_scorer/`

---

**Status**: ✅ **READY TO USE**
