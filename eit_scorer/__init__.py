"""
Spanish EIT Automated Scorer
==============================
Deterministic, rubric-driven automated scoring for the
Spanish Elicited Imitation Task (EIT).

Quick start:
    from eit_scorer.core.rubric  import load_rubric
    from eit_scorer.core.scoring import score_response
    from eit_scorer.data.models  import EITItem, EITResponse

    rubric = load_rubric("eit_scorer/config/default_rubric.yaml")
    item   = EITItem(item_id="s01", reference="El niño come una manzana", max_points=4)
    resp   = EITResponse(participant_id="P001", item_id="s01",
                         response_text="El niño come")
    result = score_response(item, resp, rubric)
    print(result.score)           # 2
    print(result.trace.audit())   # full decision log
"""

__version__ = "1.0.0"
__author__  = "Spanish EIT Scorer Project"
