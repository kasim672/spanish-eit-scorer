# Spanish EIT Scoring System: Architecture & Design Decisions

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: EIT Response                       │
│  (participant_id, item_id, response_text, human_scores)     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  NORMALIZATION LAYER                         │
│  • Lowercase, punctuation stripping, diacritics folding      │
│  • Contraction expansion (del→de el, al→a el)               │
│  • Filler word stripping (eh, um, este, etc.)               │
│  • Two forms: display (human-readable) + match (for scoring) │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  TOKENIZATION LAYER                          │
│  • Whitespace-based splitting                               │
│  • Spanish enclitic splitting (me, te, se, lo, la, etc.)    │
│  • Deterministic: same text → same tokens                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   ALIGNMENT LAYER                            │
│  • Needleman-Wunsch global sequence alignment               │
│  • Deterministic tie-breaking (match > insert > delete)     │
│  • Produces: alignment operations (match/sub/ins/del)       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 ERROR LABELING LAYER                         │
│  • Classify substitutions: near-synonym / function / content │
│  • Count errors by type                                      │
│  • Compute: total_edits, content_subs, near_synonym_subs    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FEATURE EXTRACTION LAYER                        │
│  • token_overlap_ratio (multiset-based recall)              │
│  • content_overlap (content-word-only overlap)              │
│  • idea_unit_coverage (reference content reproduced)        │
│  • word_order_penalty (LCS-based reordering severity)       │
│  • is_gibberish (noise detection)                           │
│  • length_ratio (response completeness)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 RULE MATCHING LAYER                          │
│  • Build ScoreContext (feature vector)                      │
│  • Apply rules in order (first match wins)                  │
│  • Each rule: conditions (when) → score (then)              │
│  • 11 rules covering scores 0–4                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  OUTPUT: ScoredSentence                      │
│  • score (0–4)                                              │
│  • max_points (4)                                           │
│  • trace (detailed scoring information)                     │
│  • human_rater_a, human_rater_b (if available)              │
│  • adjudicated (averaged human score)                       │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Normalization (`eit_scorer/core/normalization.py`)

**Purpose**: Prepare text for scoring while preserving human readability

**Design decisions**:
- **Two-form normalization**: Display form (human-readable) + Match form (for scoring)
- **Configurable preprocessing**: Lowercase, punctuation, diacritics, contractions
- **Deterministic**: Same input always produces same output
- **Reversible**: Can trace back from match form to display form

**Key functions**:
- `normalize_text()`: Returns (display_form, match_form)
- `expand_contractions_tokens()`: Expands Spanish contractions
- `_fold_diacritics()`: Removes accents for matching

**Configuration** (in YAML):
```yaml
normalization:
  lowercase: true
  strip_punctuation: true
  normalize_whitespace: true
  fold_diacritics_for_matching: false
  expand_contractions: true
  strip_filler_words: true
  filler_words: [eh, um, uh, este, mm, mhm, hmm, ah, eeh]
  contraction_map: {del: [de, el], al: [a, el]}
```

### 2. Tokenization (`eit_scorer/core/tokenization.py`)

**Purpose**: Split text into tokens for alignment

**Design decisions**:
- **Whitespace-based**: Simple, deterministic, language-agnostic
- **Enclitic splitting**: Handles Spanish clitics (me, te, se, lo, la, etc.)
- **Configurable**: Can enable/disable enclitic splitting
- **Deterministic**: Same text → same tokens

**Key functions**:
- `tokenize()`: Split text into tokens
- `split_spanish_enclitics()`: Split clitics from verbs
- `_peel_enclitics()`: Recursively peel enclitics

**Configuration** (in YAML):
```yaml
tokenization:
  split_on_whitespace: true
  keep_apostrophes: false
  split_enclitics: true
  enclitics: [selos, selas, melos, melas, telos, telas, noslos, noslas, ...]
```

### 3. Alignment (`eit_scorer/core/alignment.py`)

**Purpose**: Align reference and response tokens to identify differences

**Design decisions**:
- **Needleman-Wunsch algorithm**: Global sequence alignment (not local)
- **Deterministic tie-breaking**: Prefers matches, then insertions, then deletions
- **Configurable scoring**: Match score, mismatch penalty, gap penalty
- **Produces alignment operations**: match, substitution, insertion, deletion

**Key functions**:
- `align_tokens()`: Perform global alignment
- Returns: (alignment_ops, alignment_cost)

**Configuration** (in YAML):
```yaml
alignment:
  match_score: 2.0
  mismatch_penalty: -1.0
  gap_penalty: -1.0
```

**Why Needleman-Wunsch?**
- Global alignment ensures we capture all differences (not just local matches)
- Deterministic tie-breaking ensures reproducibility
- Simple, well-understood algorithm
- O(n*m) complexity is acceptable for sentence-length inputs

### 4. Error Labeling (`eit_scorer/core/error_labeling.py`)

