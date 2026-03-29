#!/usr/bin/env python
"""
demo_evaluation.py
==================
Demonstration of the evaluation layer with sample data.

Shows how to:
1. Score responses
2. Compare with human scores
3. Compute agreement metrics
4. Interpret results
"""

from eit_scorer.core.rubric import load_rubric
from eit_scorer.core.scoring import score_response
from eit_scorer.data.models import EITItem, EITResponse
from eit_scorer.evaluation.agreement import evaluate_agreement
from pathlib import Path


def main():
    # Load rubric
    rubric_path = Path("eit_scorer/config/default_rubric.yaml")
    rubric = load_rubric(rubric_path)
    
    # Sample test cases with human scores
    test_cases = [
        ("Quiero cortarme el pelo", "Quiero cortarme el pelo", 4, "Perfect match"),
        ("El libro está en la mesa", "El libro está en la mesa", 4, "Perfect match"),
        ("El carro lo tiene Pedro", "El carro tiene Pedro", 3, "Minor deletion"),
        ("La niña come una manzana", "La niña come manzana", 3, "Article deletion"),
        ("Voy a la escuela mañana", "Voy a la escuela", 2, "Word deletion"),
        ("Me gusta leer libros", "Me gusta leer", 2, "Word deletion"),
        ("El perro corre rápido", "El perro corre", 2, "Adverb deletion"),
        ("Tengo hambre ahora", "Tengo hambre", 2, "Adverb deletion"),
        ("Hace frío hoy", "Hace frío", 2, "Adverb deletion"),
        ("Quiero agua", "Quiero", 1, "Partial response"),
    ]
    
    print("=" * 70)
    print("SPANISH EIT SCORER - EVALUATION DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Score all responses
    human_scores = []
    auto_scores = []
    
    print("Scoring responses...")
    print()
    
    for i, (stimulus, response, human_score, description) in enumerate(test_cases, 1):
        item = EITItem(
            item_id=f"test_{i}",
            reference=stimulus,
            max_points=4,
        )
        resp = EITResponse(
            participant_id="demo",
            item_id=f"test_{i}",
            response_text=response,
        )
        
        scored = score_response(item, resp, rubric)
        
        human_scores.append(human_score)
        auto_scores.append(scored.score)
        
        match_symbol = "✓" if human_score == scored.score else "✗"
        print(f"{i:2d}. {description:20s} | Human: {human_score} | Auto: {scored.score} | {match_symbol}")
    
    print()
    print("=" * 70)
    print("EVALUATION METRICS")
    print("=" * 70)
    print()
    
    # Compute agreement metrics
    metrics = evaluate_agreement(human_scores, auto_scores)
    print(metrics.detailed_report())
    
    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print()
    
    # Provide interpretation
    if metrics.accuracy >= 85 and metrics.weighted_kappa >= 0.70 and metrics.mae < 0.5:
        print("✅ RESEARCH-VALID: System demonstrates strong agreement with human raters")
        print()
        print("The automated scoring system is suitable for:")
        print("  • Research studies")
        print("  • Large-scale assessment")
        print("  • Automated grading")
        print("  • Longitudinal tracking")
    elif metrics.accuracy >= 75 and metrics.weighted_kappa >= 0.50:
        print("◐ ACCEPTABLE: System shows reasonable agreement")
        print()
        print("Suitable for research with caveats:")
        print("  • Use with human verification")
        print("  • Report limitations in publications")
        print("  • Consider refinement of rules")
    else:
        print("✗ NEEDS IMPROVEMENT: System requires refinement")
        print()
        print("Recommendations:")
        print("  • Review rules causing disagreement")
        print("  • Adjust thresholds in rubric_engine.py")
        print("  • Collect more human scores for validation")
        print("  • Consider additional features")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
