#!/usr/bin/env python
"""
score_excel.py
===============
Score EIT responses from Excel file.

Usage:
    python score_excel.py <input.xlsx> <output.xlsx>

Reads all sheets (except 'Info'), scores each row, and writes results.
"""

import sys
from pathlib import Path

from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse
from eit_scorer.utils.excel_io import read_excel_sheets, write_excel_scores


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


if __name__ == "__main__":
    main()