**Purpose**: Classify errors and compute meaning-based features

**Design decisions**:
- **Typed error classification**: near-synonym / function / content
- **Near-synonym awareness**: Morphological variants don't count as content subs
- **Content-word focus**: Meaning is carried by content words, not function words
- **Multiset-based overlap**: Handles repeated words correctly

**Key functions**:
- `count_errors()`: Classify substitutions and count errors
- `token_overlap_ratio()`: Multiset-based recall
- `content_overlap_ratio()`: Content-word-only overlap
- `idea_unit_coverage()`: Proportion of reference content reproduced
- `word_order_penalty()`: LCS-based reordering severity
- `is_gibberish()`: Detect transcription noise

**Error classification priority**:
1. Check if pair is in near-synonym table → near_synonym_sub
2. Check if ref token is function word → function_sub
3. Otherwise → content_sub

**Why this design?**
- Distinguishes meaning-preserving errors (near-synonyms) from meaning-changing errors
- Focuses on content words, which carry propositional meaning
- Aligns with Ortega (2000) rubric emphasis on meaning preservation

### 5. Scoring (`eit_scorer/core/scoring.py`)

**Purpose**: Apply rules to features and produce final score

**Design decisions**:
- **Rule-based**: Explicit rules, not learned models
- **First-match-wins**: Rules applied in order, first match determines score
- **Feature-based**: Rules condition on 10 deterministic features
- **Fully traceable**: Every score decision is auditable

**Key functions**:
- `score_response()`: Main scoring function
- `_rule_matches()`: Evaluate rule conditions against context
- Returns: ScoredSentence with full trace

**Rule structure**:
```yaml
- id: R3_meaning_preserved
  description: "Meaning fully preserved despite minor form errors"
  when:
    max_edits: 3
    max_content_subs: 0
    min_idea_unit_coverage: 0.80
  then:
    score: 3
```

**Why rule-based?**
- Transparent: Every score is traceable to explicit rules
- Interpretable: Rules directly reflect rubric descriptors
- Maintainable: Easy to adjust thresholds or add rules
- Reproducible: No randomness, no learned parameters

### 6. Rubric (`eit_scorer/core/rubric.py`)

**Purpose**: Load and validate rubric configuration

**Design decisions**:
- **YAML-based**: Single source of truth for all scoring logic
- **Validated**: Schema checking on load
- **Versioned**: Rubric version tracked for reproducibility
- **Configurable**: All parameters in YAML, no hardcoding

**Key functions**:
- `load_rubric()`: Load and validate YAML rubric
- Returns: RubricConfig with all parameters

**Why YAML?**
- Human-readable and editable
- Version-controllable (git-friendly)
- No code changes needed to adjust thresholds
- Easy to maintain multiple versions

## Data Models (`eit_scorer/data/models.py`)

### EITItem
```python
@dataclass
class EITItem:
    item_id: int
    reference: str
    max_points: int | None = 4
```

### EITResponse
```python
@dataclass
class EITResponse:
    participant_id: str
    item_id: int
    response_text: str
    human_rater_a: float | None = None
    human_rater_b: float | None = None
    meta: dict[str, Any] | None = None
```

### ScoredSentence
```python
@dataclass
class ScoredSentence:
    participant_id: str
    item_id: int
    response_text: str
    score: int
    max_points: int
    trace: ScoringTrace
    human_rater_a: float | None = None
    human_rater_b: float | None = None
    adjudicated: float | None = None
    meta: dict[str, Any] | None = None
```

### ScoringTrace
```python
@dataclass
class ScoringTrace:
    display_ref: str
    display_hyp: str
    match_ref: str
    match_hyp: str
    ref_tokens: list[str]
    hyp_tokens: list[str]
    alignment: list[AlignmentOp]
    alignment_cost: float
    error_counts: dict[str, int]
    total_edits: int
    content_subs: int
    overlap_ratio: float
    content_overlap: float
    idea_unit_coverage: float
    word_order_penalty: float
    is_gibberish: bool
    near_synonym_subs: int
    applied_rule_ids: list[str]
    score: int
    max_points: int
```

## Key Design Principles

### 1. Determinism
- **Same input → same score**: No randomness, no LLM calls
- **Reproducible**: Suitable for research and large-scale evaluation
- **Auditable**: Every score can be traced to explicit rules

**Implementation**:
- All algorithms are deterministic (no randomness)
- Tie-breaking is explicit (prefers matches, then insertions, then deletions)
- No external dependencies (no spaCy, no neural networks)

### 2. Interpretability
- **Rule-based**: Explicit rules, not learned models
- **Feature-rich**: 10+ deterministic features capture meaning preservation
- **Traceable**: Full scoring trace available for inspection

**Implementation**:
- Rules directly reflect Ortega (2000) rubric descriptors
- Features are human-understandable (overlap, coverage, reordering)
- Trace includes all intermediate values

