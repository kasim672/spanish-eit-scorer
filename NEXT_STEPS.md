# Next Steps: Validation, Calibration & Deployment

## Current Status ✅

The Spanish EIT scoring system has been successfully redesigned as a **fully deterministic, rule-based pipeline** aligned with Ortega (2000) and Faretta-Stutenberg et al. (2023).

**Key achievements**:
- ✅ Removed all probabilistic NLP components (spaCy, neural networks)
- ✅ Implemented deterministic alignment (Needleman-Wunsch)
- ✅ Created meaning-based feature extraction (idea units, content overlap, word order)
- ✅ Defined 11 rubric rules aligned with Ortega (2000) scoring scale
- ✅ Built comprehensive scoring trace for interpretability
- ✅ Achieved full reproducibility (same input → same score)

## Phase 1: Validation (Weeks 1–2)

### 1.1 Prepare Validation Dataset
**Goal**: Gather human-scored responses to validate system accuracy

**Tasks**:
- [ ] Collect 50–100 responses with scores from 2+ human raters
- [ ] Ensure responses span all score levels (0–4)
- [ ] Include edge cases: gibberish, reordered, near-synonyms, false starts
- [ ] Format as JSONL: `{item_id, reference, response_text, human_rater_a, human_rater_b}`
- [ ] Store in `data/validation/` directory

**Example**:
```json
{
  "item_id": 1,
  "reference": "El libro está en la mesa.",
  "response_text": "El libro esta en la mesa.",
  "human_rater_a": 4,
  "human_rater_b": 4
}
```

### 1.2 Run Validation Script
**Goal**: Compare system scores against human scores

**Tasks**:
- [ ] Create `scripts/validate_scoring.py`:
  ```python
  from eit_scorer.core.rubric import load_rubric
  from eit_scorer.core.scoring import score_response
  from eit_scorer.data.models import EITDataset
  import json
  
  rubric = load_rubric("eit_scorer/config/default_rubric.yaml")
  dataset = EITDataset.from_jsonl("data/validation/responses.jsonl")
  
  results = []
  for item in dataset.items:
      for resp in item.responses:
          auto_score = score_response(item, resp, rubric).score
          human_score = (resp.human_rater_a + resp.human_rater_b) / 2
          results.append({
              "item_id": item.item_id,
              "auto_score": auto_score,
              "human_score": human_score,
              "diff": abs(auto_score - human_score),
          })
  
  # Compute metrics
  exact_match = sum(1 for r in results if r["diff"] == 0) / len(results)
  within_1 = sum(1 for r in results if r["diff"] <= 1) / len(results)
  mae = sum(r["diff"] for r in results) / len(results)
  
  print(f"Exact match: {exact_match:.1%}")
  print(f"Within ±1: {within_1:.1%}")
  print(f"MAE: {mae:.2f}")
  ```
- [ ] Run validation and generate report
- [ ] Compute metrics:
  - **Exact match**: % of scores matching human exactly
  - **Within ±1**: % of scores within 1 point of human
  - **MAE**: Mean absolute error
  - **Correlation**: Pearson r with human scores
  - **Confusion matrix**: Score-by-score breakdown

### 1.3 Analyze Mismatches
**Goal**: Identify systematic errors and edge cases

**Tasks**:
- [ ] Group mismatches by score level (0, 1, 2, 3, 4)
- [ ] Identify patterns:
  - Are certain rule conditions too strict/loose?
  - Are feature thresholds misaligned with human judgment?
  - Are there edge cases not covered by rules?
- [ ] Create detailed error report with examples
- [ ] Flag high-priority issues for calibration

**Example analysis**:
```
Score 3 mismatches (system=3, human=2):
  - Pattern: High idea_unit_coverage but some content loss
  - Issue: R3_meaning_preserved rule too lenient
  - Recommendation: Increase min_idea_unit_coverage from 0.80 to 0.85

Score 2 mismatches (system=2, human=1):
  - Pattern: Good token overlap but meaning unclear
  - Issue: R2_good_overlap_some_loss doesn't account for semantic coherence
  - Recommendation: Add max_word_order_penalty condition
```

