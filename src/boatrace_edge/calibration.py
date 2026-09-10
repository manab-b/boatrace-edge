from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import log
from typing import Iterable


@dataclass(frozen=True)
class ProbabilityEvaluation:
    sample_count: int
    log_loss: Decimal
    brier_score: Decimal


@dataclass(frozen=True)
class CalibrationBin:
    lower: Decimal
    upper: Decimal
    count: int
    mean_predicted: Decimal
    observed_rate: Decimal


def evaluate_binary(
    predictions: Iterable[Decimal], outcomes: Iterable[bool]
) -> ProbabilityEvaluation:
    predictions = tuple(predictions)
    outcomes = tuple(outcomes)
    if len(predictions) != len(outcomes) or not predictions:
        raise ValueError("predictions and outcomes must be non-empty and equal length")
    if any(p < 0 or p > 1 for p in predictions):
        raise ValueError("probabilities must be between 0 and 1")

    eps = 1e-15
    log_loss = -sum(
        int(y) * log(max(float(p), eps)) + (1 - int(y)) * log(max(1.0 - float(p), eps))
        for p, y in zip(predictions, outcomes)
    ) / len(predictions)
    brier = sum((p - Decimal(int(y))) ** 2 for p, y in zip(predictions, outcomes)) / Decimal(len(predictions))
    return ProbabilityEvaluation(
        sample_count=len(predictions),
        log_loss=Decimal(str(log_loss)),
        brier_score=brier,
    )


def calibration_bins(
    predictions: Iterable[Decimal], outcomes: Iterable[bool], *, bins: int = 10
) -> tuple[CalibrationBin, ...]:
    predictions = tuple(predictions)
    outcomes = tuple(outcomes)
    if len(predictions) != len(outcomes) or not predictions:
        raise ValueError("predictions and outcomes must be non-empty and equal length")
    if bins < 2:
        raise ValueError("bins must be at least 2")
    if any(p < 0 or p > 1 for p in predictions):
        raise ValueError("probabilities must be between 0 and 1")

    result: list[CalibrationBin] = []
    step = Decimal("1") / Decimal(bins)
    for index in range(bins):
        lower = step * Decimal(index)
        upper = Decimal("1") if index == bins - 1 else step * Decimal(index + 1)
        selected = [
            (p, y)
            for p, y in zip(predictions, outcomes)
            if (lower <= p < upper) or (index == bins - 1 and p == upper)
        ]
        if not selected:
            continue
        result.append(
            CalibrationBin(
                lower=lower,
                upper=upper,
                count=len(selected),
                mean_predicted=sum(p for p, _ in selected) / Decimal(len(selected)),
                observed_rate=sum(Decimal(int(y)) for _, y in selected) / Decimal(len(selected)),
            )
        )
    return tuple(result)
