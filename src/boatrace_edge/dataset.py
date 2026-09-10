from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence

import psycopg

from .probability import RaceOutcome


@dataclass(frozen=True)
class TemporalSplit:
    train: tuple[RaceOutcome, ...]
    holdout: tuple[RaceOutcome, ...]
    cutoff_at: datetime


def load_lane_outcomes(database_url: str) -> tuple[RaceOutcome, ...]:
    """Build PIT-safe first-place rows only from normalized historical tables."""
    with psycopg.connect(database_url) as conn:
        rows = conn.execute(
            """
            SELECT r.race_id, e.lane,
                   e.lane = rr.first_lane AS won,
                   r.scheduled_deadline_at AS feature_cutoff_at
            FROM race AS r
            JOIN entry AS e ON e.race_id = r.race_id
            JOIN race_result AS rr ON rr.race_id = r.race_id
            WHERE r.scheduled_deadline_at IS NOT NULL
            ORDER BY r.scheduled_deadline_at, r.race_id, e.lane
            """
        ).fetchall()
    outcomes = tuple(
        RaceOutcome(race_id, lane, won, feature_cutoff_at)
        for race_id, lane, won, feature_cutoff_at in rows
    )
    return build_lane_outcomes(outcomes)


def build_lane_outcomes(rows: Iterable[RaceOutcome]) -> tuple[RaceOutcome, ...]:
    """Validate and deterministically order normalized historical race outcomes."""
    rows = tuple(rows)
    if not rows:
        raise ValueError("historical rows are required")
    by_race: dict[str, list[RaceOutcome]] = {}
    for row in rows:
        if row.lane < 1 or row.lane > 6:
            raise ValueError("lane must be between 1 and 6")
        by_race.setdefault(row.race_id, []).append(row)

    for race_id, race_rows in by_race.items():
        if len(race_rows) != 6:
            raise ValueError(f"race {race_id} must contain exactly six lanes")
        if len({row.lane for row in race_rows}) != 6:
            raise ValueError(f"race {race_id} contains duplicate lanes")
        if sum(row.won for row in race_rows) != 1:
            raise ValueError(f"race {race_id} must contain exactly one winner")
        if len({row.feature_cutoff_at for row in race_rows}) != 1:
            raise ValueError(f"race {race_id} must share one feature cutoff")

    return tuple(sorted(rows, key=lambda row: (row.feature_cutoff_at, row.race_id, row.lane)))


def temporal_holdout(
    rows: Sequence[RaceOutcome], *, holdout_races: int
) -> TemporalSplit:
    """Split complete races chronologically; no race may straddle train/holdout."""
    normalized = build_lane_outcomes(rows)
    if holdout_races < 1:
        raise ValueError("holdout_races must be at least one")
    race_cutoffs: dict[str, datetime] = {}
    for row in normalized:
        existing = race_cutoffs.setdefault(row.race_id, row.feature_cutoff_at)
        if existing != row.feature_cutoff_at:
            raise ValueError("all lanes in a race must share one feature cutoff")

    ordered_races = sorted(race_cutoffs.items(), key=lambda item: (item[1], item[0]))
    if holdout_races >= len(ordered_races):
        raise ValueError("holdout must leave at least one training race")
    holdout_ids = {race_id for race_id, _ in ordered_races[-holdout_races:]}
    train = tuple(row for row in normalized if row.race_id not in holdout_ids)
    holdout = tuple(row for row in normalized if row.race_id in holdout_ids)
    cutoff_at = min(row.feature_cutoff_at for row in holdout)
    if max(row.feature_cutoff_at for row in train) >= cutoff_at:
        raise ValueError("temporal holdout overlaps training period")
    return TemporalSplit(train=train, holdout=holdout, cutoff_at=cutoff_at)
