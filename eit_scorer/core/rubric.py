"""
eit_scorer/core/rubric.py
===========================
Loads and validates the YAML rubric file into Python objects.

The rubric YAML is the SINGLE SOURCE OF TRUTH for all scoring logic.
Never hardcode scoring values in Python — always read from the YAML.

Rubric schema overview:
    rubric:
      name: "..."
      version: "..."
      scale:
        max_points_per_item: 4
      rules:
        - id: R4_perfect
          description: "..."
          when:
            max_edits: 0
          then:
            score: 4
      normalization: { ... }
      tokenization:  { ... }
      alignment:     { ... }
      error_labeling:
        function_words: [...]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from eit_scorer.core.normalization  import NormalizationConfig
from eit_scorer.core.tokenization   import TokenizationConfig
from eit_scorer.core.alignment      import AlignmentConfig
from eit_scorer.core.error_labeling import ErrorLabelingConfig


# ─────────────────────────────────────────────────────────────
# RUBRIC RULE
# ─────────────────────────────────────────────────────────────

@dataclass
class RubricRule:
    rule_id:     str
    description: str
    when:        dict[str, Any]   # condition dict — interpreted by scoring.py
    score:       int


# ─────────────────────────────────────────────────────────────
# FULL RUBRIC CONFIG
# ─────────────────────────────────────────────────────────────

@dataclass
class RubricConfig:
    name:             str
    version:          str
    max_points:       int
    rules:            list[RubricRule]
    normalization:    NormalizationConfig
    tokenization:     TokenizationConfig
    alignment:        AlignmentConfig
    error_labeling:   ErrorLabelingConfig

    def summary(self) -> str:
        return (
            f"Rubric '{self.name}' v{self.version} | "
            f"max_points={self.max_points} | "
            f"{len(self.rules)} rules"
        )


# ─────────────────────────────────────────────────────────────
# LOADER
# ─────────────────────────────────────────────────────────────

def load_rubric(path: str | Path) -> RubricConfig:
    """
    Load and validate a rubric YAML file.
    Returns a fully constructed RubricConfig.
    Raises ValueError on schema violations.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Rubric not found: {path}")

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    rubric_raw = raw.get("rubric", raw)   # support top-level or nested

    # ── Basic metadata ──
    name    = rubric_raw.get("name", "unnamed")
    version = str(rubric_raw.get("version", "1.0"))
    scale   = rubric_raw.get("scale", {})
    max_pts = int(scale.get("max_points_per_item", 4))

    # ── Rules ──
    rules_raw = rubric_raw.get("rules", [])
    if not rules_raw:
        raise ValueError(f"Rubric '{path}' has no rules defined.")
    rules: list[RubricRule] = []
    for r in rules_raw:
        then_block = r.get("then", {})
        rules.append(RubricRule(
            rule_id=r["id"],
            description=r.get("description", ""),
            when=r.get("when", {}),
            score=int(then_block.get("score", 0)),
        ))

    # ── Normalization ──
    norm_raw = rubric_raw.get("normalization", {})
    norm_cfg = NormalizationConfig(
        lowercase=norm_raw.get("lowercase", True),
        strip_punctuation=norm_raw.get("strip_punctuation", True),
        normalize_whitespace=norm_raw.get("normalize_whitespace", True),
        fold_diacritics_for_matching=norm_raw.get("fold_diacritics_for_matching", False),
        expand_contractions=norm_raw.get("expand_contractions", True),
        strip_filler_words=norm_raw.get("strip_filler_words", True),
        filler_words=norm_raw.get("filler_words", [
            "eh", "um", "uh", "este", "mm", "mhm", "hmm", "ah", "eeh"
        ]),
        contraction_map=norm_raw.get("contraction_map", {"del": ["de","el"], "al": ["a","el"]}),
    )

    # ── Tokenization ──
    tok_raw = rubric_raw.get("tokenization", {})
    tok_cfg = TokenizationConfig(
        split_on_whitespace=tok_raw.get("split_on_whitespace", True),
        keep_apostrophes=tok_raw.get("keep_apostrophes", False),
        split_enclitics=tok_raw.get("split_enclitics", True),
        enclitics=tok_raw.get("enclitics", [
            "selos","selas","melos","melas","telos","telas","noslos","noslas",
            "selo","sela","melo","mela","telo","tela",
            "nos","los","las","les","me","te","se","lo","la","le","os",
        ]),
    )

    # ── Alignment ──
    al_raw = rubric_raw.get("alignment", {})
    al_cfg = AlignmentConfig(
        match_score=float(al_raw.get("match_score", 2.0)),
        mismatch_penalty=float(al_raw.get("mismatch_penalty", -1.0)),
        gap_penalty=float(al_raw.get("gap_penalty", -1.0)),
    )

    # ── Error labeling ──
    el_raw = rubric_raw.get("error_labeling", {})
    fw_list = el_raw.get("function_words", [])
    el_cfg = ErrorLabelingConfig(function_words=set(fw_list) if fw_list else ErrorLabelingConfig().function_words)

    return RubricConfig(
        name=name,
        version=version,
        max_points=max_pts,
        rules=rules,
        normalization=norm_cfg,
        tokenization=tok_cfg,
        alignment=al_cfg,
        error_labeling=el_cfg,
    )