## Phase 2: Calibration (Weeks 2–3)

### 2.1 Adjust Rule Thresholds
**Goal**: Fine-tune rule conditions to match human judgment

**Tasks**:
- [ ] For each mismatched rule, analyze feature distributions
- [ ] Adjust thresholds incrementally:
  ```yaml
  # Before
  - id: R3_meaning_preserved
    when:
      min_idea_unit_coverage: 0.80  # ← Too lenient?
  
  # After
  - id: R3_meaning_preserved
    when:
      min_idea_unit_coverage: 0.85  # ← More strict
  ```
- [ ] Re-run validation after each adjustment
- [ ] Track improvement in exact_match and within_1 metrics
- [ ] Stop when metrics plateau or human agreement is matched

### 2.2 Add/Remove Rules
**Goal**: Ensure all edge cases are covered

**Tasks**:
- [ ] Identify responses that don't match any rule (should be rare)
- [ ] Create new rules for uncovered patterns:
  ```yaml
  - id: R2_custom_pattern
    description: "Specific edge case"
    when:
      min_idea_unit_coverage: 0.60
      max_content_subs: 1
      max_word_order_penalty: 0.40
    then:
      score: 2
  ```
- [ ] Test new rules on validation set
- [ ] Verify rule order (first match wins)

### 2.3 Update Feature Extraction
**Goal**: Ensure features accurately capture meaning preservation

**Tasks**:
- [ ] Review feature definitions:
  - Is `idea_unit_coverage` capturing content preservation correctly?
  - Is `word_order_penalty` distinguishing reordering from meaning loss?
  - Is `content_overlap` too strict/lenient?
- [ ] Adjust feature computation if needed:
  - Modify near-synonym pairs
  - Update function word list
  - Adjust alignment scoring (match_score, mismatch_penalty)
- [ ] Re-validate after changes

### 2.4 Document Calibration
**Goal**: Record all changes for reproducibility

**Tasks**:
- [ ] Create `CALIBRATION_LOG.md`:
  ```markdown
  ## Calibration Log
  
  ### Iteration 1 (2024-03-27)
  - Exact match: 78% → 82%
  - Within ±1: 92% → 95%
  - Changes:
    - Increased R3_meaning_preserved min_idea_unit_coverage from 0.80 to 0.85
    - Added R2_custom_pattern for reordered responses
  
  ### Iteration 2 (2024-03-28)
  - Exact match: 82% → 85%
  - Within ±1: 95% → 97%
  - Changes:
    - Adjusted R2_good_overlap_some_loss max_content_subs from 2 to 1
  ```
- [ ] Version the rubric YAML (e.g., v2.1, v2.2)
- [ ] Keep all previous versions for reference

## Phase 3: Testing & QA (Week 3)

### 3.1 Unit Tests
**Goal**: Ensure all components work correctly

**Tasks**:
- [ ] Run existing tests:
  ```bash
  pytest tests/test_alignment.py -v
  pytest tests/test_determinism.py -v
  pytest tests/test_synth_pipeline.py -v
  ```
- [ ] Add new tests for calibrated rules:
  ```python
  def test_r3_meaning_preserved():
      item = EITItem(item_id=1, reference="El niño está triste.")
      resp = EITResponse(participant_id="P001", item_id=1, response_text="El niño esta triste.")
      result = score_response(item, resp, rubric)
      assert result.score == 3
      assert "R3_meaning_preserved" in result.trace.applied_rule_ids
  ```
- [ ] Verify all tests pass

### 3.2 Edge Case Testing
**Goal**: Ensure system handles unusual inputs gracefully

**Test cases**:
- [ ] Empty response: "" → Score 0
- [ ] Single token: "el" → Score 0
- [ ] Gibberish: "[gibberish]" → Score 0
- [ ] All caps: "EL LIBRO ESTÁ EN LA MESA" → Score 4
- [ ] Extra spaces: "El  libro  está  en  la  mesa" → Score 4
- [ ] Mixed case: "El LiBrO está EN la mesa" → Score 4
- [ ] Diacritics: "El libro está en la mesa" vs "El libro esta en la mesa" → Score 4
- [ ] Contractions: "del" → "de el" → Score 4
- [ ] Enclitics: "Dámelo" → "dame lo" → Correct tokenization
- [ ] False starts: "La-las casas" → Handled correctly
- [ ] Hesitations: "El... el libro" → Handled correctly
- [ ] Multiple responses: Score best final response

