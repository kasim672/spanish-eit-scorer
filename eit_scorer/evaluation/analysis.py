"""
eit_scorer/evaluation/analysis.py
====================================
Grouped agreement analysis — break down metrics by item or proficiency band.
Reveals where the scoring engine performs well vs. needs improvement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from eit_scorer.evaluation.metrics import SentenceAgreement, sentence_level_agreement


@dataclass
class GroupReport:
    group_key:   str
    group_value: str
    agreement:   SentenceAgreement

    def summary(self) -> str:
        return f"[{self.group_key}={self.group_value}]  {self.agreement.summary()}"


def _group_key_item(row: dict) -> str:
    return str(row.get("item_id", "unknown"))


def _group_key_band(row: dict) -> str:
    return str(row.get("meta", {}).get("band",
               row.get("participant_level",
               row.get("meta", {}).get("participant_level", "unknown"))))


def grouped_sentence_agreement(
    rows:        list[dict],
    human_field: str = "adjudicated",
    group_by:    Literal["item", "band"] = "item",
) -> list[GroupReport]:
    """
    Compute sentence-level agreement broken down by group.

    group_by:
      "item"  — one report per EIT item (reveals hard vs easy items)
      "band"  — one report per CEFR proficiency band (reveals low vs high learners)

    Returns list of GroupReport sorted by group_value.
    """
    key_fn = _group_key_item if group_by == "item" else _group_key_band
    groups: dict[str, tuple[list, list]] = {}

    for row in rows:
        gv   = key_fn(row)
        pred = row.get("score", 0)
        true = row.get(human_field, row.get("human_rater_a"))
        if true is None:
            continue
        if gv not in groups:
            groups[gv] = ([], [])
        groups[gv][0].append(float(true))
        groups[gv][1].append(float(pred))

    reports: list[GroupReport] = []
    for gv, (y_true, y_pred) in sorted(groups.items()):
        if len(y_true) < 2:
            continue
        try:
            agr = sentence_level_agreement(y_true, y_pred)
            reports.append(GroupReport(
                group_key=group_by,
                group_value=gv,
                agreement=agr,
            ))
        except Exception:
            pass

    return reports
