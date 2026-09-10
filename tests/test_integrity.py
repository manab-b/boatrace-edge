from datetime import datetime, timezone

import pytest

from boatrace_edge.integrity import (
    validate_ingestion_order,
    validate_observation_cutoff,
)


UTC = timezone.utc


def test_observation_at_cutoff_is_allowed() -> None:
    cutoff = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    validate_observation_cutoff(cutoff, cutoff)


def test_future_observation_is_rejected() -> None:
    cutoff = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    future = datetime(2026, 1, 1, 12, 1, tzinfo=UTC)

    with pytest.raises(ValueError, match="after prediction cutoff"):
        validate_observation_cutoff(future, cutoff)


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        validate_observation_cutoff(
            datetime(2026, 1, 1, 12, 0),
            datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        )


def test_ingestion_cannot_precede_observation() -> None:
    observed = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    ingestion = datetime(2026, 1, 1, 11, 59, tzinfo=UTC)

    with pytest.raises(ValueError, match="precedes source observation"):
        validate_ingestion_order(observed, ingestion)
