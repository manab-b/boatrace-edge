import pytest

from boatrace_edge.historical_batch import (
    OFFICIAL_VENUE_CODES,
    iter_dates,
    validate_batch_range,
)


def test_iter_dates_is_inclusive_and_chronological():
    assert iter_dates("20260226", "20260228") == (
        "20260226",
        "20260227",
        "20260228",
    )


def test_batch_range_accepts_official_venues_and_races():
    dates = validate_batch_range(
        start="20260226",
        end="20260226",
        venues=("01", "24"),
        race_start=1,
        race_end=12,
    )
    assert dates == ("20260226",)
    assert OFFICIAL_VENUE_CODES == tuple(f"{n:02d}" for n in range(1, 25))


def test_batch_range_rejects_invalid_venue():
    with pytest.raises(ValueError, match="official two-digit venue codes"):
        validate_batch_range(
            start="20260226",
            end="20260226",
            venues=("25",),
            race_start=1,
            race_end=12,
        )


def test_batch_range_rejects_reverse_dates():
    with pytest.raises(ValueError, match="start date"):
        iter_dates("20260228", "20260226")


def test_batch_range_rejects_invalid_race_interval():
    with pytest.raises(ValueError, match="race range"):
        validate_batch_range(
            start="20260226",
            end="20260226",
            venues=("01",),
            race_start=12,
            race_end=1,
        )
