# Spanish EIT Scoring: Quick Reference Card

## Scoring Scale

| Score | Meaning | Key Feature |
|-------|---------|------------|
| **4** | Perfect | 0 edits |
| **3** | Meaning preserved | ≥80% idea units, 0 content subs |
| **2** | More than half | ≥50% idea units, ≤2 content subs |
| **1** | Less than half | ≥15% idea units, ≥2 tokens |
| **0** | No output | Gibberish, empty, or no match |

## 10 Scoring Features

| Feature | Range | Meaning |
|---------|-------|---------|
| `total_edits` | 0–∞ | Insertions + deletions + substitutions |
| `content_subs` | 0–∞ | Full content word substitutions (meaning-changing) |
| `overlap_ratio` | 0.0–1.0 | Multiset-based token recall |
| `content_overlap` | 0.0–1.0 | Content-word-only overlap |
| `idea_unit_coverage` | 0.0–1.0 | Proportion of reference content reproduced |
| `word_order_penalty` | 0.0–1.0 | Reordering severity (0=perfect, 1=fully reordered) |
| `length_ratio` | 0.0–∞ | Response length / reference length |
| `hyp_min_tokens` | 0–∞ | Number of tokens in response |
| `is_gibberish` | true/false | Transcription noise detection |
| `near_synonym_subs` | 0–∞ | Morphological variants (informational only) |

## Rule Matching Order

1. **R0_gibberish**: is_gibberish=true → **0**
2. **R0_empty_or_too_short**: hyp_min_tokens<2 → **0**
3. **R4_perfect**: max_edits=0 → **4**
4. **R3_meaning_preserved**: edits≤3, content_subs=0, IU_cov≥0.80 → **3**
5. **R3_reordered_complete**: IU_cov≥0.90, content_subs=0, word_order≤0.50 → **3**
6. **R2_more_than_half_iu**: IU_cov≥0.50, content_subs≤2, length≥0.40 → **2**
7. **R2_good_overlap_some_loss**: overlap≥0.55, content_subs≤2, length≥0.35 → **2**
8. **R1_less_than_half_iu**: IU_cov≥0.15, content_overlap≥0.15, tokens≥2 → **1**
9. **R1_some_overlap_short**: overlap≥0.20, tokens≥2 → **1**
10. **R0_other**: (catchall) → **0**

## Error Types

| Type | Example | Counted As |
|------|---------|-----------|
| **Near-synonym sub** | tiene→tenía, es→era | Minor (not content_subs) |
| **Function sub** | el→la, a→de | Minor (not content_subs) |
| **Content sub** | libro→casa, come→bebe | Major (content_subs) |

## Preprocessing Pipeline

```
Input: "El libro está en la mesa."
  ↓
Normalize: "el libro esta en la mesa"
  ↓
Tokenize: ["el", "libro", "esta", "en", "la", "mesa"]
  ↓
Expand contractions: (no change in this example)
  ↓
Align with reference
  ↓
Compute features
  ↓
Apply rules (first match wins)
  ↓
Output: Score 0–4
```

## Common Scoring Patterns

### Perfect Repetition (Score 4)
- Reference: "El libro está en la mesa."
- Response: "El libro esta en la mesa." (accent removed by normalization)
- Feature: total_edits = 0
- Rule: R4_perfect

### Meaning Preserved (Score 3)
- Reference: "El niño que se murió está triste."
- Response: "El niño que se m- murio cato esta triste."
- Features: total_edits ≤ 3, content_subs = 0, IU_cov ≥ 0.80
- Rule: R3_meaning_preserved

### More Than Half (Score 2)
- Reference: "Después de cenar me fui a dormir tranquilo."
- Response: "Después de cenar me fui a X tranquilo."
- Features: IU_cov ≥ 0.50, content_subs ≤ 2, length_ratio ≥ 0.40
- Rule: R2_more_than_half_iu

### Less Than Half (Score 1)
- Reference: "Dudo que sepa manejar muy bien."
- Response: "Dudo que sepa ma- tambien."
- Features: IU_cov ≥ 0.15, content_overlap ≥ 0.15, tokens ≥ 2
- Rule: R1_less_than_half_iu

### No Output (Score 0)
- Response: "[gibberish]" or "" or "el"
- Feature: is_gibberish = true OR hyp_min_tokens < 2
- Rule: R0_gibberish or R0_empty_or_too_short

## Key Concepts

### Idea Units (IU)
- Meaningful propositional chunks of the stimulus
- Approximated by **content word coverage**
- Content words: nouns, verbs, adjectives, adverbs
- Function words: articles, prepositions, conjunctions

### Content Substitutions
- **Meaning-changing errors** (full content word substitutions)
- Examples: libro→casa, come→bebe, está→es
- **Excludes** near-synonyms (tiene/tenía) and function words (el/la)

### Near-Synonyms
- Morphological variants: tiene/tenía, es/era, niño/niños
- Lexical near-synonyms: hablar/decir, empezar/comenzar
- Treated as **minor errors**, not full content substitutions
- Meaning is preserved despite form change

### Word Order Penalty
- Measures reordering severity (0.0 = perfect, 1.0 = fully reordered)
- Based on Longest Common Subsequence (LCS) of content tokens
- Used to distinguish genuine reordering from meaning loss

### Gibberish Detection
- Detects transcription noise: [gibberish], XXX, repeated characters
- Patterns: [.*], x+, non-Spanish characters, repeated single chars
- Known noise words: gibberish, inaudible, noise, unclear, unintelligible

## Customization Checklist

- [ ] Adjust rule thresholds in `default_rubric.yaml`
- [ ] Add/remove rules as needed
- [ ] Modify normalization settings (lowercase, punctuation, diacritics)
- [ ] Update tokenization settings (enclitics, apostrophes)
- [ ] Adjust alignment scoring (match_score, mismatch_penalty, gap_penalty)
- [ ] Update function word list if needed
- [ ] Add/remove near-synonym pairs
- [ ] Test on validation dataset
- [ ] Verify score distributions
- [ ] Document any changes

## Debugging Tips

1. **Check the trace**: Every score includes detailed feature values
2. **Verify normalization**: Compare display_hyp vs match_hyp
3. **Inspect alignment**: Check which operations were performed
4. **Review error counts**: See breakdown of error types
5. **Trace rule matching**: See which rule was applied and why
6. **Compare features**: Check if feature values match rule conditions

## Python API

```python
from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse

# Load rubric
rubric = load_rubric("eit_scorer/config/default_rubric.yaml")

# Create item and response
item = EITItem(item_id=1, reference="El libro está en la mesa.", max_points=4)
resp = EITResponse(participant_id="P001", item_id=1, response_text="El libro esta en la mesa.")

# Score
result = score_response(item, resp, rubric)

# Access results
print(f"Score: {result.score}/{result.max_points}")
print(f"Rule: {result.trace.applied_rule_ids}")
print(f"Features: {result.trace.idea_unit_coverage:.2f} IU coverage")
```

## References

- **Ortega (2000)**: Understanding syntactic complexity
- **Faretta-Stutenberg et al. (2023)**: Parallel forms reliability study
- **Rubric YAML**: `eit_scorer/config/default_rubric.yaml`
- **Scoring code**: `eit_scorer/core/scoring.py`
- **Full guide**: `SCORING_GUIDE.md`
