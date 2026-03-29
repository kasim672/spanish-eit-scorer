"""
eit_scorer/core/rubric_engine.py
==================================
Rule-based scoring engine.

Maps features to scores using explicit rubric rules.
Implements Ortega (2000) EIT scoring scale (0–4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RubricRule:
    """A single scoring rule."""
    rule_id: str
    description: str
    conditions: dict[str, Any]  # Feature conditions (when)
    score: int                   # Output score (then)


@dataclass
class RubricEngine:
    """Rule-based scoring engine."""
    rules: list[RubricRule]
    max_points: int = 4
    
    def score(self, features: dict[str, Any]) -> tuple[int, str]:
        """
        Apply rules to features and return score and applied rule ID.
        
        Rules are applied in order; first match wins.
        
        Args:
            features: Dictionary of feature values
        
        Returns:
            (score, applied_rule_id)
        """
        for rule in self.rules:
            if self._matches(rule.conditions, features):
                return rule.score, rule.rule_id
        
        # Fallback: no rule matched
        return 0, "_no_match"
    
    def _matches(self, conditions: dict[str, Any], features: dict[str, Any]) -> bool:
        """
        Check if all conditions are satisfied by features.
        
        Explicit threshold format:
            "field": value  → field >= value (for numeric fields, default)
            "is_field": value → field == value (for boolean fields)
            "field_eq": value → field == value (for exact equality)
        
        This ensures clear, readable rule definitions aligned with Ortega (2000).
        """
        for key, threshold in conditions.items():
            # Boolean fields (is_*)
            if key.startswith("is_"):
                actual_value = features.get(key)
                if actual_value is None:
                    return False
                if actual_value != threshold:
                    return False
            # Exact equality (field_eq) - strip _eq suffix to get actual field name
            elif key.endswith("_eq"):
                field_name = key[:-3]  # Remove "_eq" suffix
                actual_value = features.get(field_name)
                if actual_value is None:
                    return False
                if actual_value != threshold:
                    return False
            # Numeric fields: use >= comparison (threshold is minimum)
            else:
                actual_value = features.get(key)
                if actual_value is None:
                    return False
                if actual_value < threshold:
                    return False
        
        return True
    
    @staticmethod
    def _get_operator(op_str: str):
        """Get operator function from string."""
        ops = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "lt": lambda a, b: a < b,
            "le": lambda a, b: a <= b,
            "gt": lambda a, b: a > b,
            "ge": lambda a, b: a >= b,
        }
        return ops.get(op_str, lambda a, b: a == b)


def create_ortega_2000_engine() -> RubricEngine:
    """
    Create the explicit Ortega (2000) EIT scoring engine.
    
    Scoring scale (based on idea_unit_coverage + meaning preservation):
    - 4: Exact repetition (0 edits)
    - 3: Meaning preserved (≥90% coverage, no content subs, ≤3 edits)
    - 2: Partial meaning (≥50% coverage, ≤2 content subs)
    - 1: Minimal meaning (>0% coverage, ≥2 tokens)
    - 0: No meaning or gibberish
    
    Word-order penalties are applied only when meaning is affected.
    Synonym handling is strictly rule-based (no ML/probabilistic methods).
    """
    rules = [
        # ─────────────────────────────────────────────────────────
        # SCORE 4: EXACT REPETITION
        # ─────────────────────────────────────────────────────────
        RubricRule(
            rule_id="R4_exact_repetition",
            description="Exact match: 0 edits, 100% coverage",
            conditions={"total_edits_eq": 0},  # Exact equality
            score=4,
        ),
        
        # ─────────────────────────────────────────────────────────
        # SCORE 3: MEANING PRESERVED
        # ─────────────────────────────────────────────────────────
        # High coverage (≥90%), no content substitutions, minor edits
        RubricRule(
            rule_id="R3_meaning_preserved_high_coverage",
            description="Meaning fully preserved: ≥90% coverage, no content subs, ≤3 edits",
            conditions={
                "idea_unit_coverage": 0.90,
                "content_subs": 0,
                "total_edits": 3,
            },
            score=3,
        ),
        
        # Good coverage (≥80%), no content subs, minimal edits
        RubricRule(
            rule_id="R3_meaning_preserved_good_coverage",
            description="Meaning preserved: ≥80% coverage, no content subs, ≤2 edits",
            conditions={
                "idea_unit_coverage": 0.80,
                "content_subs": 0,
                "total_edits": 2,
            },
            score=3,
        ),
        
        # ─────────────────────────────────────────────────────────
        # SCORE 2: PARTIAL MEANING (>50% COVERAGE)
        # ─────────────────────────────────────────────────────────
        # More than half idea units, some content loss acceptable
        RubricRule(
            rule_id="R2_partial_meaning_high",
            description="Partial meaning: ≥60% coverage, ≤2 content subs",
            conditions={
                "idea_unit_coverage": 0.60,
                "content_subs": 2,
            },
            score=2,
        ),
        
        # Moderate coverage (≥50%), limited content loss
        RubricRule(
            rule_id="R2_partial_meaning_moderate",
            description="Partial meaning: ≥50% coverage, ≤3 content subs",
            conditions={
                "idea_unit_coverage": 0.50,
                "content_subs": 3,
            },
            score=2,
        ),
        
        # ─────────────────────────────────────────────────────────
        # SCORE 1: MINIMAL MEANING (<50% COVERAGE)
        # ─────────────────────────────────────────────────────────
        # Some recognizable content but incomplete
        RubricRule(
            rule_id="R1_minimal_meaning",
            description="Minimal meaning: >0% coverage, ≥2 tokens, <50% coverage",
            conditions={
                "idea_unit_coverage": 0.01,  # Greater than 0
                "hyp_min_tokens": 2,
            },
            score=1,
        ),
        
        # ─────────────────────────────────────────────────────────
        # SCORE 0: NO MEANING / GIBBERISH
        # ─────────────────────────────────────────────────────────
        # Gibberish response (all noise)
        RubricRule(
            rule_id="R0_gibberish",
            description="Response is transcription noise (all gibberish)",
            conditions={"is_gibberish": True},
            score=0,
        ),
        
        # Empty or too short response
        RubricRule(
            rule_id="R0_empty_response",
            description="Response has fewer than 2 tokens",
            conditions={"hyp_min_tokens": 1},
            score=0,
        ),
        
        # No coverage (fallback)
        RubricRule(
            rule_id="R0_no_coverage",
            description="No meaningful content reproduced",
            conditions={},
            score=0,
        ),
    ]
    
    return RubricEngine(rules=rules, max_points=4)
