# Testing Guide - For Hackathon Judges & Reviewers

**Quick validation commands to verify the Spanish EIT Scorer system.**

---

## 🚀 Quick Validation (5 Minutes)

### 1. Run Test Suite
```bash
# Activate virtual environment
source .venv/bin/activate

# Run all 108 tests (should see "108 passed")
python -m pytest tests/ -q
```

**Expected Output**:
```
108 passed in 2.22s
```

---

### 2. Run Evaluation Demo
```bash
python scripts/demo_evaluation.py
```

**Expected Output**:
- 10 sample responses scored
- 9/10 exact matches with human scores
- Cohen's Kappa: 0.851 (almost perfect)
- Accuracy: 90%
- MAE: 0.10

**What This Shows**:
- ✅ Scoring system works correctly
- ✅ Evaluation metrics computed accurately
- ✅ Research-grade validation (κ = 0.851)

---

### 3. Score Sample Excel File
```bash
python scripts/score_excel.py "AutoEIT Sample Transcriptions for Scoring.xlsx" "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"
```

**Expected Output**:
```
Loaded rubric: Rubric 'Spanish EIT Default Rubric' v2.0 | max_points=4 | 10 rules
Reading Excel file: AutoEIT Sample Transcriptions for Scoring.xlsx
Found 4 sheets to process

Processing sheet: 38001-1A (30 rows)
  Completed: 30 scores

Processing sheet: 38002-2A (30 rows)
  Completed: 30 scores

Processing sheet: 38004-2A (30 rows)
  Completed: 30 scores

Processing sheet: 38006-2A (30 rows)
  Completed: 30 scores

Writing results to: AutoEIT Sample Transcriptions for ScoringOutput.xlsx
Successfully scored 120 responses
Output saved to: AutoEIT Sample Transcriptions for ScoringOutput.xlsx
```

**What This Shows**:
- ✅ Multi-sheet Excel processing works
- ✅ Batch scoring (120 responses) completes successfully
- ✅ Output file created

---

### 4. View Output File
```bash
# Check output file exists
ls -lh "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"

# View first few scores (requires Python)
python3 << 'EOF'
import openpyxl
wb = openpyxl.load_workbook("AutoEIT Sample Transcriptions for ScoringOutput.xlsx")
ws = wb["38001-1A"]
print("\nFirst 5 scored responses:")
print(f"{'ID':<5} {'Stimulus':<40} {'Response':<40} {'Score':<5}")
print("-" * 95)
for row in range(2, 7):
    sid = ws.cell(row, 1).value
    stim = ws.cell(row, 2).value
    resp = ws.cell(row, 3).value
    score = ws.cell(row, 4).value
    print(f"{sid:<5} {str(stim)[:38]:<40} {str(resp)[:38]:<40} {score:<5}")
EOF
```

**What This Shows**:
- ✅ Scores written to Excel correctly
- ✅ All columns preserved
- ✅ Realistic score distribution

---

## 🧪 Detailed Testing

### Test Categories

#### 1. Core Functionality Tests
```bash
# Alignment tests (6 tests)
python -m pytest tests/test_alignment.py -v

# Scoring tests (16 tests)
python -m pytest tests/test_integration.py -v

# Rubric engine tests (12 tests)
python -m pytest tests/test_rubric_engine.py -v
```

#### 2. Evaluation Tests
```bash
# Evaluation metrics tests (17 tests)
python -m pytest tests/test_evaluation_agreement.py -v
```

**Key Tests**:
- Perfect agreement (κ = 1.0)
- No agreement (κ = 0.0)
- Partial agreement
- MAE computation
- Interpretation framework

#### 3. Determinism Tests
```bash
# Reproducibility tests (13 tests)
python -m pytest tests/test_determinism.py -v
```

**Verifies**:
- Same input → same score
- Reproducible fingerprints
- Consistent audit trails

---

## 📊 View Test Results

### List All Tests
```bash
python -m pytest tests/ --co -q
```

**Output**: List of all 108 test names

### Run with Timing
```bash
python -m pytest tests/ -v --durations=10
```

**Output**: Shows slowest 10 tests (all should be <100ms)

### Run Specific Test
```bash
# Test perfect match scoring
python -m pytest tests/test_integration.py::test_perfect_match_scores_4 -v

# Test evaluation metrics
python -m pytest tests/test_evaluation_agreement.py::test_perfect_agreement -v
```

---

## 🎯 Validation Checklist

Use this checklist to verify the system:

- [ ] **Tests Pass**: Run `python -m pytest tests/ -q` → See "108 passed"
- [ ] **Demo Works**: Run `python scripts/demo_evaluation.py` → See evaluation report
- [ ] **Excel Scoring**: Run scoring command → Output file created
- [ ] **Deterministic**: Run demo twice → Same results both times
- [ ] **Metrics Valid**: κ ≥ 0.70, Accuracy ≥ 85%, MAE < 0.5

---

## 🔍 Inspect Test Cases

### View Specific Test Code
```bash
# View alignment tests
cat tests/test_alignment.py

# View evaluation tests
cat tests/test_evaluation_agreement.py

# View integration tests
cat tests/test_integration.py
```

### Run Single Test with Output
```bash
# Run with print statements visible
python -m pytest tests/test_integration.py::test_perfect_match_scores_4 -v -s
```

