# Spanish EIT Scoring System: Documentation Index

## 📚 Documentation Overview

This project includes comprehensive documentation for the Spanish EIT (Elicited Imitation Task) scoring system. Start here to find the right guide for your needs.

## 🎯 Quick Start

**New to the system?** Start here:
1. Read **`PROJECT_SUMMARY.md`** (5 min) — Overview of what changed and why
2. Read **`QUICK_REFERENCE.md`** (10 min) — Scoring scale, features, and rules
3. Try **`SCORING_GUIDE.md`** (30 min) — Detailed guide with examples

**Want to understand the architecture?** Read:
1. **`ARCHITECTURE.md`** (20 min) — System design and components
2. **`IMPLEMENTATION_SUMMARY.md`** (15 min) — Implementation details

**Ready to deploy?** Follow:
1. **`NEXT_STEPS.md`** (30 min) — Validation, calibration, and deployment roadmap

## 📖 Documentation Files

### User Guides

#### `PROJECT_SUMMARY.md` (Executive Summary)
**What**: High-level overview of the system redesign
**Who**: Project managers, stakeholders, new team members
**When**: Start here first
**Length**: 10 minutes
**Contents**:
- Executive summary
- What changed (before/after)
- System architecture overview
- Key components
- Usage examples
- Next steps

#### `QUICK_REFERENCE.md` (Quick Reference Card)
**What**: One-page reference for scoring scale, features, and rules
**Who**: Scorers, developers, anyone needing quick lookup
**When**: Use while scoring or debugging
**Length**: 5 minutes (reference)
**Contents**:
- Scoring scale (0–4)
- 10 scoring features
- 11 rubric rules
- Error types
- Preprocessing pipeline
- Common scoring patterns
- Debugging tips
- Python API

#### `SCORING_GUIDE.md` (Complete Scoring Guide)
**What**: Comprehensive guide to scoring system
**Who**: Scorers, researchers, anyone learning the system
**When**: Read to understand scoring in detail
**Length**: 30 minutes
**Contents**:
- Scoring scale (Ortega 2000)
- 10 scoring features (detailed)
- 11 rubric rules (detailed)
- Preprocessing pipeline
- Error classification
- Scoring examples (5 detailed examples)
- Scoring trace explanation
- Customization guide
- Troubleshooting

### Technical Documentation

#### `IMPLEMENTATION_SUMMARY.md` (Implementation Overview)
**What**: Overview of implementation and design
**Who**: Developers, technical leads
**When**: Read to understand how system works
**Length**: 15 minutes
**Contents**:
- Current status
- Key components (6 components)
- Rubric rules (table)
- Design principles (5 principles)
- Removed components
- Testing & validation
- Usage examples
- Configuration
- Next steps

#### `ARCHITECTURE.md` (Architecture & Design Decisions)
**What**: Detailed architecture and design decisions
**Who**: Developers, architects, anyone modifying system
**When**: Read before making changes
**Length**: 20 minutes
**Contents**:
- System overview (diagram)
- Core components (6 components, detailed)
- Data models
- Key design principles (5 principles)
- Removed components (with rationale)
- Testing strategy
- Configuration management
- Performance characteristics
- Future enhancements

### Deployment & Roadmap

#### `NEXT_STEPS.md` (Validation & Deployment Roadmap)
**What**: Step-by-step roadmap for validation, calibration, testing, and deployment
**Who**: Project managers, developers, QA
**When**: Read before starting validation phase
**Length**: 30 minutes
**Contents**:
- Current status
- Phase 1: Validation (weeks 1–2)
- Phase 2: Calibration (weeks 2–3)
- Phase 3: Testing & QA (week 3)
- Phase 4: Documentation & Deployment (week 4)
- Phase 5: Ongoing Maintenance (ongoing)
- Success criteria
- Timeline
- Resources needed
- Risks & mitigation
- Questions & decisions

## 🔍 Finding What You Need

### By Role

