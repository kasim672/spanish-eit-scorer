# Spanish EIT Scoring System: Complete Guide

## Overview

The Spanish EIT scoring system is a **fully deterministic, rule-based pipeline** that scores learner responses on a 0–4 scale according to the Ortega (2000) rubric. Every score is traceable to explicit rules and features.

## Scoring Scale (Ortega 2000)

| Score | Descriptor | Meaning |
|-------|-----------|---------|
| **4** | Perfect repetition | Exact match after normalization |
| **3** | Meaning preserved | Complete meaning despite grammatical errors |
| **2** | More than half idea units | Partial meaning, some content loss |
| **1** | Less than half idea units | Incomplete or unrelated meaning |
| **0** | No meaningful output | Silence, gibberish, or minimal repetition |

## Scoring Features

The system evaluates responses using 10 deterministic features:

### 1. **Total Edits** (`total_edits`)
- Sum of insertions, deletions, and substitutions from alignment
- Lower = more similar to reference
- Used in: R4_perfect (≤0), R3_meaning_preserved (≤3)

### 2. **Content Substitutions** (`content_subs`)
- Count of full content word substitutions (meaning-changing errors)
- **Excludes** near-synonyms (morphological variants, tense shifts)
- Lower = better meaning preservation
- Used in: R3_meaning_preserved (=0), R2_more_than_half_iu (≤2)

### 3. **Token Overlap Ratio** (`overlap_ratio`)
- Multiset-based recall: how many reference tokens appear in response
- Range: 0.0 (no overlap) to 1.0 (perfect recall)
- Handles repeated words correctly
- Used in: R2_good_overlap_some_loss (≥0.55), R1_some_overlap_short (≥0.20)

### 4. **Content Overlap** (`content_overlap`)
- Token overlap restricted to content words only (nouns, verbs, adjectives, adverbs)
- Ignores function words (articles, prepositions, conjunctions)
- Range: 0.0 to 1.0
- Used in: R1_less_than_half_iu (≥0.15)

### 5. **Idea Unit Coverage** (`idea_unit_coverage`)
- Proportion of reference content words reproduced in response
- **Near-synonym aware**: Morphological variants count as covered
- Example: If reference has "tiene" and response has "tenía", coverage includes this
- Range: 0.0 to 1.0
- Used in: R3_meaning_preserved (≥0.80), R3_reordered_complete (≥0.90), R2_more_than_half_iu (≥0.50), R1_less_than_half_iu (≥0.15)

### 6. **Word Order Penalty** (`word_order_penalty`)
- Severity of word reordering (0.0 = perfect order, 1.0 = fully reordered)
- Based on Longest Common Subsequence (LCS) of content tokens
- Distinguishes genuine reordering from meaning loss
- Used in: R3_reordered_complete (≤0.50)

### 7. **Length Ratio** (`length_ratio`)
- Response length / reference length
- Proxy for completeness
- Range: 0.0 (empty) to 1.0+ (longer than reference)
- Used in: R2_more_than_half_iu (≥0.40), R2_good_overlap_some_loss (≥0.35)

### 8. **Minimum Tokens** (`hyp_min_tokens`)
- Number of tokens in response
- Used to filter out empty or near-empty responses
- Used in: R0_empty_or_too_short (<2), R1_less_than_half_iu (≥2), R1_some_overlap_short (≥2)

### 9. **Gibberish Detection** (`is_gibberish`)
- Boolean: True if response is transcription noise
- Detects: [gibberish], XXX, repeated characters, non-Spanish noise
- Used in: R0_gibberish (true)

### 10. **Near-Synonym Substitutions** (`near_synonym_subs`)
- Count of morphological variants and lexical near-synonyms
- Examples: tiene/tenía, es/era, niño/niños, bueno/buena
- Treated as minor errors, not full content substitutions
- Informational only (not used in rule conditions)

## Scoring Rules

Rules are applied in order; the **first matching rule wins**. Order matters!

### Rule R0_gibberish (Score 0)
**Condition**: `is_gibberish: true`
**Meaning**: Response is transcription noise ([gibberish], XXX, etc.)
**Example**: "[gibberish]" → Score 0

### Rule R0_empty_or_too_short (Score 0)
**Condition**: `hyp_min_tokens < 2`
**Meaning**: Response has fewer than 2 tokens — no meaningful production
**Example**: "" or "el" → Score 0

