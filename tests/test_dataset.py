from datetime import datetime, timedelta, timezone

import pytest

from boatrace_edge.dataset import build_lane_outcomes, temporal_holdout
from boatrace_edge.probability import RaceOutcome


def race_rows(race_id: str, day: int, winner: int):
    cutoff = datetime(2026, 2, day, 9, tzinfo=timezone.utc)
    return [
        RaceOutcome(race_id, lane, lane == winner, cutoff)
        for lane in range(1, 7)
    ]


def test_build_lane_outcomes_is_deterministic_and_complete():
    rows = race_rows("r2", 2, 2) + race_rows("r1", 1, 1)
    normalized = build_lane_outcomes(rows)

    assert [row.race_id for row in normalized[:6]] == ["r1"] * 6
    assert [row.lane for row in normalized[:6]] == [1, 2, 3, 4, 5, 6]


def test_temporal_holdout_keeps_whole_races_and_time_order():
    rows = race_rows("r1", 1, 1) + race_rows("r2", 2, 2) + race_rows("r3", 3, 3)
    split = temporal_holdout(rows, holdout_races=1)

    assert {row.race_id for row in split.train} == {"r1", "r2"}
    assert {row.race_id for row in split.holdout} == {"r3"}
    assert max(row.feature_cutoff_at for row in split.train) < split.cutoff_at


def test_rejects_incomplete_race():
    rows = race_rows("r1", 1, 1)[:-1]
    with pytest.raises(ValueError, match="exactly six lanes"):
        build_lane_outcomes(rows)


def test_rejects_mixed_cutoffs_within_race():
    rows = race_rows("r1", 1, 1)
    rows[1] = RaceOutcome("r1", 2, False, rows[1].feature_cutoff_at + timedelta(minutes=1))
    with pytest.raises(ValueError, match="share one feature cutoff"):
        temporal_holdout(rows + race_rows("r2", 2, 2), holdout_races=1)


def test_holdout_cannot_consume_all_races():
    with pytest.raises(ValueError, match="at least one training race"):
        temporal_holdout(race_rows("r1", 1, 1), holdout_races=1)
