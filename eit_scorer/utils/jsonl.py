"""eit_scorer/utils/jsonl.py — JSONL read/write helpers."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator


def read_jsonl(path: str | Path) -> Iterator[dict]:
    """Yield one dict per non-empty line in a JSONL file."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: str | Path, rows: list[dict]) -> None:
    """Write dicts as JSONL. sort_keys=True ensures deterministic output."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
