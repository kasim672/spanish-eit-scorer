"""
tests/test_synth_pipeline.py
==============================
Tests that synthetic dataset generation is reproducible (same seed → same output)
and that the full pipeline (generate → score → eval) works end-to-end.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eit_scorer.core.rubric        import load_rubric
from eit_scorer.synthetic.stimuli  import default_stimuli_60
from eit_scorer.synthetic.generate import (
    SyntheticDatasetConfig,
    generate_synthetic_items,
    generate_synthetic_responses,
)
from eit_scorer.evaluation.metrics import (
    sentence_level_agreement, totals_by_participant, total_score_agreement
)

RUBRIC = load_rubric(Path(__file__).parent.parent / "eit_scorer/config/default_rubric.yaml")


def _serialize(responses) -> str:
    return json.dumps(
        [r.model_dump() for r in responses],
        sort_keys=True, ensure_ascii=False
    )


def test_synth_reproducible_same_seed():
    """Same seed → identical synthetic dataset."""
    cfg = SyntheticDatasetConfig(n_participants=10, seed=42, use_spacy=False)
    items = generate_synthetic_items()
    r1 = generate_synthetic_responses(items, RUBRIC, cfg)
    r2 = generate_synthetic_responses(items, RUBRIC, cfg)
    assert _serialize(r1) == _serialize(r2)


def test_synth_different_seeds_differ():
    items = generate_synthetic_items()
    cfg1 = SyntheticDatasetConfig(n_participants=5, seed=1,   use_spacy=False)
    cfg2 = SyntheticDatasetConfig(n_participants=5, seed=999, use_spacy=False)
    r1 = generate_synthetic_responses(items, RUBRIC, cfg1)
    r2 = generate_synthetic_responses(items, RUBRIC, cfg2)
    assert _serialize(r1) != _serialize(r2)


def test_correct_record_count():
    n_p   = 8
    items = generate_synthetic_items()
    cfg   = SyntheticDatasetConfig(n_participants=n_p, seed=0, use_spacy=False)
    resps = generate_synthetic_responses(items, RUBRIC, cfg)
    assert len(resps) == n_p * len(items)


def test_all_responses_have_human_scores():
    items = generate_synthetic_items()
    cfg   = SyntheticDatasetConfig(n_participants=3, seed=7, use_spacy=False)
    resps = generate_synthetic_responses(items, RUBRIC, cfg)
    for r in resps:
        assert r.human_rater_a is not None
        assert r.human_rater_b is not None


def test_human_scores_in_range():
    items = generate_synthetic_items()
    cfg   = SyntheticDatasetConfig(n_participants=5, seed=77, use_spacy=False)
    resps = generate_synthetic_responses(items, RUBRIC, cfg)
    for r in resps:
        assert 0 <= r.human_rater_a <= RUBRIC.max_points
        assert 0 <= r.human_rater_b <= RUBRIC.max_points


def test_stimuli_60_items():
    items = default_stimuli_60()
    assert len(items) == 60
    levels = {it.level for it in items}
    assert levels == {"A1","A2","B1","B2","C1","C2"}


def test_evaluation_metrics_on_synth():
    """Full pipeline: generate → score → evaluate."""
    from eit_scorer.core.scoring import score_response

    items = generate_synthetic_items()[:10]
    cfg   = SyntheticDatasetConfig(n_participants=5, seed=42, use_spacy=False)
    resps = generate_synthetic_responses(items, RUBRIC, cfg)

    y_true, y_pred = [], []
    rows = []
    items_map = {it.item_id: it for it in items}

    for resp in resps:
        item = items_map[resp.item_id]
        ss   = score_response(item, resp, RUBRIC)
        true = resp.human_rater_a
        if true is not None:
            y_true.append(float(true))
            y_pred.append(float(ss.score))
            rows.append({
                "participant_id": resp.participant_id,
                "score":          ss.score,
                "adjudicated":    resp.meta.get("adjudicated", resp.human_rater_a),
            })

    agr = sentence_level_agreement(y_true, y_pred)
    assert 0 <= agr.accuracy <= 100
    assert -1 <= agr.cohens_kappa <= 1
    assert agr.mae >= 0


def test_kappa_perfect_agreement():
    y = [4.0, 3.0, 2.0, 1.0, 0.0, 4.0, 3.0]
    agr = sentence_level_agreement(y, y)
    assert agr.accuracy == 100.0
    assert abs(agr.cohens_kappa   - 1.0) < 1e-9
    assert abs(agr.weighted_kappa - 1.0) < 1e-9
    assert agr.mae == 0.0


def test_total_score_agreement():
    pred = [22.0, 18.0, 30.0]
    true = [24.0, 17.0, 28.0]
    ta   = total_score_agreement(pred, true, within_points=10.0)
    assert ta.n_participants == 3
    assert ta.max_abs_diff == 2.0
    assert ta.pct_within_n == 100.0
    assert ta.meets_10pt_target


def test_large_gen_streaming(tmp_path):
    """LargeDatasetGenerator writes correct record count."""
    from eit_scorer.synthetic.generate import LargeDatasetGenerator
    gen = LargeDatasetGenerator(rubric=RUBRIC, seed=42,
                                use_spacy=False, chunk_size=500)
    meta = gen.generate(n_records=1000, output_dir=tmp_path, show_progress=False)
    assert meta["generation"]["n_records"] == 1000
    # Verify dataset.jsonl line count
    lines = (tmp_path / "dataset.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1000
