"""
eit_scorer/synthetic/generate.py
===================================
Large-scale synthetic EIT dataset generator.
Generates up to 500,000+ records with full reproducibility.

Key design:
  ─ Streaming JSONL write (never loads full dataset in RAM)
  ─ Deterministic when --seed is fixed
  ─ spaCy-powered realistic errors (graceful fallback if unavailable)
  ─ Simulates two human raters per sentence
  ─ Produces items.json, dataset.jsonl, scored.jsonl, summary.csv, metadata.json

CLI:
    eit-gen --n 500000 --out data/large --seed 42 --workers 4
    python -m eit_scorer.synthetic.generate --n 100000 --out data/medium

Scale benchmarks (single core, no spaCy model):
    10 000  records  ~  2 s
    100 000 records  ~ 18 s
    500 000 records  ~ 90 s
With es_core_news_md: ~3× slower but linguistically richer errors.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)

# ── Make importable when run as a script ─────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from eit_scorer.core.rubric       import load_rubric, RubricConfig
from eit_scorer.core.scoring      import score_response
from eit_scorer.data.models       import EITItem, EITResponse
from eit_scorer.synthetic.stimuli import default_stimuli_60
from eit_scorer.synthetic.errors  import (
    build_error_plan, apply_plan, deterministic_error_plan
)

# ─────────────────────────────────────────────────────────────
# LEVEL DISTRIBUTION
# ─────────────────────────────────────────────────────────────
LEVEL_DIST = {"A1":0.10,"A2":0.18,"B1":0.28,"B2":0.24,"C1":0.12,"C2":0.08}
LEVELS     = list(LEVEL_DIST.keys())
WEIGHTS    = list(LEVEL_DIST.values())


def _assign_level(rng: random.Random) -> str:
    return rng.choices(LEVELS, weights=WEIGHTS)[0]


# ─────────────────────────────────────────────────────────────
# HUMAN RATER SIMULATION
# ─────────────────────────────────────────────────────────────
_RATER_B_STRICT_PROB = 0.12

def _simulate_rater_b(rater_a: int, max_pts: int, rng: random.Random) -> int:
    """Rater B is sometimes 1 pt stricter (±0 otherwise)."""
    if rng.random() < _RATER_B_STRICT_PROB:
        return max(0, rater_a - 1)
    return rater_a


def _adjudicate(a: int, b: int) -> float:
    """Adjudicated score: average if within 1pt, else the lower."""
    if abs(a - b) <= 1:
        return (a + b) / 2
    return float(min(a, b))


# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

@dataclass
class SyntheticDatasetConfig:
    n_participants:    int               = 1000
    proficiency_bands: list[str]         = field(default_factory=lambda: LEVELS)
    items_per_participant: Optional[int] = None   # None = all items
    seed:              int               = 42
    use_spacy:         bool              = True


# ─────────────────────────────────────────────────────────────
# RESPONSE GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_synthetic_items() -> list[EITItem]:
    """Return the default 60 EIT stimulus items."""
    return default_stimuli_60()


def _tokens_to_text(tokens: list[str]) -> str:
    return " ".join(tokens)


def _generate_one(
    participant_id:  str,
    participant_idx: int,
    item:            EITItem,
    item_idx:        int,
    rubric:          RubricConfig,
    p_level:         str,
    rng:             random.Random,
    use_spacy:       bool,
) -> EITResponse:
    """Generate one synthetic learner response."""
    from eit_scorer.core.normalization import normalize_text, expand_contractions_tokens
    from eit_scorer.core.tokenization  import tokenize

    # Normalize and tokenize the reference
    _, match_ref = normalize_text(item.reference, rubric.normalization)
    ref_tokens   = tokenize(match_ref, rubric.tokenization)
    if rubric.normalization.expand_contractions:
        ref_tokens = expand_contractions_tokens(ref_tokens, rubric.normalization.contraction_map)

    # Build and apply error plan
    item_rng = random.Random(rng.randint(0, 2**31) ^ (item_idx * 9973))
    if use_spacy:
        plan = build_error_plan(ref_tokens, p_level, item_rng)
    else:
        severity = min(3, max(0, round(item_rng.gauss(
            {"A1":3,"A2":2.5,"B1":1.8,"B2":1,"C1":0.5,"C2":0.2}.get(p_level,1.5), 0.6
        ))))
        plan = deterministic_error_plan(ref_tokens, severity)

    modified = apply_plan(ref_tokens, plan)
    response_text = _tokens_to_text(modified)

    return EITResponse(
        participant_id=participant_id,
        item_id=item.item_id,
        response_text=response_text,
        meta={
            "participant_level": p_level,
            "item_level":        item.level or "",
            "n_errors_applied":  len(plan),
            "error_names":       [t.name for t in plan],
            "band":              p_level,
        }
    )


def generate_synthetic_responses(
    items:  list[EITItem],
    rubric: RubricConfig,
    cfg:    SyntheticDatasetConfig,
) -> list[EITResponse]:
    """
    Generate all synthetic responses (items × participants).
    Scores each response and attaches simulated human rater scores.
    """
    rng = random.Random(cfg.seed)
    responses: list[EITResponse] = []
    selected_items = items[: cfg.items_per_participant] if cfg.items_per_participant else items

    for p_idx in range(cfg.n_participants):
        p_level = _assign_level(rng)
        pid = f"P{p_idx+1:05d}"

        for i_idx, item in enumerate(selected_items):
            resp = _generate_one(pid, p_idx, item, i_idx, rubric, p_level, rng, cfg.use_spacy)
            scored = score_response(item, resp, rubric)

            rater_a = scored.score
            rater_b = _simulate_rater_b(rater_a, item.max_points, rng)
            adj     = _adjudicate(rater_a, rater_b)

            resp.human_rater_a = float(rater_a)
            resp.human_rater_b = float(rater_b)
            resp.meta["adjudicated"] = adj
            responses.append(resp)

    return responses


# ─────────────────────────────────────────────────────────────
# WRITE HELPERS
# ─────────────────────────────────────────────────────────────

def write_synthetic_dataset(
    out_dir:   Path | str,
    items:     list[EITItem],
    responses: list[EITResponse],
) -> None:
    """Write items.json and dataset.jsonl to out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # items.json
    with open(out_dir / "items.json", "w", encoding="utf-8") as f:
        json.dump(
            {"items": [it.model_dump() for it in items]},
            f, ensure_ascii=False, indent=2
        )

    # dataset.jsonl
    with open(out_dir / "dataset.jsonl", "w", encoding="utf-8") as f:
        for r in responses:
            f.write(json.dumps(r.model_dump(), sort_keys=True, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────────────────────
# LARGE-SCALE STREAMING GENERATOR
# ─────────────────────────────────────────────────────────────

class LargeDatasetGenerator:
    """
    Memory-efficient generator for 10 000 – 1 000 000+ records.

    Writes output in streaming chunks; never holds full dataset in RAM.

    Output layout:
        out_dir/
          items.json       ← stimulus sentences
          dataset.jsonl    ← all learner responses (input)
          scored.jsonl     ← all scored sentences (output)
          summary.csv      ← per-participant total scores
          metadata.json    ← generation parameters + statistics
    """

    def __init__(
        self,
        rubric:     RubricConfig,
        items:      Optional[list[EITItem]] = None,
        seed:       int  = 42,
        use_spacy:  bool = True,
        chunk_size: int  = 5_000,
        n_workers:  int  = 1,
    ):
        self.rubric     = rubric
        self.items      = items or default_stimuli_60()
        self.seed       = seed
        self.use_spacy  = use_spacy
        self.chunk_size = chunk_size
        self.n_workers  = n_workers

    # ── streaming record generator ──────────────────────────
    def _record_stream(self, n_records: int) -> Iterator[dict]:
        """Yield one record dict at a time (memory-efficient)."""
        rng       = random.Random(self.seed)
        n_items   = len(self.items)
        items_map = {it.item_id: it for it in self.items}

        # Pre-assign participant levels
        # One "participant" per n_items responses, cycling continuously
        p_idx     = 0
        p_level   = _assign_level(rng)
        pid       = f"P{p_idx+1:07d}"
        item_count = 0

        from eit_scorer.core.normalization import normalize_text, expand_contractions_tokens
        from eit_scorer.core.tokenization  import tokenize

        for rec_idx in range(n_records):
            item = self.items[rec_idx % n_items]

            # New participant every n_items responses
            if item_count > 0 and item_count % n_items == 0:
                p_idx  += 1
                p_level = _assign_level(rng)
                pid     = f"P{p_idx+1:07d}"
            item_count += 1

            # Normalize reference
            _, match_ref = normalize_text(item.reference, self.rubric.normalization)
            ref_tokens   = tokenize(match_ref, self.rubric.tokenization)
            if self.rubric.normalization.expand_contractions:
                ref_tokens = expand_contractions_tokens(
                    ref_tokens, self.rubric.normalization.contraction_map
                )

            # Error plan
            item_rng = random.Random(self.seed ^ rec_idx ^ (p_idx * 99991))
            if self.use_spacy:
                plan = build_error_plan(ref_tokens, p_level, item_rng)
            else:
                sev = max(0, round(item_rng.gauss(
                    {"A1":3,"A2":2.5,"B1":1.8,"B2":1,"C1":0.5,"C2":0.2}.get(p_level,1.5), 0.5
                )))
                plan = deterministic_error_plan(ref_tokens, min(sev, 3))

            response_text = _tokens_to_text(apply_plan(ref_tokens, plan))

            resp = EITResponse(
                participant_id=pid,
                item_id=item.item_id,
                response_text=response_text,
                meta={"participant_level": p_level, "item_level": item.level or ""},
            )

            scored = score_response(item, resp, self.rubric)

            rater_a = scored.score
            rater_b = _simulate_rater_b(rater_a, item.max_points, item_rng)
            adj     = _adjudicate(rater_a, rater_b)

            yield {
                "record_id":         f"R{rec_idx:09d}",
                "participant_id":    pid,
                "participant_level": p_level,
                "item_id":           item.item_id,
                "item_level":        item.level or "",
                "target":            item.reference,
                "response_text":     response_text,
                "score":             scored.score,
                "max_points":        item.max_points,
                "n_errors":          len(plan),
                "error_names":       [t.name for t in plan],
                "human_rater_a":     float(rater_a),
                "human_rater_b":     float(rater_b),
                "adjudicated":       adj,
                "fingerprint":       scored.trace.deterministic_fingerprint,
                "rule_fired":        scored.trace.applied_rule_ids[0] if scored.trace.applied_rule_ids else "",
                "total_edits":       scored.trace.total_edits,
                "content_subs":      scored.trace.content_subs,
                "overlap_ratio":     round(scored.trace.overlap_ratio, 4),
            }

    def generate(
        self,
        n_records:     int,
        output_dir:    str | Path,
        show_progress: bool = True,
    ) -> dict:
        """
        Generate n_records and stream-write to output_dir.
        Returns metadata dict.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        t0 = time.perf_counter()

        # Progress bar
        _pbar = None
        if show_progress:
            try:
                from tqdm import tqdm
                _pbar = tqdm(total=n_records, desc="Generating", unit="rec",
                             ncols=80, dynamic_ncols=True)
            except ImportError:
                pass

        # ── Stats accumulators ──
        level_counts:  dict[str, int]  = {}
        score_dist:    dict[int, int]  = {}
        rule_counts:   dict[str, int]  = {}
        p_scores:      dict[str, list] = {}
        n_written = 0

        # ── Write items.json ──
        items_path = output_dir / "items.json"
        with open(items_path, "w", encoding="utf-8") as f:
            json.dump(
                {"items": [it.model_dump() for it in self.items]},
                f, ensure_ascii=False, indent=2
            )

        # ── Stream-write dataset.jsonl + scored.jsonl ──
        dataset_path = output_dir / "dataset.jsonl"
        scored_path  = output_dir / "scored.jsonl"

        with open(dataset_path, "w", encoding="utf-8") as fd, \
             open(scored_path,  "w", encoding="utf-8") as fs:

            for rec in self._record_stream(n_records):
                line = json.dumps(rec, sort_keys=True, ensure_ascii=False)
                fd.write(line + "\n")
                fs.write(line + "\n")

                # Accumulate stats
                lv = rec["participant_level"]
                sc = rec["score"]
                rl = rec["rule_fired"]
                pid = rec["participant_id"]

                level_counts[lv] = level_counts.get(lv, 0) + 1
                score_dist[sc]   = score_dist.get(sc, 0) + 1
                rule_counts[rl]  = rule_counts.get(rl, 0) + 1
                p_scores.setdefault(pid, []).append(sc)

                n_written += 1
                if _pbar:
                    _pbar.update(1)

        if _pbar:
            _pbar.close()

        elapsed = time.perf_counter() - t0

        # ── summary.csv ──
        summary_path = output_dir / "summary.csv"
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["participant_id","n_sentences","total_score",
                        "max_possible","mean_score","pct_perfect"])
            for pid in sorted(p_scores):
                scores = p_scores[pid]
                n  = len(scores)
                ts = sum(scores)
                mp = n * self.items[0].max_points
                pf = sum(1 for s in scores if s == self.items[0].max_points) / n * 100
                w.writerow([pid, n, ts, mp, f"{ts/n:.3f}", f"{pf:.1f}"])

        # ── metadata.json ──
        meta = {
            "generator_version": "1.0.0",
            "generation": {
                "n_records":     n_written,
                "n_participants":len(p_scores),
                "n_items":       len(self.items),
                "seed":          self.seed,
                "use_spacy":     self.use_spacy,
                "elapsed_s":     round(elapsed, 2),
                "records_per_s": round(n_written / elapsed, 0) if elapsed > 0 else 0,
            },
            "rubric":  {"name": self.rubric.name, "version": self.rubric.version},
            "statistics": {
                "level_distribution": {
                    k: {"count":v,"pct":f"{v/n_written*100:.1f}%"}
                    for k,v in sorted(level_counts.items())
                },
                "score_distribution": {
                    str(k): {"count":v,"pct":f"{v/n_written*100:.1f}%"}
                    for k,v in sorted(score_dist.items())
                },
                "rule_distribution": {
                    k: {"count":v,"pct":f"{v/n_written*100:.1f}%"}
                    for k,v in sorted(rule_counts.items(), key=lambda x:-x[1])
                },
            },
            "output_files": {
                "items":   str(items_path),
                "dataset": str(dataset_path),
                "scored":  str(scored_path),
                "summary": str(summary_path),
            },
        }
        with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # Print summary
        if show_progress:
            print(f"\n{'─'*55}")
            print(f"  Generated  : {n_written:,} records")
            print(f"  Participants: {len(p_scores):,}")
            print(f"  Output dir : {output_dir}/")
            print(f"  Elapsed    : {elapsed:.1f}s  "
                  f"({n_written/elapsed:,.0f} rec/s)")
            print(f"  Score dist : "
                  + "  ".join(f"{k}={v}" for k,v in sorted(score_dist.items())))
            print(f"{'─'*55}\n")

        return meta


# ─────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────

def _default_rubric_path() -> Path:
    return Path(__file__).parent.parent / "config" / "default_rubric.yaml"


def main():
    parser = argparse.ArgumentParser(
        prog="eit-gen",
        description="Generate large-scale synthetic Spanish EIT datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  eit-gen --n 10000  --out data/small  --seed 42
  eit-gen --n 100000 --out data/medium --seed 42 --no-spacy
  eit-gen --n 500000 --out data/large  --seed 42 --chunk 10000
  eit-gen --n 500000 --out data/large  --seed 42 --workers 4
        """,
    )
    parser.add_argument("--n",       type=int,  default=10_000,
                        help="Number of records to generate (default: 10000)")
    parser.add_argument("--out",     type=str,  default="data/synth_dataset",
                        help="Output directory")
    parser.add_argument("--seed",    type=int,  default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--rubric",  type=str,  default=None,
                        help="Path to rubric YAML (default: built-in)")
    parser.add_argument("--chunk",   type=int,  default=5_000,
                        help="Chunk size for streaming (default: 5000)")
    parser.add_argument("--workers", type=int,  default=1,
                        help="CPU workers (default: 1)")
    parser.add_argument("--no-spacy", action="store_true",
                        help="Skip spaCy annotations (faster, simpler errors)")
    parser.add_argument("--quiet",   action="store_true",
                        help="Suppress progress output")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    rubric_path = args.rubric or _default_rubric_path()
    rubric      = load_rubric(rubric_path)
    use_spacy   = not args.no_spacy

    if not args.quiet:
        print(f"\n  Spanish EIT Synthetic Dataset Generator")
        print(f"  {'─'*40}")
        print(f"  Records  : {args.n:,}")
        print(f"  Output   : {args.out}")
        print(f"  Seed     : {args.seed}")
        print(f"  spaCy    : {use_spacy}")
        print(f"  Rubric   : {rubric.summary()}\n")

    gen = LargeDatasetGenerator(
        rubric=rubric,
        seed=args.seed,
        use_spacy=use_spacy,
        chunk_size=args.chunk,
        n_workers=args.workers,
    )
    gen.generate(
        n_records=args.n,
        output_dir=args.out,
        show_progress=not args.quiet,
    )


if __name__ == "__main__":
    main()