### Rule R4_perfect (Score 4)
**Condition**: `max_edits: 0`
**Meaning**: No edits — response matches target exactly after normalization
**Example**: 
- Reference: "El libro está en la mesa."
- Response: "El libro esta en la mesa." (accent removed by normalization)
- Score: 4

### Rule R3_meaning_preserved (Score 3)
**Conditions**:
- `max_edits: 3` (at most 3 insertions/deletions/substitutions)
- `max_content_subs: 0` (no full content word substitutions)
- `min_idea_unit_coverage: 0.80` (at least 80% of content words reproduced)

**Meaning**: Meaning fully preserved despite minor form errors
**Example**:
- Reference: "El niño que se murió está triste."
- Response: "El niño que se m- murió cato esta triste."
- Analysis: 1 deletion (cato), 1 substitution (cato→está), but all content words present
- Score: 3 (meaning preserved despite disfluency)

### Rule R3_reordered_complete (Score 3)
**Conditions**:
- `min_idea_unit_coverage: 0.90` (at least 90% of content words reproduced)
- `max_content_subs: 0` (no full content word substitutions)
- `max_word_order_penalty: 0.50` (at most 50% reordering)

**Meaning**: Content fully present but reordered — meaning preserved despite word order change
**Example**:
- Reference: "El chico con el que yo salgo es español."
- Response: "El chico es español con el que yo salgo."
- Analysis: All content words present, but reordered; meaning still clear
- Score: 3

### Rule R2_more_than_half_iu (Score 2)
**Conditions**:
- `min_idea_unit_coverage: 0.50` (at least 50% of content words reproduced)
- `max_content_subs: 2` (at most 2 full content word substitutions)
- `min_length_ratio: 0.40` (response is at least 40% of reference length)

**Meaning**: More than half idea units reproduced; meaning partially preserved
**Example**:
- Reference: "Después de cenar me fui a dormir tranquilo."
- Response: "Después de cenar me fui a X tranquilo."
- Analysis: 6/8 content words present (75% coverage), 1 substitution (X for dormir)
- Score: 2

### Rule R2_good_overlap_some_loss (Score 2)
**Conditions**:
- `min_token_overlap_ratio: 0.55` (at least 55% of tokens reproduced)
- `max_content_subs: 2` (at most 2 full content word substitutions)
- `min_length_ratio: 0.35` (response is at least 35% of reference length)

**Meaning**: Good overall overlap but content substitutions reduce meaning fidelity
**Example**:
- Reference: "Las casas son muy bonitas pero caras."
- Response: "Los coches son muy baratos pero feos."
- Analysis: 5/7 tokens match (71% overlap), but 2 content substitutions (casas→coches, bonitas→baratos)
- Score: 2

### Rule R1_less_than_half_iu (Score 1)
**Conditions**:
- `min_idea_unit_coverage: 0.15` (at least 15% of content words reproduced)
- `min_content_overlap: 0.15` (at least 15% of content words overlap)
- `hyp_min_tokens: 2` (at least 2 tokens)

**Meaning**: Less than half idea units reproduced — incomplete or unrelated meaning
**Example**:
- Reference: "Dudo que sepa manejar muy bien."
- Response: "Dudo que sepa ma- tambien."
- Analysis: 3/6 content words present (50% coverage), but meaning incomplete
- Score: 1

### Rule R1_some_overlap_short (Score 1)
**Conditions**:
- `min_token_overlap_ratio: 0.20` (at least 20% of tokens reproduced)
- `hyp_min_tokens: 2` (at least 2 tokens)

**Meaning**: Some recognizable content but very incomplete production
**Example**:
- Reference: "La cantidad de personas que fuman ha disminuido."
- Response: "La cantidad de personas fumar alguno, alguno."
- Analysis: 4/8 tokens match (50% overlap), but meaning incomplete
- Score: 1

### Rule R0_other (Score 0)
**Condition**: (catchall — no conditions)
**Meaning**: No prior rule matched — insufficient production or completely wrong
**Example**: Any response that doesn't match higher-scoring rules
**Score**: 0

## Preprocessing Pipeline

### 1. Normalization
Two forms are created:
- **Display form**: For human readability (preserves diacritics, case)
- **Match form**: For scoring (lowercase, punctuation stripped, diacritics folded)

