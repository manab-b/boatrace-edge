from datetime import datetime, timezone
from decimal import Decimal

import pytest

from boatrace_edge.probability import RaceOutcome, fit_lane_frequency, predict_race


def rows_for_race(race_id: str, winner: int, day: int = 26):
    cutoff = datetime(2026, 2, day, 9, tzinfo=timezone.utc)
    return [
        RaceOutcome(race_id=race_id, lane=lane, won=lane == winner, feature_cutoff_at=cutoff)
        for lane in range(1, 7)
    ]


def test_lane_frequency_uses_only_historical_outcomes():
    model = fit_lane_frequency(rows_for_race("r1", 1) + rows_for_race("r2", 2))

    assert model.sample_count == 12
    assert model.probability(1) == Decimal("1") / Decimal("2")
    assert model.probability(2) == Decimal("1") / Decimal("2")
    assert model.probability(3) == Decimal("0")


def test_smoothing_is_explicit_and_deterministic():
    model = fit_lane_frequency(rows_for_race("r1", 1), smoothing=Decimal("1"))

    assert sum(model.probabilities) == Decimal("1")
    assert model.probability(1) == Decimal("2") / Decimal("7")
    assert model.probability(2) == Decimal("1") / Decimal("7")


def test_predict_race_normalizes_candidate_lanes():
    model = fit_lane_frequency(rows_for_race("r1", 1))
    predictions = predict_race(model, [1, 2, 3, 4, 5, 6])

    assert sum(predictions.values()) == Decimal("1")
    assert predictions[1] == Decimal("1")


def test_rejects_duplicate_race_lane_rows():
    rows = rows_for_race("r1", 1)
    rows.append(rows[0])

    with pytest.raises(ValueError, match="duplicate race/lane"):
        fit_lane_frequency(rows)


def test_rejects_invalid_race_shape():
    rows = rows_for_race("r1", 1)
    rows[1] = RaceOutcome("r1", 2, True, rows[1].feature_cutoff_at)

    with pytest.raises(ValueError, match="exactly one winner"):
        fit_lane_frequency(rows)
