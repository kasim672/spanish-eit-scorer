# Installation Guide

Complete setup instructions for the Spanish EIT Scorer.

---

## Prerequisites

- **Python**: 3.11 or higher
- **Operating System**: Linux, macOS, or Windows
- **Git**: For cloning the repository

---

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd spanish_eit_scorer
```

### 2. Activate Virtual Environment

The repository includes a pre-configured virtual environment (`.venv`):

```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**Note**: If `.venv` doesn't exist or you prefer a fresh environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.lock.txt
```

**Core Dependencies**:
- `pydantic` - Data validation
- `openpyxl` - Excel I/O
- `scikit-learn` - Cohen's Kappa (optional, has built-in fallback)
- `pytest` - Testing framework

### 4. Verify Installation

```bash
# Run test suite (should see 108 passed)
python -m pytest tests/ -q

# Run demo
python scripts/demo_evaluation.py
```

---

## Optional: DataBuilder Setup

**Note**: The core scoring system does NOT require spaCy. This is only needed for the optional DataBuilder feature.

### Install spaCy Model

```bash
pip install spacy
python -m spacy download es_core_news_sm
```

### Test DataBuilder

```bash
python scripts/databuilder.py --count 10 --output data/test.jsonl
```

---

## Quick Validation

### Test the System

```bash
# 1. Run all tests
python -m pytest tests/ -v

# Expected: 108 passed in ~2.2s

# 2. Run evaluation demo
python scripts/demo_evaluation.py

# Expected: κ = 0.851, 90% accuracy

# 3. Score sample Excel file
python scripts/score_excel.py "AutoEIT Sample Transcriptions for Scoring.xlsx" "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"

# Expected: 120 responses scored successfully
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'eit_scorer'"

**Solution**: Ensure you're in the project root and virtual environment is activated

```bash
# Check current directory
pwd  # Should show .../spanish_eit_scorer

# Activate virtual environment
source .venv/bin/activate
```

### Issue: "No module named 'openpyxl'"

**Solution**: Install dependencies

```bash
pip install -r requirements.lock.txt
```

### Issue: "No module named 'spacy'"

**Solution**: This is only needed for DataBuilder (optional)

```bash
# If you need DataBuilder
pip install spacy
python -m spacy download es_core_news_sm

# If you don't need DataBuilder
# Skip this - core scoring works without spaCy
```

### Issue: Tests fail

**Solution**: Ensure all dependencies installed

```bash
# Reinstall dependencies
pip install -r requirements.lock.txt

# Run tests with verbose output
python -m pytest tests/ -v --tb=short
```

---

## System Requirements

### Minimum Requirements

- **CPU**: Any modern processor
- **RAM**: 512 MB
- **Disk**: 100 MB
- **Python**: 3.11+

### Recommended Requirements

- **CPU**: 2+ cores
- **RAM**: 2 GB
- **Disk**: 500 MB (with spaCy model)
- **Python**: 3.11+

---

## Verification Checklist

After installation, verify:

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip list | grep pydantic`)
- [ ] Tests pass (`python -m pytest tests/ -q`)
- [ ] Demo runs (`python scripts/demo_evaluation.py`)
- [ ] Excel scoring works
- [ ] Results directory created (`ls results/`)

---

## Next Steps

After successful installation:

1. **Run Demo**: `python scripts/demo_evaluation.py`
2. **Score Data**: `python scripts/score_excel.py input.xlsx output.xlsx`
3. **Read Docs**: See [docs/](docs/) for technical details
4. **Explore Code**: Check [docs/architecture.md](docs/architecture.md)

---

## Support

### Documentation

- **Overview**: [README.md](README.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Scoring Logic**: [docs/scoring_logic.md](docs/scoring_logic.md)
- **Evaluation**: [docs/evaluation.md](docs/evaluation.md)

### Testing

- Run tests: `python -m pytest tests/ -v`
- View test list: `python -m pytest tests/ --co -q`
- Run specific test: `python -m pytest tests/test_evaluation_agreement.py -v`

---

## Installation Complete! 🎉

You're ready to use the Spanish EIT Scorer. Start with:

```bash
python scripts/demo_evaluation.py
```

**Status**: ✅ **READY TO USE**