### 3. Rubric Alignment
- **Direct reflection of Ortega (2000)**: Scores 0–4 map directly to rubric descriptors
- **Meaning-based evaluation**: Focuses on idea-unit preservation, not syntax
- **Noise-aware**: Handles disfluencies (false starts, hesitations) per rubric guidelines

**Implementation**:
- Rules named after rubric levels (R0, R1, R2, R3, R4)
- Features focus on content preservation (idea units, content overlap)
- Preprocessing handles disfluencies (false starts, hesitations)

### 4. Efficiency
- **No external dependencies**: No spaCy, no neural networks, no API calls
- **Fast**: Alignment is O(n*m), all features are O(n) or O(n*m)
- **Scalable**: Suitable for batch processing large datasets

**Implementation**:
- Pure Python, no external NLP libraries
- Efficient algorithms (Needleman-Wunsch, LCS)
- Minimal memory footprint

### 5. Maintainability
- **Single source of truth**: All scoring logic in YAML rubric
- **Configurable**: All parameters in YAML, no hardcoding
- **Versioned**: Rubric version tracked for reproducibility
- **Documented**: Comprehensive documentation and examples

**Implementation**:
- YAML-based rubric configuration
- No scoring logic in Python code
- Version control for all rubric changes
- Detailed documentation and examples

## Removed Components
### ❌ Neural Similarity Network
**Why removed**:
- Introduced non-determinism (learned parameters)
- Difficult to interpret (black box)
- Overkill for EIT scoring (simple overlap metrics sufficient)
- Difficult to reproduce (requires specific model weights)
**Replacement**:
- Multiset-based token overlap (deterministic, interpretable)
- Content-word-only overlap (deterministic, interpretable)
- Idea-unit coverage (deterministic, interpretable)
### ❌ Probabilistic Features
**Why removed**:
- Introduced non-determinism
- Difficult to interpret
- Not needed for rule-based scoring
**Replacement**:
- Deterministic features (overlap, coverage, reordering)
- All features are human-understandable

## Testing Strategy

### Unit Tests
- **Alignment**: Verify Needleman-Wunsch correctness
- **Determinism**: Verify same input → same score
- **Pipeline**: Verify end-to-end scoring

### Integration Tests
- **Synthetic data**: Score synthetic responses with known scores
- **Edge cases**: Empty, gibberish, reordered, near-synonyms
- **Performance**: Verify ≥100 scores/second

### Validation Tests
- **Human comparison**: Compare against human-scored dataset
- **Metrics**: Exact match, within ±1, MAE, correlation
- **Error analysis**: Identify systematic errors

## Configuration Management

### Rubric Versioning
```
eit_scorer/config/
├── default_rubric.yaml          # Current version (v2.0)
├── default_rubric_v1.9.yaml     # Previous version
└── default_rubric_v1.8.yaml     # Older version
```

### Runtime Configuration
```python
# Load specific rubric version
rubric = load_rubric("eit_scorer/config/default_rubric_v2.0.yaml")

# Or use default
rubric = load_rubric("eit_scorer/config/default_rubric.yaml")
```

### Logging Configuration
```python
import logging
logger = logging.getLogger("eit_scorer")
logger.info(f"Loaded rubric: {rubric.name} v{rubric.version}")
logger.info(f"Scored item {item_id}: {score}/4 (rule: {applied_rule})")
```

## Performance Characteristics

| Operation | Complexity | Time (typical) |
|-----------|-----------|----------------|
| Normalization | O(n) | <1ms |
| Tokenization | O(n) | <1ms |
| Alignment | O(n*m) | 1–5ms |
| Error labeling | O(n) | <1ms |
| Feature extraction | O(n*m) | 1–5ms |
| Rule matching | O(r) | <1ms |
| **Total** | **O(n*m)** | **5–15ms** |

Where n = reference length, m = response length, r = number of rules

**Throughput**: ~100 scores/second on standard hardware

## Future Enhancements

### Short-term (v2.1–v2.2)
- [ ] Add more near-synonym pairs
- [ ] Refine rule thresholds based on validation
- [ ] Add support for multiple languages
- [ ] Create REST API wrapper

### Medium-term (v3.0)
- [ ] Support for partial credit (0.5-point increments)
- [ ] Confidence scores (how confident is the system?)
- [ ] Explanation generation (why this score?)
- [ ] Interactive rule editor

### Long-term (v4.0)
- [ ] Machine learning for rule optimization
- [ ] Automatic rubric generation from examples
- [ ] Multi-language support
- [ ] Integration with learning management systems

## References

- **Ortega (2000)**: Understanding syntactic complexity
- **Faretta-Stutenberg et al. (2023)**: Parallel forms reliability study
- **Needleman-Wunsch**: Global sequence alignment algorithm
- **LCS**: Longest Common Subsequence for word order analysis

---

**Last updated**: 2024-03-27
**Status**: Complete
