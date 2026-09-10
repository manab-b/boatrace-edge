from decimal import Decimal

import pytest

from boatrace_edge.calibration import calibration_bins, evaluate_binary


def test_evaluate_binary_returns_log_loss_and_brier_score():
    result = evaluate_binary(
        [Decimal("0.9"), Decimal("0.2")],
        [True, False],
    )

    assert result.sample_count == 2
    assert result.log_loss > 0
    assert result.brier_score == Decimal("0.025")


def test_calibration_bins_report_prediction_and_observed_rate():
    bins = calibration_bins(
        [Decimal("0.1"), Decimal("0.2"), Decimal("0.8"), Decimal("0.9")],
        [False, False, True, True],
        bins=2,
    )

    assert len(bins) == 2
    assert bins[0].mean_predicted == Decimal("0.15")
    assert bins[0].observed_rate == Decimal("0")
    assert bins[1].mean_predicted == Decimal("0.85")
    assert bins[1].observed_rate == Decimal("1")


def test_rejects_invalid_probability_inputs():
    with pytest.raises(ValueError):
        evaluate_binary([Decimal("1.1")], [True])
    with pytest.raises(ValueError):
        calibration_bins([], [], bins=10)