---

## 📈 Performance Benchmarks

### Test Execution Time
```bash
python -m pytest tests/ -v --durations=0
```

**Expected**:
- Total: ~2.2 seconds
- Average: ~20ms per test
- No test >100ms

### Scoring Performance
```bash
# Time the Excel scoring
time python scripts/score_excel.py "AutoEIT Sample Transcriptions for Scoring.xlsx" "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"
```

**Expected**: <2 seconds for 120 responses (~60 responses/second)

---

## 🎨 Visual Inspection

### View Score Distribution
```bash
python3 << 'EOF'
import openpyxl

wb = openpyxl.load_workbook("AutoEIT Sample Transcriptions for ScoringOutput.xlsx")
all_scores = []

for sheet_name in wb.sheetnames:
    if sheet_name.lower() == "info":
        continue
    ws = wb[sheet_name]
    for row in range(2, ws.max_row + 1):
        score = ws.cell(row, 4).value
        if score is not None:
            all_scores.append(int(score))

print("\nScore Distribution:")
for s in range(5):
    count = all_scores.count(s)
    pct = count / len(all_scores) * 100
    bar = "█" * int(pct / 2)
    print(f"  Score {s}: {count:3d} ({pct:5.1f}%) {bar}")

print(f"\nTotal: {len(all_scores)} responses")
EOF
```

**Expected**: Realistic distribution (mostly 1-3, some 0 and 4)

---

## 🔬 Advanced Testing

### Test with Custom Data
```bash
# Create test file with human scores
python3 << 'EOF'
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Test"

# Header
ws.cell(1, 1).value = "Sentence"
ws.cell(1, 2).value = "Stimulus"
ws.cell(1, 3).value = "Transcription Rater 1"
ws.cell(1, 4).value = "Score"

# Test data
test_data = [
    (1, "Quiero cortarme el pelo", "Quiero cortarme el pelo", 4),
    (2, "El libro está en la mesa", "El libro está mesa", 3),
    (3, "Voy a la escuela", "Voy escuela", 2),
]

for i, (sid, stim, resp, score) in enumerate(test_data, 2):
    ws.cell(i, 1).value = sid
    ws.cell(i, 2).value = stim
    ws.cell(i, 3).value = resp
    ws.cell(i, 4).value = score

wb.save("test_custom.xlsx")
print("Created test_custom.xlsx")
EOF

# Score it
python scripts/score_excel.py test_custom.xlsx test_custom_output.xlsx

# View metrics
cat results/summary_metrics.json
```

---

## 🎯 For Judges: What Makes This Special

### 1. Deterministic & Reproducible
```bash
# Run demo twice - results are identical
python scripts/demo_evaluation.py > run1.txt
python scripts/demo_evaluation.py > run2.txt
diff run1.txt run2.txt  # Should show no differences
```

### 2. Research-Grade Metrics
- Cohen's Kappa (gold standard for inter-rater reliability)
- Weighted Kappa (accounts for ordinal scores)
- Automatic validity assessment

### 3. Production-Ready
- 108 comprehensive tests (100% passing)
- Complete error handling
- Full audit trails
- Extensive documentation

### 4. Clean Architecture
- Explicit rubric rules (no black box)
- Clear feature definitions
- Transparent scoring logic
- Complete traceability

---

## 📝 Test Output Examples

### Successful Test Run
```
============================= test session starts ==============================
platform linux -- Python 3.11.8, pytest-9.0.2, pluggy-1.6.0
collected 108 items

tests/test_alignment.py ......                                           [  5%]
tests/test_content_units.py ...........                                  [ 15%]
tests/test_determinism.py ............                                   [ 26%]
tests/test_evaluation_agreement.py .................                     [ 42%]
tests/test_integration.py ................                               [ 57%]
tests/test_meaning_score.py ..............                               [ 70%]
tests/test_noise_handler.py ..........                                   [ 79%]
tests/test_rubric_engine.py ............                                 [ 90%]
tests/test_synth_pipeline.py ..........                                  [100%]

============================= 108 passed in 2.22s ==============================
```

### Evaluation Metrics JSON
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

## ⚡ One-Command Validation

```bash
# Complete validation in one command
source .venv/bin/activate && \
python -m pytest tests/ -q && \
python scripts/demo_evaluation.py && \
python scripts/score_excel.py "AutoEIT Sample Transcriptions for Scoring.xlsx" "AutoEIT Sample Transcriptions for ScoringOutput.xlsx"
```

**Expected**: All commands succeed, no errors

---

## 🏆 Success Criteria

| Criterion | Command | Expected Result |
|-----------|---------|-----------------|
| Tests pass | `python -m pytest tests/ -q` | 108 passed |
| Demo works | `python scripts/demo_evaluation.py` | κ = 0.851 |
| Excel scoring | `python scripts/score_excel.py ...` | 120 responses scored |
| Deterministic | Run demo twice | Identical results |
| Fast | Test suite | <3 seconds |

---

## 📞 Support

If any test fails:
1. Check virtual environment is activated
2. Verify dependencies installed: `pip list`
3. Review error message
4. Check [INSTALLATION.md](INSTALLATION.md)

**Status**: ✅ **READY FOR TESTING**
