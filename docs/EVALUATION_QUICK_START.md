# Evaluation Layer - Quick Start Guide

## 🚀 Quick Start

### Score Excel File with Evaluation
```bash
python score_excel.py input.xlsx output.xlsx
```

**Requirements**: Human scores in column D of input file

**Output**:
- Scored Excel file
- Console evaluation report
- `results/summary_metrics.json`

---

## 📊 Metrics Explained (Simple)

| Metric | What It Means | Good Value |
|--------|---------------|------------|
| **Accuracy** | % of exact matches | ≥85% |
| **Cohen's Kappa** | Agreement beyond chance | ≥0.70 |
| **Weighted Kappa** | Agreement for ordinal scores | ≥0.70 |
| **MAE** | Average error size | <0.5 |

---

## 🎯 Interpretation Scale

### Cohen's Kappa (κ)
- **0.8–1.0**: Almost perfect ✅
- **0.6–0.8**: Substantial ✅
- **0.4–0.6**: Moderate ⚠️
- **0.2–0.4**: Fair ⚠️
- **<0.2**: Slight ❌

### Accuracy
- **≥90%**: Excellent ✅
- **80–90%**: Good ✅
- **70–80%**: Fair ⚠️
- **<70%**: Poor ❌

### MAE (0–4 scale)
- **<0.3**: Excellent ✅
- **0.3–0.5**: Good ✅
- **0.5–0.8**: Fair ⚠️
- **>0.8**: Poor ❌

---

## 💻 Code Examples

### Basic Evaluation
```python
from eit_scorer.evaluation.agreement import evaluate_agreement

metrics = evaluate_agreement(
    y_true=[4, 3, 2, 1],  # Human scores
    y_pred=[4, 3, 2, 0],  # Auto scores
)

print(metrics.detailed_report())
```

### Get Specific Metrics
```python
print(f"Accuracy: {metrics.accuracy:.1f}%")
print(f"Kappa: {metrics.cohens_kappa:.3f}")
print(f"MAE: {metrics.mae:.3f}")
```

### Check Validity
```python
if metrics.accuracy >= 85 and metrics.weighted_kappa >= 0.70:
    print("✅ RESEARCH-VALID")
else:
    print("⚠️ NEEDS IMPROVEMENT")
```

---

## 📁 Output Files

### JSON Metrics (`results/summary_metrics.json`)
```json
{
  "n_samples": 10,
  "accuracy": 90.0,
  "cohens_kappa": 0.851,
  "weighted_kappa": 0.952,
  "mae": 0.1,
  "interpretation": {
    "accuracy": "Excellent (≥90%)",
    "kappa": "Almost perfect agreement",
    "weighted_kappa": "Almost perfect agreement",
    "mae": "Excellent (0.10, 2.5% of scale)"
  }
}
```

---

## 🔍 Troubleshooting

### "No human scores available for evaluation"
**Cause**: Column D in Excel is empty  
**Solution**: Add human scores to column D before running

### "Length mismatch" error
**Cause**: Different number of human vs auto scores  
**Solution**: Ensure all rows have human scores or none do

### Low kappa (<0.5)
**Cause**: Systematic disagreement with human raters  
**Solution**: Review rules in `rubric_engine.py`, adjust thresholds

---

## 🎓 Research Use

### Reporting in Papers
```
The automated scoring system demonstrated substantial agreement 
with human raters (weighted κ = 0.95, accuracy = 90%, MAE = 0.10), 
indicating suitability for research use.
```

### Validation Protocol
1. Collect ≥30 human-scored responses
2. Run evaluation: `python score_excel.py data.xlsx output.xlsx`
3. Check `results/summary_metrics.json`
4. Verify κ ≥0.70, accuracy ≥85%, MAE <0.5
5. Report metrics in publications

---

## ⚡ Quick Commands

```bash
# Score with evaluation
python score_excel.py input.xlsx output.xlsx

# Run demo
python demo_evaluation.py

# Run tests
python -m pytest tests/test_evaluation_agreement.py -v

# View metrics
cat results/summary_metrics.json
```

---

## 📚 Learn More

- **Full Details**: `EVALUATION_LAYER_COMPLETE.md`
- **System Overview**: `FINAL_SYSTEM_REPORT.md`
- **API Docs**: `eit_scorer/evaluation/agreement.py`
- **Tests**: `tests/test_evaluation_agreement.py`

---

**Status**: ✅ **READY TO USE**
