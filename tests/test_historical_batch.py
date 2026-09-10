from datetime import datetime, timezone

import pytest

from boatrace_edge.historical_batch import (
    OFFICIAL_VENUE_CODES,
    collect_outcome_archive_day,
    iter_dates,
    validate_batch_range,
)
from boatrace_edge.official_archive import ArchiveText


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


def test_archive_batch_fetches_each_daily_archive_once(monkeypatch: pytest.MonkeyPatch) -> None:
    archive = ArchiveText(
        "http://example.invalid/archive",
        datetime(2026, 9, 10, tzinfo=timezone.utc),
        "archive-sha",
        "text",
        "text-sha",
    )
    calls = {"program": 0, "result": 0}

    def fetch_program(_: str) -> ArchiveText:
        calls["program"] += 1
        return archive

    def fetch_result(_: str) -> ArchiveText:
        calls["result"] += 1
        return archive

    monkeypatch.setattr("boatrace_edge.historical_batch.fetch_program_archive", fetch_program)
    monkeypatch.setattr("boatrace_edge.historical_batch.fetch_result_archive", fetch_result)
    monkeypatch.setattr("boatrace_edge.historical_batch.parse_program_text", lambda *args: {})
    monkeypatch.setattr("boatrace_edge.historical_batch.parse_result_text", lambda *args: {})

    snapshots = collect_outcome_archive_day("20260226", ("01", "24"))

    assert snapshots == ()
    assert calls == {"program": 1, "result": 1}