**Project Manager**
1. `PROJECT_SUMMARY.md` — Understand what changed
2. `NEXT_STEPS.md` — Follow deployment roadmap
3. `QUICK_REFERENCE.md` — Understand scoring scale

**Scorer / Researcher**
1. `QUICK_REFERENCE.md` — Learn scoring scale and rules
2. `SCORING_GUIDE.md` — Understand scoring in detail
3. `QUICK_REFERENCE.md` — Use as reference while scoring

**Developer**
1. `PROJECT_SUMMARY.md` — Understand system overview
2. `ARCHITECTURE.md` — Understand system design
3. `IMPLEMENTATION_SUMMARY.md` — Understand implementation
4. Code docstrings — Understand specific functions

**QA / Tester**
1. `NEXT_STEPS.md` — Follow testing roadmap
2. `QUICK_REFERENCE.md` — Understand scoring rules
3. `SCORING_GUIDE.md` — Understand edge cases

### By Task

**Understanding the System**
1. `PROJECT_SUMMARY.md` — High-level overview
2. `ARCHITECTURE.md` — Detailed architecture
3. `IMPLEMENTATION_SUMMARY.md` — Implementation details

**Scoring Responses**
1. `QUICK_REFERENCE.md` — Scoring scale and rules
2. `SCORING_GUIDE.md` — Detailed guide with examples
3. Code docstrings — Specific function documentation

**Customizing Rules**
1. `SCORING_GUIDE.md` — Understand current rules
2. `ARCHITECTURE.md` — Understand rule structure
3. `eit_scorer/config/default_rubric.yaml` — Edit rules

**Debugging Scores**
1. `QUICK_REFERENCE.md` — Debugging tips
2. `SCORING_GUIDE.md` — Troubleshooting section
3. Scoring trace — Inspect detailed scoring information

**Deploying System**
1. `NEXT_STEPS.md` — Follow deployment roadmap
2. `ARCHITECTURE.md` — Understand system design
3. `IMPLEMENTATION_SUMMARY.md` — Understand configuration

## 📊 Documentation Map

```
PROJECT_SUMMARY.md (Executive Summary)
├── What changed (before/after)
├── System architecture overview
├── Key components
├── Usage examples
└── Next steps

QUICK_REFERENCE.md (Quick Reference)
├── Scoring scale (0–4)
├── 10 scoring features
├── 11 rubric rules
├── Common patterns
└── Debugging tips

SCORING_GUIDE.md (Complete Guide)
├── Scoring scale (detailed)
├── 10 scoring features (detailed)
├── 11 rubric rules (detailed)
├── 5 scoring examples
├── Scoring trace explanation
├── Customization guide
└── Troubleshooting

IMPLEMENTATION_SUMMARY.md (Implementation)
├── Current status
├── Key components (6)
├── Rubric rules (table)
├── Design principles (5)
├── Removed components
├── Testing & validation
└── Configuration

ARCHITECTURE.md (Architecture)
├── System overview (diagram)
├── Core components (6, detailed)
├── Data models
├── Design principles (5)
├── Removed components (rationale)
├── Testing strategy
├── Configuration management
└── Performance characteristics

NEXT_STEPS.md (Roadmap)
├── Phase 1: Validation
├── Phase 2: Calibration
├── Phase 3: Testing & QA
├── Phase 4: Documentation & Deployment
├── Phase 5: Ongoing Maintenance
├── Success criteria
├── Timeline
└── Resources needed
```

## 🚀 Getting Started

### Step 1: Understand the System (15 minutes)
```
Read: PROJECT_SUMMARY.md
Focus on: What changed, System architecture, Key components
```

### Step 2: Learn Scoring (20 minutes)
```
Read: QUICK_REFERENCE.md + SCORING_GUIDE.md
Focus on: Scoring scale, Features, Rules, Examples
```

### Step 3: Understand Architecture (20 minutes)
```
Read: ARCHITECTURE.md
Focus on: System overview, Core components, Design principles
```

