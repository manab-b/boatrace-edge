from datetime import datetime, timezone
from decimal import Decimal

from boatrace_edge.dataset import temporal_holdout
from boatrace_edge.evaluation import evaluate_lane_baseline
from boatrace_edge.probability import RaceOutcome


def race_rows(race_id: str, day: int, winner: int):
    cutoff = datetime(2026, 2, day, 9, tzinfo=timezone.utc)
    return [RaceOutcome(race_id, lane, lane == winner, cutoff) for lane in range(1, 7)]


def test_baseline_evaluation_records_temporal_provenance():
    rows = race_rows("r1", 1, 1) + race_rows("r2", 2, 2) + race_rows("r3", 3, 3)
    split = temporal_holdout(rows, holdout_races=1)
    evaluation = evaluate_lane_baseline(split)

    assert evaluation.model_version == "lane-frequency-v1"
    assert evaluation.train_races == 2
    assert evaluation.holdout_races == 1
    assert evaluation.holdout_rows == 6
    assert evaluation.train_end_cutoff_at < evaluation.holdout_start_cutoff_at
    assert evaluation.metrics.sample_count == 6
    assert evaluation.calibration


def test_baseline_evaluation_is_deterministic():
    rows = race_rows("r1", 1, 1) + race_rows("r2", 2, 2) + race_rows("r3", 3, 3)
    split = temporal_holdout(rows, holdout_races=1)

    first = evaluate_lane_baseline(split, smoothing=Decimal("1"))
    second = evaluate_lane_baseline(split, smoothing=Decimal("1"))

    assert first == second
