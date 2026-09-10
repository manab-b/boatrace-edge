from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RaceOutcome:
    """Point-in-time training row for the baseline lane-win model."""

    race_id: str
    lane: int
    won: bool
    feature_cutoff_at: object


@dataclass(frozen=True)
class LaneProbabilityModel:
    """Deterministic empirical baseline for first-place probability by lane.

    This is deliberately a weak baseline: lane is the only feature. Training rows
    must be historical outcomes that were available after the race was scheduled
    and before any future prediction dataset is assembled. No odds, payouts, or
    post-race fields are accepted as model inputs.
    """

    probabilities: tuple[Decimal, ...]
    sample_count: int
    model_version: str = "lane-frequency-v1"

    def probability(self, lane: int) -> Decimal:
        if lane < 1 or lane > 6:
            raise ValueError("lane must be between 1 and 6")
        return self.probabilities[lane - 1]


def fit_lane_frequency(rows: Iterable[RaceOutcome], *, smoothing: Decimal = Decimal("0")) -> LaneProbabilityModel:
    rows = tuple(rows)
    if not rows:
        raise ValueError("at least one historical outcome is required")
    if smoothing < 0:
        raise ValueError("smoothing must be non-negative")

    wins = [Decimal("0")] * 6
    exposures = [Decimal("0")] * 6
    race_ids: set[str] = set()
    for row in rows:
        if not row.race_id:
            raise ValueError("race_id is required")
        if row.race_id in race_ids:
            raise ValueError("each race_id may appear only once per lane outcome")
        if row.lane < 1 or row.lane > 6:
            raise ValueError("lane must be between 1 and 6")
        race_ids.add(row.race_id)
        exposures[row.lane - 1] += Decimal("1")
        wins[row.lane - 1] += Decimal("1") if row.won else Decimal("0")

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
