from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .calibration import CalibrationBin, ProbabilityEvaluation, calibration_bins, evaluate_binary
from .dataset import TemporalSplit
from .probability import fit_lane_frequency, predict_race


@dataclass(frozen=True)
class BaselineEvaluation:
    model_version: str
    train_races: int
    holdout_races: int
    holdout_rows: int
    train_end_cutoff_at: datetime
    holdout_start_cutoff_at: datetime
    metrics: ProbabilityEvaluation
    calibration: tuple[CalibrationBin, ...]


def evaluate_lane_baseline(
    split: TemporalSplit, *, smoothing: Decimal = Decimal("0"), bins: int = 10
) -> BaselineEvaluation:
    model = fit_lane_frequency(split.train, smoothing=smoothing)
    predictions = []
    outcomes = []
    for race_id in sorted({row.race_id for row in split.holdout}):
        race_rows = [row for row in split.holdout if row.race_id == race_id]
        race_predictions = predict_race(model, [row.lane for row in race_rows])
        for row in race_rows:
            predictions.append(race_predictions[row.lane])
            outcomes.append(row.won)

    return BaselineEvaluation(
        model_version=model.model_version,
        train_races=len({row.race_id for row in split.train}),
        holdout_races=len({row.race_id for row in split.holdout}),
        holdout_rows=len(split.holdout),
        train_end_cutoff_at=max(row.feature_cutoff_at for row in split.train),
        holdout_start_cutoff_at=split.cutoff_at,
        metrics=evaluate_binary(predictions, outcomes),
        calibration=calibration_bins(predictions, outcomes, bins=bins),
    )
