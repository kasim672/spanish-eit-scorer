"""eit_scorer/utils/io.py — File loading helpers."""
from __future__ import annotations
import json
from pathlib import Path

from eit_scorer.data.models  import EITItem, EITResponse
from eit_scorer.utils.jsonl  import read_jsonl


def load_items_json(path: str | Path) -> dict[str, EITItem]:
    """Load items.json → {item_id: EITItem}."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", data) if isinstance(data, dict) else data
    return {it["item_id"]: EITItem(**it) for it in items}


def load_responses_jsonl(path: str | Path) -> list[EITResponse]:
    """Load dataset.jsonl → list[EITResponse]."""
    results = []
    for row in read_jsonl(path):
        # Accept both flat and nested keys
        results.append(EITResponse(
            participant_id=row.get("participant_id", "unknown"),
            item_id=row.get("item_id", ""),
            response_text=row.get("response_text", row.get("response", "")),
            human_rater_a=row.get("human_rater_a"),
            human_rater_b=row.get("human_rater_b"),
            meta=row.get("meta", {}),
        ))
    return results
