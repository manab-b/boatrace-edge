from datetime import date

from boatrace_edge import historical_store


def test_next_checkpoint_date_starts_from_requested_date_when_empty(monkeypatch) -> None:
    monkeypatch.setattr(historical_store, "get_checkpoint", lambda database_url: None)

    assert historical_store.next_checkpoint_date("db", "2026-01-01") == "20260101"


def test_next_checkpoint_date_resumes_after_last_completed_date(monkeypatch) -> None:
    monkeypatch.setattr(historical_store, "get_checkpoint", lambda database_url: date(2026, 1, 3))

    assert historical_store.next_checkpoint_date("db", "2026-01-01") == "20260104"


def test_next_checkpoint_date_does_not_move_before_requested_start(monkeypatch) -> None:
    monkeypatch.setattr(historical_store, "get_checkpoint", lambda database_url: date(2025, 12, 31))

    assert historical_store.next_checkpoint_date("db", "2026-01-01") == "20260101"
