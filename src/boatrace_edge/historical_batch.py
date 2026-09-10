from __future__ import annotations

import re
from datetime import date, timedelta

from .historical import (
    RaceSnapshot,
    _fetch,
    parse_racelist,
    parse_resultlist,
    racelist_url,
    resultlist_url,
)


OFFICIAL_VENUE_CODES = tuple(f"{number:02d}" for number in range(1, 25))


def iter_dates(start: str, end: str) -> tuple[str, ...]:
    """Return inclusive YYYYMMDD dates in chronological order."""
    if not re.fullmatch(r"\d{8}", start) or not re.fullmatch(r"\d{8}", end):
        raise ValueError("dates must be YYYYMMDD")
    try:
        first = date.fromisoformat(f"{start[:4]}-{start[4:6]}-{start[6:8]}")
        last = date.fromisoformat(f"{end[:4]}-{end[4:6]}-{end[6:8]}")
    except ValueError:
        raise ValueError("dates must be YYYYMMDD") from None
    if first > last:
        raise ValueError("start date must not be after end date")
    days: list[str] = []
    current = first
    while current <= last:
        days.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return tuple(days)


def validate_batch_range(
    *, start: str, end: str, venues: tuple[str, ...], race_start: int, race_end: int
) -> tuple[str, ...]:
    dates = iter_dates(start, end)
    if not venues:
        raise ValueError("at least one venue is required")
    if any(not re.fullmatch(r"\d{2}", venue) or venue not in OFFICIAL_VENUE_CODES for venue in venues):
        raise ValueError("venues must be official two-digit venue codes 01 through 24")
    if not 1 <= race_start <= race_end <= 12:
        raise ValueError("race range must be between 1 and 12")
    return dates


def collect_outcome_day(
    race_date: str, venue_code: str, *, race_start: int = 1, race_end: int = 12
) -> tuple[RaceSnapshot, ...]:
    """Collect official entries/deadlines plus official results without odds.

    The odds status remains UNKNOWN because this path deliberately does not
    request an odds source. INCOMPLETE_SOURCE_RESPONSE is reserved for an
    attempted odds fetch whose official response cannot be normalized safely.
    """
    validate_batch_range(
        start=race_date,
        end=race_date,
        venues=(venue_code,),
        race_start=race_start,
        race_end=race_end,
    )
    results = _fetch(resultlist_url(race_date, venue_code))
    snapshots: list[RaceSnapshot] = []
    for race_number in range(race_start, race_end + 1):
        racelist = _fetch(racelist_url(race_date, venue_code, race_number))
        deadline, entries = parse_racelist(racelist.payload, race_date, race_number)
        result = parse_resultlist(results.payload, race_number)
        snapshots.append(
            RaceSnapshot(
                f"{race_date}-{venue_code}-{race_number:02d}",
                race_date,
                venue_code,
                race_number,
                deadline,
                entries,
                (),
                "UNKNOWN",
                result,
                (racelist, results),
            )
        )
    return tuple(snapshots)