**Normalization steps**:
1. Lowercase (if enabled)
2. Strip punctuation (if enabled)
3. Normalize whitespace (if enabled)
4. Fold diacritics for matching (if enabled)
5. Strip filler words (eh, um, este, etc.)
6. Expand contractions (del → de el, al → a el)

**Example**:
- Original: "El libro está en la mesa."
- Display: "El libro está en la mesa."
- Match: "el libro esta en la mesa"

### 2. Tokenization
- Split on whitespace
- Split Spanish enclitics (me, te, se, lo, la, le, nos, os, los, las, les)
- Optional apostrophe handling

**Example**:
- "El libro está en la mesa." → ["el", "libro", "esta", "en", "la", "mesa"]
- "Dámelo." → ["dame", "lo"] (enclitic split)

### 3. Alignment
- Needleman-Wunsch algorithm (global sequence alignment)
- Deterministic tie-breaking (prefers matches, then insertions, then deletions)
- Produces alignment operations: match, substitution, insertion, deletion

**Example**:
```
Reference: el libro esta en la mesa
Response:  el libro esta en X mesa
Alignment: match match match match match sub match
```

## Error Classification

Substitutions are classified into three types:

### 1. Near-Synonym Substitution
- Morphological variants: tiene/tenía, es/era, niño/niños
- Lexical near-synonyms: hablar/decir, empezar/comenzar
- **Treatment**: Counted separately, not as content_subs
- **Rationale**: Meaning is preserved despite form change

### 2. Function Word Substitution
- Articles: el/la, un/una
- Prepositions: a/de, en/con
- Conjunctions: y/pero, que/si
- **Treatment**: Counted separately, not as content_subs
- **Rationale**: Function words carry less meaning than content words

### 3. Content Word Substitution
- Nouns, verbs, adjectives, adverbs
- Full meaning change
- **Treatment**: Counted as content_subs
- **Rationale**: Indicates loss of propositional meaning

## Scoring Examples

### Example 1: Perfect Repetition (Score 4)
```
Item 2: "El libro está en la mesa."
Response: "El libro esta en la mesa."
Analysis:
  - Normalization removes accent: "el libro esta en la mesa"
  - Alignment: 7 matches, 0 edits
  - Applied rule: R4_perfect (max_edits: 0)
Score: 4/4
```

### Example 2: Meaning Preserved (Score 3)
```
Item 16: "El niño que se murió está triste."
Response: "El niño que se m- murio cato esta triste."
Analysis:
  - Tokens: ["el", "niño", "que", "se", "m", "murio", "cato", "esta", "triste"]
  - Reference tokens: ["el", "niño", "que", "se", "murio", "esta", "triste"]
  - Alignment: 6 matches, 1 deletion (m), 1 substitution (cato→está)
  - total_edits: 2
  - content_subs: 0 (cato is not a content word, it's noise)
  - idea_unit_coverage: 6/6 = 1.0 (all content words present)
  - Applied rule: R3_meaning_preserved (max_edits: 3, max_content_subs: 0, IU_cov: 0.80)
Score: 3/4
```

### Example 3: More Than Half Idea Units (Score 2)
```
Item 12: "Después de cenar me fui a dormir tranquilo."
Response: "Después de cenar me fui a X tranquilo."
Analysis:
  - Reference tokens: ["despues", "de", "cenar", "me", "fui", "a", "dormir", "tranquilo"]
  - Response tokens: ["despues", "de", "cenar", "me", "fui", "a", "x", "tranquilo"]
  - Alignment: 7 matches, 1 substitution (dormir→x)
  - total_edits: 1
  - content_subs: 1 (dormir is a content word)
  - idea_unit_coverage: 6/7 = 0.86 (6 of 7 content words present)
  - Applied rule: R2_more_than_half_iu (IU_cov: 0.50, content_subs: 2, length_ratio: 0.40)
Score: 2/4
```

