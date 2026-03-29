# Spanish EIT Scorer - Start Here

**Version**: 2.0  
**Status**: ✅ **PRODUCTION-READY**  
**Last Updated**: March 29, 2026

---

## 🎯 What Is This?

A **deterministic, rubric-based scoring system** for Spanish Elicited Imitation Tasks (EIT) with **research-grade evaluation metrics**.

**Key Features**:
- Scores Spanish EIT responses on 0–4 scale (Ortega 2000)
- Fully deterministic and reproducible
- Includes Cohen's Kappa, Accuracy, and MAE for validation
- Excel integration for batch processing
- 108 tests (100% passing)

---

## ⚡ Quick Start

### 1. Score an Excel File
```bash
python score_excel.py input.xlsx output.xlsx
```

**Input Format**:
- Column A: Sentence ID
- Column B: Stimulus (reference)
- Column C: Transcription (response)
- Column D: Score (optional human scores)

**Output**: Scored Excel file + evaluation metrics (if human scores present)

### 2. Run Demo
```bash
python demo_evaluation.py
```

Shows 10 sample responses with evaluation metrics.

### 3. Run Tests
```bash
python -m pytest tests/ -v
```

Verifies all 108 tests pass.

---

## 📚 Documentation Guide

### For First-Time Users
1. **START_HERE.md** (this file) - Quick overview
2. **EVALUATION_QUICK_START.md** - Evaluation layer basics
3. **QUICK_REFERENCE.md** - Rules and features lookup

### For Developers
1. **ARCHITECTURE.md** - System design
2. **SCORING_GUIDE.md** - Scoring methodology
3. **REFACTORING_COMPLETE.md** - Implementation details

### For Researchers
1. **EVALUATION_LAYER_COMPLETE.md** - Evaluation metrics details
2. **FINAL_SYSTEM_REPORT.md** - Comprehensive system report
3. **VERIFICATION_CHECKLIST.md** - Complete verification

### For Reference
1. **SYSTEM_STATUS.md** - Current system status
2. **DOCUMENTATION_INDEX.md** - All documentation files

---

## 🔑 Key Concepts

### Scoring Scale (Ortega 2000)
- **4**: Perfect match (0 edits)
- **3**: Meaning preserved (≥80% coverage, ≤3 edits)
- **2**: Partial meaning (≥50% coverage)
- **1**: Minimal meaning (>0% coverage)
- **0**: No meaning or gibberish

### Evaluation Metrics
- **Cohen's Kappa**: Agreement beyond chance (target: ≥0.70)
- **Accuracy**: Exact match rate (target: ≥85%)
- **MAE**: Average error (target: <0.5)

### Research Validity
✅ **RESEARCH-VALID** when all three criteria met:
- Accuracy ≥85%
- Weighted κ ≥0.70
- MAE <0.5

---

## 📂 Project Structure

```
spanish_eit_scorer/
├── eit_scorer/              ← Core package
│   ├── core/                ← Scoring engine
│   ├── evaluation/          ← Evaluation metrics
│   ├── utils/               ← I/O utilities
│   └── config/              ← Rubric configuration
├── tests/                   ← 108 tests (100% passing)
├── results/                 ← Output directory
├── score_excel.py           ← Excel scoring CLI
├── demo_evaluation.py       ← Evaluation demo
└── [Documentation files]
```

---

## 🎓 Common Tasks

### Score Responses
```bash
python score_excel.py input.xlsx output.xlsx
```

### Evaluate Agreement
```python
from eit_scorer.evaluation.agreement import evaluate_agreement

metrics = evaluate_agreement(
    y_true=[4, 3, 2, 1],  # Human
    y_pred=[4, 3, 2, 0],  # Auto
)
print(metrics.detailed_report())
```

### Score Single Response
```python
from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse

rubric = load_rubric("eit_scorer/config/default_rubric.yaml")

item = EITItem(
    item_id="1",
    reference="Quiero cortarme el pelo",
    max_points=4,
)

response = EITResponse(
    participant_id="P001",
    item_id="1",
    response_text="Quiero cortarme el pelo",
)

scored = score_response(item, response, rubric)
print(f"Score: {scored.score}/4")
```

---

## ✅ System Status

| Component | Status | Notes |
|-----------|--------|-------|
| Scoring Engine | ✅ | Deterministic, rule-based |
| Evaluation Layer | ✅ | Cohen's Kappa, Accuracy, MAE |
| Excel Integration | ✅ | Multi-sheet, batch processing |
| Tests | ✅ | 108/108 passing (100%) |
| Documentation | ✅ | Comprehensive and complete |
| Production Ready | ✅ | Validated and tested |

---

## 🆘 Need Help?

### Quick Answers
- **How do I score responses?** → Run `python score_excel.py input.xlsx output.xlsx`
- **How do I evaluate agreement?** → Add human scores to column D, run scoring
- **Where are metrics saved?** → `results/summary_metrics.json`
- **How do I interpret kappa?** → ≥0.70 is good, ≥0.80 is excellent
- **Is the system validated?** → Yes, 90% accuracy, κ=0.851 on test data

### Documentation
- **Quick lookup**: `EVALUATION_QUICK_START.md`
- **Full details**: `EVALUATION_LAYER_COMPLETE.md`
- **System overview**: `FINAL_SYSTEM_REPORT.md`

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run evaluation tests only
python -m pytest tests/test_evaluation_agreement.py -v

# Run demo
python demo_evaluation.py
```

---

## 🎉 What's New in v2.0

### Evaluation Layer
- ✅ Cohen's Kappa (unweighted & weighted)
- ✅ Accuracy (exact match rate)
- ✅ MAE (mean absolute error)
- ✅ Automatic interpretation
- ✅ Research validity assessment
- ✅ JSON export

### Excel Integration
- ✅ Automatic human score extraction
- ✅ Evaluation metrics computation
- ✅ Detailed console reports
- ✅ JSON output

### Testing
- ✅ 17 new evaluation tests
- ✅ 108 total tests (100% passing)
- ✅ Comprehensive validation

---

## 📞 Support

For detailed information, see:
- `FINAL_SYSTEM_REPORT.md` - Complete system overview
- `EVALUATION_LAYER_COMPLETE.md` - Evaluation details
- `QUICK_REFERENCE.md` - Rules and features

**System Status**: ✅ **READY FOR PRODUCTION AND RESEARCH USE**