### Step 4: Plan Deployment (30 minutes)
```
Read: NEXT_STEPS.md
Focus on: Validation, Calibration, Testing, Deployment
```

**Total time**: ~85 minutes to understand the complete system

## 📝 Key Concepts

### Scoring Scale (Ortega 2000)
| Score | Meaning |
|-------|---------|
| **4** | Perfect repetition |
| **3** | Meaning preserved |
| **2** | More than half idea units |
| **1** | Less than half idea units |
| **0** | No meaningful output |

### 10 Scoring Features
1. `total_edits` — Insertions + deletions + substitutions
2. `content_subs` — Full content word substitutions
3. `overlap_ratio` — Multiset-based token recall
4. `content_overlap` — Content-word-only overlap
5. `idea_unit_coverage` — Proportion of reference content reproduced
6. `word_order_penalty` — Reordering severity
7. `length_ratio` — Response completeness
8. `hyp_min_tokens` — Number of tokens
9. `is_gibberish` — Transcription noise detection
10. `near_synonym_subs` — Morphological variants

### 11 Rubric Rules
- R0_gibberish (Score 0)
- R0_empty_or_too_short (Score 0)
- R4_perfect (Score 4)
- R3_meaning_preserved (Score 3)
- R3_reordered_complete (Score 3)
- R2_more_than_half_iu (Score 2)
- R2_good_overlap_some_loss (Score 2)
- R1_less_than_half_iu (Score 1)
- R1_some_overlap_short (Score 1)
- R0_other (Score 0)

## 🔗 Related Files

### Code Files
- `eit_scorer/core/scoring.py` — Main scoring pipeline
- `eit_scorer/core/rubric.py` — Rubric loading
- `eit_scorer/config/default_rubric.yaml` — Rubric configuration
- `eit_scorer/core/alignment.py` — Alignment algorithm
- `eit_scorer/core/error_labeling.py` — Error classification
- `eit_scorer/core/normalization.py` — Text normalization
- `eit_scorer/core/tokenization.py` — Text tokenization

### Test Files
- `tests/test_alignment.py` — Alignment tests
- `tests/test_determinism.py` — Determinism tests
- `tests/test_synth_pipeline.py` — Pipeline tests

### Example Data
- `examples/synth_dataset/` — Example datasets
- `data/synth/` — Synthetic test data

## ❓ FAQ

**Q: Where do I start?**
A: Read `PROJECT_SUMMARY.md` first, then `QUICK_REFERENCE.md`.

**Q: How do I score a response?**
A: See `SCORING_GUIDE.md` for detailed guide with examples.

**Q: How do I customize rules?**
A: See `SCORING_GUIDE.md` "Customization" section and `ARCHITECTURE.md`.

**Q: How do I debug a score?**
A: See `QUICK_REFERENCE.md` "Debugging Tips" and `SCORING_GUIDE.md` "Troubleshooting".

**Q: What changed from the old system?**
A: See `PROJECT_SUMMARY.md` "What Changed" section.

**Q: How do I deploy the system?**
A: See `NEXT_STEPS.md` for step-by-step roadmap.

**Q: What are the design principles?**
A: See `ARCHITECTURE.md` "Key Design Principles" section.

**Q: How do I understand the architecture?**
A: See `ARCHITECTURE.md` for detailed architecture and design decisions.

## 📞 Support

- **Questions**: Check the relevant documentation file
- **Bug reports**: File issues on GitHub
- **Feature requests**: Submit via issue tracker
- **Documentation issues**: Report via GitHub

## 📅 Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 2.0 | 2024-03-27 | ✅ Complete | Deterministic implementation |
| 1.0 | 2024-03-01 | ❌ Deprecated | Probabilistic implementation |

## 📄 License

[Add license information here]

---

**Last Updated**: 2024-03-27
**Status**: ✅ Complete
**Next Phase**: Validation (see `NEXT_STEPS.md`)
