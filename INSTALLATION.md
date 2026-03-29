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

### 2. Set Up Virtual Environment

**Option A: Use Existing .venv (Recommended)**
```bash
# Activate existing virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows
```

**Option B: Create New Virtual Environment**
```bash
# Create new virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.lock.txt
```

**Core Dependencies**:
- `pydantic` - Data validation
- `openpyxl` - Excel I/O
- `scikit-learn` - Cohen's Kappa (optional, has built-in fallback)
- `pytest` - Testing framework

### 4. Install spaCy Model (OPTIONAL)
**Only required for DataBuilder feature**

```bash
python -m spacy download es_core_news_sm
```

**Note**: The core scoring system does NOT require spaCy. This is only needed for the optional DataBuilder feature that generates synthetic datasets.

### 5. Verify Installation
```bash
# Run test suite (should see 108 passed)
python -m pytest tests/ -q

# Run quick demo
python scripts/demo_evaluation.py
```

---

## Quick Validation

### Test the System
```bash
# 1. Run all tests
python -m pytest tests/ -v

# Expected output: 108 passed in ~2.2s

# 2. Score sample Excel file
python scripts/score_excel.py "AutoEIT Sample Transcriptions for Scoring.xlsx" "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"

# Expected output: Successfully scored 120 responses

# 3. View results
cat results/summary_metrics.json
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'eit_scorer'"
**Solution**: Ensure you're in the project root directory and virtual environment is activated

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
**Solution**: This is only needed for DataBuilder (optional feature)

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

## Development Setup

### Install Development Dependencies
```bash
# Install with development extras
pip install -e ".[dev]"

# Or install manually
pip install pytest pytest-cov black mypy
```

### Run Tests with Coverage
```bash
python -m pytest tests/ --cov=eit_scorer --cov-report=html
```

### Code Formatting
```bash
# Format code
black eit_scorer/ tests/ scripts/

# Type checking
mypy eit_scorer/
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
- [ ] Excel scoring works (`python scripts/score_excel.py ...`)
- [ ] Results directory created (`ls results/`)

---

## Next Steps

After successful installation:

1. **Read**: [START_HERE.md](START_HERE.md) for quick overview
2. **Try**: Run `python scripts/demo_evaluation.py`
3. **Score**: Process your Excel file with `python scripts/score_excel.py`
4. **Learn**: Read [docs/EVALUATION_QUICK_START.md](docs/EVALUATION_QUICK_START.md)
5. **Explore**: Check [docs/FINAL_SYSTEM_REPORT.md](docs/FINAL_SYSTEM_REPORT.md)

---

## Support

### Documentation
- Quick start: [START_HERE.md](START_HERE.md)
- Evaluation guide: [docs/EVALUATION_QUICK_START.md](docs/EVALUATION_QUICK_START.md)
- Full documentation: [docs/](docs/)

### Testing
- Run tests: `python -m pytest tests/ -v`
- View test list: `python -m pytest tests/ --co -q`
- Run specific test: `python -m pytest tests/test_evaluation_agreement.py -v`

### Issues
- Check documentation in `docs/` folder
- Review test files for examples
- Open an issue on GitHub

---

## Installation Complete! 🎉

You're ready to use the Spanish EIT Scorer. Start with:

```bash
python scripts/demo_evaluation.py
```

**Status**: ✅ **READY TO USE**
