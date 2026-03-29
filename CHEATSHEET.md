# Spanish EIT Scorer - Cheat Sheet

**One-page quick reference for all essential commands.**

---

## 🚀 Setup (One-Time)

```bash
source .venv/bin/activate
pip install -r requirements.lock.txt
```

---

## ⚡ Essential Commands

### Score Excel File
```bash
python scripts/score_excel.py "AutoEIT Sample Transcriptions for Scoring.xlsx" "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"
```

### Run Demo
```bash
python scripts/demo_evaluation.py
```

### Run Tests
```bash
python -m pytest tests/ -q
```

---

## 🧪 Testing

| Command | Purpose |
|---------|---------|
| `python -m pytest tests/ -q` | Quick test (summary) |
| `python -m pytest tests/ -v` | Verbose test (detailed) |
| `python -m pytest tests/test_evaluation_agreement.py -v` | Evaluation tests only |
| `python -m pytest tests/ --co -q` | List all tests |

---

## 📊 View Results

### Evaluation Metrics
```bash
cat results/summary_metrics.json
python -m json.tool results/summary_metrics.json
```

### Score Distribution
```bash
python3 << 'EOF'
import openpyxl
wb = openpyxl.load_workbook("AutoEIT Sample Transcriptions for ScoringOutput.xlsx")
scores = []
for sheet in wb.sheetnames:
    if sheet.lower() != "info":
        ws = wb[sheet]
        for row in range(2, ws.max_row + 1):
            s = ws.cell(row, 4).value
            if s: scores.append(int(s))
for s in range(5):
    print(f"Score {s}: {scores.count(s)} ({scores.count(s)/len(scores)*100:.1f}%)")
EOF
```

---

## 🎯 Scoring Scale

| Score | Description |
|-------|-------------|
| **4** | Perfect match (0 edits) |
| **3** | Meaning preserved (≥80% coverage) |
| **2** | Partial meaning (≥50% coverage) |
| **1** | Minimal meaning (>0% coverage) |
| **0** | No meaning / gibberish |

---

## 📈 Evaluation Metrics

| Metric | Target | Interpretation |
|--------|--------|----------------|
| **Cohen's Kappa** | ≥0.70 | Good agreement |
| **Accuracy** | ≥85% | Excellent match rate |
| **MAE** | <0.5 | Low error |

---

## 🎓 API Usage

### Score Single Response
```python
from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse

rubric = load_rubric("eit_scorer/config/default_rubric.yaml")
item = EITItem(item_id="1", reference="Quiero cortarme el pelo", max_points=4)
response = EITResponse(participant_id="P001", item_id="1", response_text="Quiero cortarme el pelo")
scored = score_response(item, response, rubric)
print(f"Score: {scored.score}/4")
```

### Evaluate Agreement
```python
from eit_scorer.evaluation.agreement import evaluate_agreement

metrics = evaluate_agreement(
    y_true=[4, 3, 2, 1],
    y_pred=[4, 3, 2, 0],
)
print(metrics.detailed_report())
```

---

## 🏆 Quick Validation

```bash
# Complete validation (one command)
source .venv/bin/activate && \
python -m pytest tests/ -q && \
python scripts/demo_evaluation.py | tail -20
```

**Expected**: Tests pass + evaluation shows κ = 0.851

---

## 📁 Project Structure

```
spanish_eit_scorer/
├── scripts/          # CLI scripts
├── eit_scorer/       # Core package
├── tests/            # 108 tests
├── docs/             # Documentation
├── results/          # Output files
└── README.md         # Main docs
```

---

## 🎬 Demo Sequence

1. `python -m pytest tests/ -q` → 108 passed
2. `python scripts/demo_evaluation.py` → κ = 0.851
3. `python scripts/score_excel.py ...` → 120 scored
4. `cat results/summary_metrics.json` → View metrics

**Total Time**: 3 minutes

---

## 📞 Help

- **Setup**: [INSTALLATION.md](INSTALLATION.md)
- **Commands**: [COMMANDS.md](COMMANDS.md)
- **Testing**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Demo**: [HACKATHON_DEMO.md](HACKATHON_DEMO.md)

---

**Status**: ✅ **READY TO DEMO**
