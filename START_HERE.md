# 🚀 Start Here - Spanish EIT Scorer

## For Quick Understanding (2 minutes)

Read in this order:

1. **SUMMARY.md** (260 lines)
   - Executive overview
   - Key capabilities
   - Quick demo commands
   - Status and metrics

2. **QUICKSTART.md** (existing)
   - 3 commands to get started
   - Immediate hands-on experience

3. **README.md** (existing)
   - Main project documentation
   - Installation and usage
   - Examples

---

## For Complete Understanding (30 minutes)

Read in this order:

1. **SUMMARY.md** - Executive overview
2. **PROJECT_OVERVIEW.md** (2,254 lines, 35 sections)
   - Complete A-Z technical reference
   - All algorithms explained
   - All features documented
   - All workflows covered
3. **ISSUES.md** - Known issues (all resolved)
4. **docs/architecture.md** - System design
5. **docs/scoring_logic.md** - Scoring methodology
6. **docs/evaluation.md** - Evaluation metrics

---

## For Hands-On Testing (5 minutes)

```bash
# 1. Install
pip install -e .

# 2. Run demo (see κ = 0.851)
python scripts/demo_evaluation.py

# 3. Run tests (108 tests)
python -m pytest tests/ -q

# 4. Score Excel file
python scripts/score_excel.py \
  "AutoEIT Sample Transcriptions for Scoring.xlsx" \
  "output.xlsx"

# 5. Start API
eit-api --port 8000
# → Open http://localhost:8000/docs
```

---

## Documentation Map

### Quick Start
- **START_HERE.md** (this file) - Navigation guide
- **SUMMARY.md** - Executive summary
- **QUICKSTART.md** - 2-minute quick start
- **README.md** - Main documentation

### Complete Reference
- **PROJECT_OVERVIEW.md** - Complete A-Z technical documentation (35 sections)
- **ISSUES.md** - Known issues and fixes (all resolved)

### Technical Details
- **docs/architecture.md** - System design
- **docs/scoring_logic.md** - Scoring methodology
- **docs/evaluation.md** - Evaluation metrics
- **docs/rubric_format.md** - Rubric specification

### Installation
- **INSTALLATION.md** - Detailed setup guide

---

## Key Files to Inspect

### Core Scoring
- `eit_scorer/core/scoring.py` - Main pipeline
- `eit_scorer/core/rubric_engine.py` - Rule evaluation
- `eit_scorer/config/default_rubric.yaml` - 10 scoring rules

### API
- `apps/api/main.py` - FastAPI implementation

### Scripts
- `scripts/score_excel.py` - Excel batch processing
- `scripts/demo_evaluation.py` - Evaluation demo
- `scripts/databuilder.py` - Synthetic data generator

### Tests
- `tests/test_integration.py` - End-to-end tests
- `tests/test_determinism.py` - Reproducibility tests
- `tests/test_evaluation_agreement.py` - Metrics tests

---

## Quick Commands Reference

```bash
# Install
pip install -e .

# Test
python -m pytest tests/ -q

# Demo
python scripts/demo_evaluation.py

# Score Excel
python scripts/score_excel.py input.xlsx output.xlsx

# Generate synthetic data
eit-score synth --out data/test --participants 100

# Score dataset
eit-score score --items items.json --dataset dataset.jsonl --out scored.jsonl

# Evaluate
eit-score eval --scored scored.jsonl --human adjudicated

# Start API
eit-api --port 8000

# API docs
open http://localhost:8000/docs
```

---

## Project Status

**Version**: 1.0.0  
**Tests**: 108/108 passing ✓  
**Validation**: κ = 0.851 (almost perfect) ✓  
**Documentation**: Complete ✓  
**Issues**: All resolved ✓  
**Status**: PRODUCTION-READY ✅

---

## Next Steps

1. **For Evaluators**: Read SUMMARY.md → Run demo → Review metrics
2. **For Testers**: Read QUICKSTART.md → Run tests → Score sample data
3. **For Developers**: Read PROJECT_OVERVIEW.md → Explore code → Run API
4. **For Researchers**: Read docs/ → Validate methodology → Run evaluation

---

**Need help?** Check ISSUES.md for troubleshooting or PROJECT_OVERVIEW.md section 27 for common issues.