### Example 4: Less Than Half Idea Units (Score 1)
```
Item 6: "Dudo que sepa manejar muy bien."
Response: "Dudo que sepa ma- tambien."
Analysis:
  - Reference tokens: ["dudo", "que", "sepa", "manejar", "muy", "bien"]
  - Response tokens: ["dudo", "que", "sepa", "ma", "tambien"]
  - Alignment: 3 matches, 2 deletions (manejar, muy), 1 substitution (bien→tambien)
  - total_edits: 3
  - content_subs: 1 (bien→tambien)
  - idea_unit_coverage: 3/5 = 0.60 (3 of 5 content words present)
  - Applied rule: R1_less_than_half_iu (IU_cov: 0.15, content_overlap: 0.15, hyp_min_tokens: 2)
Score: 1/4
```

### Example 5: Gibberish (Score 0)
```
Item 28: "El examen no fue tan difícil como me habían dicho."
Response: "[gibberish]"
Analysis:
  - is_gibberish: true (matches noise pattern)
  - Applied rule: R0_gibberish (is_gibberish: true)
Score: 0/4
```

## Scoring Trace

Every scored response includes a detailed trace with:
- **display_ref**: Reference sentence (human-readable)
- **display_hyp**: Response sentence (human-readable)
- **match_ref**: Reference after normalization (for scoring)
- **match_hyp**: Response after normalization (for scoring)
- **ref_tokens**: Reference tokens
- **hyp_tokens**: Response tokens
- **alignment**: Alignment operations (match/sub/ins/del)
- **alignment_cost**: Total alignment cost
- **error_counts**: Breakdown of error types
- **total_edits**: Total insertions + deletions + substitutions
- **content_subs**: Full content word substitutions
- **overlap_ratio**: Token overlap (multiset-based)
- **content_overlap**: Content-word-only overlap
- **idea_unit_coverage**: Proportion of reference content reproduced
- **word_order_penalty**: Reordering severity (0=perfect, 1=fully reordered)
- **is_gibberish**: Boolean noise detection
- **near_synonym_subs**: Count of morphological variants
- **applied_rule_ids**: Which rule(s) matched
- **score**: Final score (0–4)
- **max_points**: Maximum possible score

## Customization

### Adjusting Rule Thresholds
Edit `eit_scorer/config/default_rubric.yaml`:
```yaml
rules:
  - id: R3_meaning_preserved
    when:
      max_edits: 3              # ← Adjust this
      max_content_subs: 0       # ← Or this
      min_idea_unit_coverage: 0.80  # ← Or this
    then:
      score: 3
```

### Adding New Rules
```yaml
rules:
  - id: R3_custom_rule
    description: "Custom rule for specific cases"
    when:
      min_idea_unit_coverage: 0.75
      max_content_subs: 1
      max_word_order_penalty: 0.30
    then:
      score: 3
```

### Modifying Preprocessing
```yaml
normalization:
  lowercase: true
  strip_punctuation: true
  fold_diacritics_for_matching: false  # ← Change this to true to ignore accents
  expand_contractions: true
  filler_words: [eh, um, uh, este, mm]  # ← Add/remove filler words

tokenization:
  split_enclitics: true
  enclitics: [me, te, se, lo, la, le, nos, os, los, las, les]  # ← Add/remove enclitics
```

## Troubleshooting

### Score is lower than expected
1. Check the **applied_rule_ids** in the trace
2. Verify the **feature values** (overlap_ratio, idea_unit_coverage, etc.)
3. Check if response contains **content substitutions** (meaning-changing errors)
4. Verify **normalization** is working correctly (check display_hyp vs match_hyp)

### Score is higher than expected
1. Check if a **higher-scoring rule** matched unexpectedly
2. Verify **feature thresholds** in the rule conditions
3. Check if **near-synonyms** are being counted correctly
4. Verify **gibberish detection** is working (for low-quality responses)

### Inconsistent scores
1. Ensure **rubric YAML** is not being modified between runs
2. Check for **non-deterministic preprocessing** (should not happen)
3. Verify **tokenization** is consistent (check ref_tokens vs hyp_tokens)
4. Check **alignment** is deterministic (same input should produce same alignment)

## References

- **Ortega, L. (2000)**: Understanding syntactic complexity: The measurement of change in the syntax of instructed L2 Spanish learners. Unpublished doctoral dissertation, University of Hawai'i at Manoa.
- **Faretta-Stutenberg et al. (2023)**: Parallel forms reliability of two versions of the Spanish Elicited Imitation Task. *Research Methods in Applied Linguistics*, 2(3). https://doi.org/10.1016/j.rmal.2023.100070
