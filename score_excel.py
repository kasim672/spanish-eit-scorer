#!/usr/bin/env python
"""
score_excel.py
===============
Score EIT responses from Excel file with evaluation metrics.

Usage:
    python score_excel.py <input.xlsx> <output.xlsx>

Reads all sheets (except 'Info'), scores each row, computes agreement metrics
if human scores are available, and writes results.
"""

import sys
import json
from pathlib import Path

from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse
from eit_scorer.utils.excel_io import read_excel_sheets, write_excel_scores
from eit_scorer.evaluation.agreement import (
    evaluate_agreement,
    interpret_accuracy,
    interpret_kappa,
    interpret_mae,
)


def main():
    if len(sys.argv) < 3:
        print("Usage: python score_excel.py <input.xlsx> <output.xlsx>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Load rubric
    rubric_path = Path(__file__).parent / "eit_scorer/config/default_rubric.yaml"
    rubric = load_rubric(rubric_path)
    print(f"Loaded rubric: {rubric.summary()}")
    
    # Read Excel sheets
    print(f"Reading Excel file: {input_path}")
    sheets_data = read_excel_sheets(input_path)
    print(f"Found {len(sheets_data)} sheets to process")
    
    # Score each sheet
    scores_by_sheet: dict[str, list[int]] = {}
    total_scored = 0
    
    # For evaluation (if human scores available)
    all_human_scores = []
    all_auto_scores = []
    
    for sheet_name, rows in sheets_data.items():
        print(f"\nProcessing sheet: {sheet_name} ({len(rows)} rows)")
        scores = []
        
        for i, row in enumerate(rows):
            # Create item and response
            item = EITItem(
                item_id=str(row.sentence_id),
                reference=row.stimulus,
                max_points=4,
            )
            resp = EITResponse(
                participant_id=sheet_name,
                item_id=str(row.sentence_id),
                response_text=row.transcription,
            )
            
            # Score
            try:
                scored = score_response(item, resp, rubric)
                scores.append(scored.score)
                all_auto_scores.append(scored.score)
                
                # Extract human score if available
                if row.score is not None:
                    all_human_scores.append(int(row.score))
                
                total_scored += 1
                
                if (i + 1) % 100 == 0:
                    print(f"  Scored {i + 1}/{len(rows)} rows...")
            except Exception as e:
                print(f"  Error scoring row {i + 1}: {e}")
                scores.append(0)
        
        scores_by_sheet[sheet_name] = scores
        print(f"  Completed: {len(scores)} scores")
    
    # Write results
    print(f"\nWriting results to: {output_path}")
    write_excel_scores(input_path, output_path, scores_by_sheet)
    print(f"Successfully scored {total_scored} responses")
    print(f"Output saved to: {output_path}")
    
    # Evaluate agreement if human scores are available
    if all_human_scores and all_auto_scores:
        print("\n" + "="*60)
        print("EVALUATION METRICS")
        print("="*60)
        metrics = evaluate_agreement(all_human_scores, all_auto_scores)
        print(metrics.detailed_report())
        
        # Save metrics to JSON
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        metrics_path = results_dir / "summary_metrics.json"
        metrics_dict = {
            "n_samples": metrics.n_samples,
            "accuracy": round(metrics.accuracy, 2),
            "cohens_kappa": round(metrics.cohens_kappa, 3),
            "weighted_kappa": round(metrics.weighted_kappa, 3),
            "mae": round(metrics.mae, 3),
            "interpretation": {
                "accuracy": interpret_accuracy(metrics.accuracy),
                "kappa": interpret_kappa(metrics.cohens_kappa),
                "weighted_kappa": interpret_kappa(metrics.weighted_kappa),
                "mae": interpret_mae(metrics.mae),
            }
        }
        
        with open(metrics_path, "w") as f:
            json.dump(metrics_dict, f, indent=2)
        
        print(f"\n✅ Evaluation metrics saved to: {metrics_path}")
    else:
        print("\nNote: No human scores available for evaluation")


if __name__ == "__main__":
    main()

