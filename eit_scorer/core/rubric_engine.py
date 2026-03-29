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
        
        Condition format:
            "max_field": value  → field <= value
            "min_field": value  → field >= value
            "is_field": value   → field == value
            "field_op": value   → field op value (where op is eq, ne, lt, le, gt, ge)
        """
        for key, expected_value in conditions.items():
            # Check for explicit operator suffix (eq, ne, lt, le, gt, ge)
            parts = key.rsplit("_", 1)
            op_str = parts[-1] if len(parts) > 1 and parts[-1] in {"eq", "ne", "lt", "le", "gt", "ge"} else None
            
            if op_str:
                # Explicit operator: "field_op"
                field = "_".join(parts[:-1])
                op = self._get_operator(op_str)
            else:
                # Implicit operator based on prefix
                field = key
                if key.startswith("max_"):
                    field = key[4:]  # Remove "max_" prefix
                    op = lambda a, b: a <= b
                elif key.startswith("min_"):
                    field = key[4:]  # Remove "min_" prefix
                    op = lambda a, b: a >= b
                elif key.startswith("is_"):
                    field = key[3:]  # Remove "is_" prefix
                    op = lambda a, b: a == b
                else:
                    op = lambda a, b: a == b
            
            # Get actual value from features
            actual_value = features.get(field)
            if actual_value is None:
                return False
            
            # Check condition
            if not op(actual_value, expected_value):
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
    Create the default Ortega (2000) EIT scoring engine.
    
    Scoring scale:
    - 0: No meaningful output, garbled, minimal repetition
    - 1: Less than half idea units, incomplete meaning
    - 2: More than half idea units, inexact meaning
    - 3: Meaning preserved, grammatical errors acceptable
    - 4: Exact repetition
    """
    rules = [
        # Score 0: Gibberish
        RubricRule(
            rule_id="R0_gibberish",
            description="Response is transcription noise",
            conditions={"is_gibberish": True},
            score=0,
        ),
        
        # Score 0: Empty or too short
        RubricRule(
            rule_id="R0_empty_or_too_short",
            description="Response has fewer than 2 tokens",
            conditions={"hyp_min_tokens_lt": 2},
            score=0,
        ),
        
        # Score 4: Perfect repetition
        RubricRule(
            rule_id="R4_perfect",
            description="No edits — exact repetition",
            conditions={"max_total_edits": 0},
            score=4,
        ),
        
        # Score 3: Meaning preserved
        RubricRule(
            rule_id="R3_meaning_preserved",
            description="Meaning fully preserved, minor form errors",
            conditions={
                "max_total_edits": 3,
                "max_content_subs": 0,
                "min_idea_unit_coverage": 0.80,
            },
            score=3,
        ),
        
        # Score 3: Reordered but complete
        RubricRule(
            rule_id="R3_reordered_complete",
            description="Content complete but reordered",
            conditions={
                "min_idea_unit_coverage": 0.90,
                "max_content_subs": 0,
                "max_word_order_penalty": 0.50,
            },
            score=3,
        ),
        
        # Score 2: More than half idea units
        RubricRule(
            rule_id="R2_more_than_half_iu",
            description="More than half idea units reproduced",
            conditions={
                "min_idea_unit_coverage": 0.50,
                "max_content_subs": 2,
                "min_length_ratio": 0.40,
            },
            score=2,
        ),
        
        # Score 2: Good overlap but some loss
        RubricRule(
            rule_id="R2_good_overlap_some_loss",
            description="Good token overlap but content loss",
            conditions={
                "min_token_overlap_ratio": 0.55,
                "max_content_subs": 2,
                "min_length_ratio": 0.35,
            },
            score=2,
        ),
        
        # Score 1: Less than half idea units
        RubricRule(
            rule_id="R1_less_than_half_iu",
            description="Less than half idea units reproduced",
            conditions={
                "min_idea_unit_coverage": 0.15,
                "min_content_overlap": 0.15,
                "hyp_min_tokens_ge": 2,
            },
            score=1,
        ),
        
        # Score 1: Some overlap but short
        RubricRule(
            rule_id="R1_some_overlap_short",
            description="Some recognizable content but incomplete",
            conditions={
                "min_token_overlap_ratio": 0.20,
                "hyp_min_tokens_ge": 2,
            },
            score=1,
        ),
        
        # Score 0: Catchall
        RubricRule(
            rule_id="R0_other",
            description="No prior rule matched",
            conditions={},
            score=0,
        ),
    ]
    
    return RubricEngine(rules=rules, max_points=4)