### 3.3 Performance Testing
**Goal**: Ensure system is fast enough for production

**Tasks**:
- [ ] Benchmark scoring speed:
  ```python
  import time
  start = time.time()
  for _ in range(1000):
      score_response(item, resp, rubric)
  elapsed = time.time() - start
  print(f"1000 scores in {elapsed:.2f}s ({1000/elapsed:.0f} scores/sec)")
  ```
- [ ] Target: ≥100 scores/second on standard hardware
- [ ] Profile code to identify bottlenecks if needed

### 3.4 Regression Testing
**Goal**: Ensure calibration didn't break existing functionality

**Tasks**:
- [ ] Re-run validation on original dataset
- [ ] Verify metrics haven't degraded
- [ ] Check that all score levels (0–4) are still achievable
- [ ] Verify determinism (same input → same score)

## Phase 4: Documentation & Deployment (Week 4)

### 4.1 Update Documentation
**Goal**: Ensure all documentation reflects final system

**Tasks**:
- [ ] Update `SCORING_GUIDE.md` with final rule thresholds
- [ ] Update `QUICK_REFERENCE.md` with final feature ranges
- [ ] Add calibration notes to `IMPLEMENTATION_SUMMARY.md`
- [ ] Create `VALIDATION_REPORT.md` with results and metrics
- [ ] Add examples of each score level with final rules

### 4.2 Create API Documentation
**Goal**: Enable easy integration with other systems

**Tasks**:
- [ ] Document Python API:
  ```python
  from eit_scorer.core.rubric import load_rubric
  from eit_scorer.core.scoring import score_response
  from eit_scorer.data.models import EITItem, EITResponse
  
  # Load rubric
  rubric = load_rubric("eit_scorer/config/default_rubric.yaml")
  
  # Score single response
  item = EITItem(item_id=1, reference="...", max_points=4)
  resp = EITResponse(participant_id="P001", item_id=1, response_text="...")
  result = score_response(item, resp, rubric)
  
  # Access results
  print(result.score)  # 0–4
  print(result.trace)  # Detailed trace
  ```
- [ ] Document REST API (if applicable):
  ```bash
  POST /score
  {
    "item_id": 1,
    "reference": "El libro está en la mesa.",
    "response_text": "El libro esta en la mesa."
  }
  
  Response:
  {
    "score": 4,
    "max_points": 4,
    "trace": { ... }
  }
  ```
- [ ] Create integration examples

### 4.3 Prepare for Production
**Goal**: Ensure system is ready for deployment

**Tasks**:
- [ ] Set up logging:
  ```python
  import logging
  logger = logging.getLogger("eit_scorer")
  logger.info(f"Scored item {item_id}: {score}/4")
  ```
- [ ] Add error handling:
  ```python
  try:
      result = score_response(item, resp, rubric)
  except ValueError as e:
      logger.error(f"Scoring failed: {e}")
      return {"error": str(e)}
  ```
- [ ] Create configuration management:
  - Support multiple rubric versions
  - Allow runtime rubric selection
  - Log which rubric version was used
- [ ] Set up monitoring:
  - Track score distributions
  - Monitor rule application rates
  - Alert on unusual patterns

### 4.4 Deploy to Production
**Goal**: Make system available for use

**Tasks**:
- [ ] Package system:
  ```bash
  pip install -e .
  ```
- [ ] Deploy to server/API
- [ ] Set up monitoring and logging
- [ ] Create user documentation
- [ ] Train users on system usage

## Phase 5: Ongoing Maintenance (Ongoing)

### 5.1 Monitor Performance
**Goal**: Ensure system continues to work well

**Tasks**:
- [ ] Track score distributions monthly
- [ ] Monitor rule application rates
- [ ] Alert on unusual patterns (e.g., all scores are 2)
- [ ] Collect user feedback

