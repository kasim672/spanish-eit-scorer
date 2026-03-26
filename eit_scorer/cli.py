"""
eit_scorer/cli.py
===================
Command-line interface: eit-score

Sub-commands:
  synth   — generate a synthetic dataset (small, for testing/dev)
  score   — score a dataset.jsonl against items.json
  eval    — compute agreement metrics vs human raters

Usage:
  eit-score synth  --out data/synth  --participants 200
  eit-score score  --items data/synth/items.json  --dataset data/synth/dataset.jsonl  --out data/synth/scored.jsonl
  eit-score eval   --scored data/synth/scored.jsonl  --human adjudicated  --group band
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Default rubric path ───────────────────────────────────────
def _default_rubric_path() -> Path:
    return Path(__file__).parent / "config" / "default_rubric.yaml"


# ─────────────────────────────────────────────────────────────
# CMD: synth
# ─────────────────────────────────────────────────────────────
def cmd_synth(args) -> int:
    from eit_scorer.core.rubric          import load_rubric
    from eit_scorer.synthetic.stimuli    import default_stimuli_60
    from eit_scorer.synthetic.generate   import (
        SyntheticDatasetConfig,
        generate_synthetic_items,
        generate_synthetic_responses,
        write_synthetic_dataset,
    )

    rubric = load_rubric(args.rubric or _default_rubric_path())
    items  = generate_synthetic_items()

    cfg = SyntheticDatasetConfig(
        n_participants=args.participants,
        seed=args.seed,
        use_spacy=not args.no_spacy,
    )

    print(f"Generating {args.participants} participants × {len(items)} items "
          f"= {args.participants * len(items):,} responses …")

    responses = generate_synthetic_responses(items, rubric, cfg)
    write_synthetic_dataset(args.out, items, responses)

    print(f"✓  Written to {args.out}/")
    print(f"   items.json   : {len(items)} items")
    print(f"   dataset.jsonl: {len(responses)} responses")
    return 0


# ─────────────────────────────────────────────────────────────
# CMD: score
# ─────────────────────────────────────────────────────────────
def cmd_score(args) -> int:
    from eit_scorer.core.rubric    import load_rubric
    from eit_scorer.core.scoring   import score_response
    from eit_scorer.utils.io       import load_items_json, load_responses_jsonl
    from eit_scorer.utils.jsonl    import write_jsonl

    rubric    = load_rubric(args.rubric or _default_rubric_path())
    items_map = load_items_json(args.items)
    responses = load_responses_jsonl(args.dataset)

    print(f"Scoring {len(responses):,} responses against {len(items_map)} items …")

    scored_rows = []
    missing = 0
    for resp in responses:
        item = items_map.get(resp.item_id)
        if item is None:
            logger.warning(f"Item not found: {resp.item_id} — skipping")
            missing += 1
            continue
        ss = score_response(item, resp, rubric)
        d  = ss.to_jsonl_dict()
        # Flatten trace for readability in JSONL
        d["total_edits"]       = ss.trace.total_edits
        d["content_subs"]      = ss.trace.content_subs
        d["overlap_ratio"]     = round(ss.trace.overlap_ratio, 4)
        d["rule_fired"]        = ss.trace.applied_rule_ids[0] if ss.trace.applied_rule_ids else ""
        d["adjudicated"]       = ss.adjudicated
        scored_rows.append(d)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_path, scored_rows)

    print(f"✓  {len(scored_rows):,} sentences scored → {out_path}")
    if missing:
        print(f"   ⚠ {missing} responses skipped (item_id not found)")
    return 0


# ─────────────────────────────────────────────────────────────
# CMD: eval
# ─────────────────────────────────────────────────────────────
def cmd_eval(args) -> int:
    from eit_scorer.evaluation.metrics  import (
        sentence_level_agreement, totals_by_participant, total_score_agreement
    )
    from eit_scorer.evaluation.analysis import grouped_sentence_agreement
    from eit_scorer.utils.jsonl         import read_jsonl

    rows = list(read_jsonl(args.scored))
    if not rows:
        print("ERROR: scored file is empty")
        return 1

    human_field = args.human   # e.g. "adjudicated" or "human_rater_a"

    # Build y_true / y_pred
    y_true, y_pred = [], []
    for row in rows:
        true = row.get(human_field, row.get("human_rater_a"))
        if true is None:
            continue
        pred = row.get("score", 0)
        y_true.append(float(true))
        y_pred.append(float(pred))

    if not y_true:
        print(f"ERROR: no rows have field '{human_field}'")
        return 1

    # ── Sentence-level ────────────────────────────────────────
    sent_agr = sentence_level_agreement(y_true, y_pred)
    print("\n" + "=" * 60)
    print("  EIT SCORER — EVALUATION REPORT")
    print("=" * 60)
    print(f"\n── Sentence-level Agreement ({len(y_true):,} sentences) ──")
    print(f"  Accuracy (exact match) : {sent_agr.accuracy:.1f}%"
          f"  {'✓' if sent_agr.meets_90pct_target else '✗'}  [target ≥90%]")
    print(f"  Cohen's κ (unweighted) : {sent_agr.cohens_kappa:.4f}")
    print(f"  Weighted κ (quadratic) : {sent_agr.weighted_kappa:.4f}"
          f"  [{sent_agr.kappa_label}]")
    print(f"  Mean Absolute Error    : {sent_agr.mae:.4f} pts")

    # ── Participant totals ────────────────────────────────────
    try:
        pred_totals, true_totals = totals_by_participant(
            rows, true_field=human_field, pred_field="score"
        )
        if pred_totals:
            tot_agr = total_score_agreement(
                pred_totals, true_totals,
                within_points=args.within_points
            )
            print(f"\n── Participant Total Score Agreement ({tot_agr.n_participants} participants) ──")
            print(f"  MAE (total score)      : {tot_agr.mae:.2f} pts")
            print(f"  Max absolute diff      : {tot_agr.max_abs_diff:.1f} pts"
                  f"  {'✓' if tot_agr.meets_10pt_target else '✗'}  [target <10pt]")
            print(f"  Within {args.within_points:.0f} pts         : {tot_agr.pct_within_n:.1f}%")
    except Exception as e:
        logger.warning(f"Could not compute total agreement: {e}")

    # ── Overall status ────────────────────────────────────────
    print("\n── Overall Status ──")
    meets = sent_agr.meets_90pct_target
    print(f"  {'✓ TARGETS MET' if meets else '✗ TARGETS NOT YET MET'}")
    if not meets:
        gap = 90.0 - sent_agr.accuracy
        print(f"  Accuracy gap: {gap:.1f}pp below 90% target")
        print(f"  Recommendation: review disagreements by error type (--group band)")

    # ── Grouped analysis ─────────────────────────────────────
    if args.group:
        reports = grouped_sentence_agreement(rows, human_field=human_field, group_by=args.group)
        print(f"\n── Agreement by {args.group.upper()} ──")
        for r in reports:
            print(f"  {r.summary()}")

    print("=" * 60 + "\n")
    return 0


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eit-score",
        description="Spanish EIT Automated Scorer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quick start:
  eit-score synth  --out data/synth --participants 100
  eit-score score  --items data/synth/items.json \\
                   --dataset data/synth/dataset.jsonl \\
                   --out data/synth/scored.jsonl
  eit-score eval   --scored data/synth/scored.jsonl
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── synth ──
    p_synth = sub.add_parser("synth", help="Generate synthetic dataset")
    p_synth.add_argument("--out",          type=str,  default="data/synth_dataset")
    p_synth.add_argument("--participants", type=int,  default=100)
    p_synth.add_argument("--seed",         type=int,  default=42)
    p_synth.add_argument("--rubric",       type=str,  default=None)
    p_synth.add_argument("--no-spacy",     action="store_true")

    # ── score ──
    p_score = sub.add_parser("score", help="Score a dataset")
    p_score.add_argument("--items",   required=True, type=str)
    p_score.add_argument("--dataset", required=True, type=str)
    p_score.add_argument("--out",     default="data/scored.jsonl", type=str)
    p_score.add_argument("--rubric",  type=str, default=None)

    # ── eval ──
    p_eval = sub.add_parser("eval", help="Evaluate against human raters")
    p_eval.add_argument("--scored",       required=True, type=str)
    p_eval.add_argument("--human",        default="adjudicated", type=str,
                        help="Field name for human score (default: adjudicated)")
    p_eval.add_argument("--group",        default=None, choices=["item","band"],
                        help="Group agreement by item or proficiency band")
    p_eval.add_argument("--within-points",type=float, default=10.0,
                        help="Threshold for participant total score comparison")

    return parser


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parser = build_parser()
    args   = parser.parse_args()

    dispatch = {"synth": cmd_synth, "score": cmd_score, "eval": cmd_eval}
    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(fn(args))


if __name__ == "__main__":
    main()
