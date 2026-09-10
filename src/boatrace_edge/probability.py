from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RaceOutcome:
    """Point-in-time training row for the baseline lane-win model."""

    race_id: str
    lane: int
    won: bool
    feature_cutoff_at: datetime


@dataclass(frozen=True)
class LaneProbabilityModel:
    """Deterministic empirical baseline for first-place probability by lane.

    This is deliberately a weak baseline: lane is the only feature. Training rows
    contain historical outcomes only; odds, payouts, and post-race fields are not
    accepted as model inputs.
    """

    probabilities: tuple[Decimal, ...]
    sample_count: int
    model_version: str = "lane-frequency-v1"

    def probability(self, lane: int) -> Decimal:
        if lane < 1 or lane > 6:
            raise ValueError("lane must be between 1 and 6")
        return self.probabilities[lane - 1]


def fit_lane_frequency(
    rows: Iterable[RaceOutcome], *, smoothing: Decimal = Decimal("0")
) -> LaneProbabilityModel:
    rows = tuple(rows)
    if not rows:
        raise ValueError("at least one historical outcome is required")
    if smoothing < 0:
        raise ValueError("smoothing must be non-negative")

    wins = [Decimal("0")] * 6
    exposures = [Decimal("0")] * 6
    seen: set[tuple[str, int]] = set()
    winners: dict[str, int] = {}

    for row in rows:
        if not row.race_id:
            raise ValueError("race_id is required")
        if row.lane < 1 or row.lane > 6:
            raise ValueError("lane must be between 1 and 6")
        key = (row.race_id, row.lane)
        if key in seen:
            raise ValueError("duplicate race/lane row")
        seen.add(key)
        exposures[row.lane - 1] += Decimal("1")
        if row.won:
            winners[row.race_id] = winners.get(row.race_id, 0) + 1
            wins[row.lane - 1] += Decimal("1")

    race_ids = {race_id for race_id, _ in seen}
    if any(winners.get(race_id, 0) != 1 for race_id in race_ids):
        raise ValueError("each race must contain exactly one winner")
    if any(sum(1 for race_id, lane in seen if race_id == rid) != 6 for rid in race_ids):
        raise ValueError("each race must contain exactly six lanes")

    total_exposure = sum(exposures)
    probabilities = tuple(
        (wins[i] + smoothing) / (total_exposure + smoothing * Decimal("6"))
        for i in range(6)
    )
    return LaneProbabilityModel(probabilities=probabilities, sample_count=len(rows))


def predict_race(model: LaneProbabilityModel, lanes: Sequence[int]) -> dict[int, Decimal]:
    if len(lanes) != 6 or sorted(lanes) != [1, 2, 3, 4, 5, 6]:
        raise ValueError("lanes must contain exactly 1 through 6")
    predictions = {lane: model.probability(lane) for lane in lanes}
    total = sum(predictions.values())
    if total <= 0:
        raise ValueError("model probabilities must have positive mass")
    return {lane: probability / total for lane, probability in predictions.items()}
