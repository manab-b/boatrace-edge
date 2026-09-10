from __future__ import annotations

import re
from datetime import date, timedelta

from .historical import RaceSnapshot, _fetch, parse_racelist, parse_resultlist, racelist_url, resultlist_url
from .official_archive import archive_documents, fetch_program_archive, fetch_result_archive, parse_program_text, parse_result_text


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
    if len(set(venues)) != len(venues):
        raise ValueError("venues must not contain duplicates")
    return dates


def collect_outcome_day(
    race_date: str, venue_code: str, *, race_start: int = 1, race_end: int = 12
) -> tuple[RaceSnapshot, ...]:
    """Collect official entries/deadlines plus official results without odds."""
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


def collect_outcome_archive_day(
    race_date: str,
    venue_codes: str | tuple[str, ...],
    *,
    race_start: int = 1,
    race_end: int = 12,
) -> tuple[RaceSnapshot, ...]:
    """Collect complete races from the official daily B/K LZH archives.

    The official daily archives contain all venues. For a batch request, the
    B and K archives are fetched exactly once for the date and then parsed for
    each requested venue. Odds are deliberately excluded. A race missing
    either a complete program or a result is skipped rather than inferred.

    The string form is retained for the single-venue API used by existing
    callers; the tuple form is the batch path and avoids 24 duplicate downloads.
    """
    venues = (venue_codes,) if isinstance(venue_codes, str) else venue_codes
    validate_batch_range(
        start=race_date,
        end=race_date,
        venues=venues,
        race_start=race_start,
        race_end=race_end,
    )

    program = fetch_program_archive(race_date)
    result = fetch_result_archive(race_date)
    documents = archive_documents(program, result)
    snapshots: list[RaceSnapshot] = []

    for venue_code in venues:
        programs = parse_program_text(program.text, race_date, venue_code)
        results = parse_result_text(result.text, venue_code)
        if not programs or not results:
            continue
        for race_number in range(race_start, race_end + 1):
            if race_number not in programs or race_number not in results:
                continue
            deadline, entries = programs[race_number]
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
                    results[race_number],
                    documents,
                )
            )
    return tuple(snapshots)