### 5.2 Continuous Improvement
**Goal**: Refine system based on real-world usage

**Tasks**:
- [ ] Gather new validation data quarterly
- [ ] Re-calibrate rules if needed
- [ ] Add new rules for edge cases
- [ ] Update documentation

### 5.3 Version Management
**Goal**: Maintain reproducibility and traceability

**Tasks**:
- [ ] Version all rubric changes (v2.0, v2.1, v2.2, etc.)
- [ ] Keep changelog:
  ```markdown
  ## Changelog
  
  ### v2.1 (2024-04-15)
  - Increased R3_meaning_preserved min_idea_unit_coverage from 0.80 to 0.85
  - Added R2_custom_pattern for reordered responses
  - Validation: 85% exact match, 97% within ±1
  
  ### v2.0 (2024-03-27)
  - Initial deterministic implementation
  - Removed spaCy and neural components
  - Validation: 78% exact match, 92% within ±1
  ```
- [ ] Tag releases in git

## Success Criteria

### Phase 1: Validation
- [ ] Exact match with human scores: ≥80%
- [ ] Within ±1 of human scores: ≥95%
- [ ] All score levels (0–4) represented
- [ ] Edge cases identified and documented

### Phase 2: Calibration
- [ ] Exact match: ≥85%
- [ ] Within ±1: ≥97%
- [ ] All mismatches analyzed and explained
- [ ] Rubric version updated and documented

### Phase 3: Testing
- [ ] All unit tests pass
- [ ] All edge cases handled correctly
- [ ] Performance: ≥100 scores/second
- [ ] Determinism verified (same input → same score)

### Phase 4: Documentation
- [ ] All documentation updated
- [ ] API documented and tested
- [ ] Examples provided for each score level
- [ ] Integration guide created

### Phase 5: Deployment
- [ ] System deployed to production
- [ ] Monitoring and logging active
- [ ] User documentation available
- [ ] Support process established

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| 1. Validation | 2 weeks | Week 1 | Week 2 |
| 2. Calibration | 1 week | Week 2 | Week 3 |
| 3. Testing & QA | 1 week | Week 3 | Week 4 |
| 4. Documentation | 1 week | Week 4 | Week 5 |
| 5. Deployment | 1 week | Week 5 | Week 6 |
| **Total** | **6 weeks** | | |

## Resources Needed

- **Human raters**: 2–3 for validation dataset
- **Validation data**: 50–100 responses with human scores
- **Development time**: ~40 hours
- **Testing time**: ~20 hours
- **Documentation time**: ~15 hours

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Validation data insufficient | Can't validate properly | Collect 100+ responses, ensure all score levels |
| Rule thresholds misaligned | System scores incorrectly | Iterative calibration with validation data |
| Performance too slow | Can't use in production | Profile and optimize bottlenecks |
| Edge cases not covered | System fails on unusual inputs | Comprehensive edge case testing |
| Determinism broken | Scores not reproducible | Verify determinism in all tests |

## Questions & Decisions

1. **Validation dataset**: Where will human-scored responses come from?
   - Option A: Collect new data from participants
   - Option B: Use existing data from Faretta-Stutenberg et al. (2023)
   - **Recommendation**: Option B if available, otherwise Option A

2. **Exact match target**: Should we aim for 85% or 90%?
   - Option A: 85% (faster, good enough)
   - Option B: 90% (slower, more accurate)
   - **Recommendation**: 85% for initial release, 90% for future versions

3. **Rule customization**: Should users be able to modify rules?
   - Option A: Yes, via YAML editing
   - Option B: No, fixed rules only
   - **Recommendation**: Option A for flexibility, with version control

4. **API design**: REST API or Python library only?
   - Option A: Python library only (simpler)
   - Option B: REST API (more flexible)
   - **Recommendation**: Start with Python library, add REST API later if needed

## Contact & Support

- **Questions**: Contact the development team
- **Bug reports**: File issues on GitHub
- **Feature requests**: Submit via issue tracker
- **Documentation**: See `SCORING_GUIDE.md` and `QUICK_REFERENCE.md`

---

**Last updated**: 2024-03-27
**Status**: Ready for Phase 1 (Validation)
