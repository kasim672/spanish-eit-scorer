#!/usr/bin/env python
"""
databuilder.py
==============
Generate synthetic EIT datasets with controlled error injection.

This is an OPTIONAL feature that uses spaCy for advanced NLP capabilities.
The core scoring system does NOT require spaCy.

Usage:
    python scripts/databuilder.py --output data/synth/dataset.jsonl --count 100

Features:
    - Generate synthetic responses with controlled errors
    - Inject deletions, substitutions, false starts, pauses
    - Assign simulated human scores based on error severity
    - Output in JSONL format for evaluation
"""

import argparse
from pathlib import Path

from eit_scorer.synthetic.generate import generate_dataset


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic EIT dataset with controlled errors"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/synth/dataset.jsonl",
        help="Output JSONL file path (default: data/synth/dataset.jsonl)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of responses to generate (default: 100)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--stimuli",
        type=str,
        default=None,
        help="Path to stimuli JSON file (optional, uses built-in if not provided)",
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("SPANISH EIT DATABUILDER - SYNTHETIC DATASET GENERATION")
    print("=" * 70)
    print()
    print(f"Output: {output_path}")
    print(f"Count: {args.count}")
    print(f"Seed: {args.seed}")
    print()
    
    # Generate dataset
    print("Generating synthetic responses...")
    dataset = generate_dataset(
        n=args.count,
        seed=args.seed,
        output_path=str(output_path),
    )
    
    print()
    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"✅ Generated {len(dataset)} responses")
    print(f"✅ Saved to: {output_path}")
    print()
    
    # Show score distribution
    scores = [r.get("human_score", 0) for r in dataset]
    score_dist = {s: scores.count(s) for s in range(5)}
    
    print("Score Distribution:")
    for score in range(5):
        count = score_dist.get(score, 0)
        pct = count / len(dataset) * 100 if dataset else 0
        bar = "█" * int(pct / 2)
        print(f"  {score}: {count:3d} ({pct:5.1f}%) {bar}")
    
    print()
    print("=" * 70)
    print()
    print("Next steps:")
    print(f"  1. Review generated data: cat {output_path}")
    print(f"  2. Score the dataset: python scripts/score_excel.py ...")
    print(f"  3. Evaluate agreement: Check results/summary_metrics.json")
    print()


if __name__ == "__main__":
    main()
