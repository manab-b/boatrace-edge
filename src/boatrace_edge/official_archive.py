from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from urllib.request import Request, urlopen

import lhafile

from .historical import EntryRecord, RawDocument, ResultRecord

ARCHIVE_BASE = "http://www1.mbrace.or.jp/od2"
JST = timezone(timedelta(hours=9))


@dataclass(frozen=True)
class ArchiveText:
    source_url: str
    fetched_at: datetime
    archive_sha256: str
    text: str
    text_sha256: str


def _archive_url(kind: str, race_date: str) -> str:
    if kind not in {"B", "K"}:
        raise ValueError("kind must be B or K")
    if not re.fullmatch(r"\d{8}", race_date):
        raise ValueError("race_date must be YYYYMMDD")
    return f"{ARCHIVE_BASE}/{kind}/{race_date[:6]}/{kind.lower()}{race_date[2:]}.lzh"


def program_archive_url(race_date: str) -> str:
    return _archive_url("B", race_date)


def result_archive_url(race_date: str) -> str:
    return _archive_url("K", race_date)


def _fetch_archive(url: str) -> ArchiveText:
    request = Request(url, headers={"User-Agent": "BOAT-RACE-EDGE/0.1"})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    archive_sha256 = hashlib.sha256(payload).hexdigest()
    archive = lhafile.Lhafile(BytesIO(payload))
    names = archive.namelist() or []
    if len(names) != 1:
        raise ValueError(f"official archive must contain exactly one text file, got {len(names)}")
    text_payload = archive.read(names[0])
    text = text_payload.decode("shift_jis", errors="strict")
    return ArchiveText(
        source_url=url,
        fetched_at=datetime.now(timezone.utc),
        archive_sha256=archive_sha256,
        text=text,
        text_sha256=hashlib.sha256(text_payload).hexdigest(),
    )


def fetch_program_archive(race_date: str) -> ArchiveText:
    return _fetch_archive(program_archive_url(race_date))


def fetch_result_archive(race_date: str) -> ArchiveText:
    return _fetch_archive(result_archive_url(race_date))


def _normal(text: str) -> str:
    return unicodedata.normalize("NFKC", text).replace("\r", "")


def _venue_blocks(text: str, marker: str) -> dict[str, list[str]]:
    lines = _normal(text).splitlines()
    blocks: dict[str, list[str]] = {}
    current: list[str] | None = None
    venue: str | None = None
    for line in lines:
        begin = re.match(r"^\s*(\d{2})" + re.escape(marker) + r"BGN\s*$", line)
        if begin:
            if current is not None:
                raise ValueError("nested official archive venue boundaries")
            venue = begin.group(1)
            current = []
            continue
        end = re.match(r"^\s*(\d{2})" + re.escape(marker) + r"END\s*$", line)
        if end:
            if current is None or venue != end.group(1):
                raise ValueError("malformed official archive venue boundaries")
            blocks[venue] = current
            current = None
            venue = None
            continue
        if current is not None:
            current.append(line)
    if current is not None or venue is not None:
        raise ValueError("unterminated official archive venue block")
    return blocks


def _parse_race_header(line: str) -> int | None:
    match = re.match(r"^\s*(\d{1,2})R(?:\s|$)", line)
    return int(match.group(1)) if match else None


def _entry_from_line(line: str) -> EntryRecord | None:
    # Official B files are fixed-format and may place the racer number
    # immediately after the lane number; whitespace is not semantically
    # significant here.
    match = re.match(r"^\s*([1-6])\s*(\d{4})(.*)$", line)
    if not match:
        return None
    return EntryRecord(int(match.group(1)), match.group(2), "UNKNOWN")


def parse_program_text(text: str, race_date: str, venue_code: str) -> dict[int, tuple[datetime, tuple[EntryRecord, ...]]]:
    if not re.fullmatch(r"\d{8}", race_date):
        raise ValueError("race_date must be YYYYMMDD")
    if not re.fullmatch(r"\d{2}", venue_code):
        raise ValueError("venue_code must be a two-digit official venue code")
    blocks = _venue_blocks(text, "B")
    if venue_code not in blocks:
        return {}

    races: dict[int, tuple[datetime, tuple[EntryRecord, ...]]] = {}
    current_race: int | None = None
    deadline: time | None = None
    entries: dict[int, EntryRecord] = {}

    def finish_current() -> None:
        if current_race is None:
            return
        if deadline is None or set(entries) != set(range(1, 7)):
            raise ValueError(f"incomplete program data for {current_race}R")
        races[current_race] = (
            datetime.combine(datetime.strptime(race_date, "%Y%m%d").date(), deadline, JST),
            tuple(entries[i] for i in range(1, 7)),
        )

    for line in blocks[venue_code]:
        race = _parse_race_header(line)
        if race is not None:
            finish_current()
            current_race = race
            deadline = None
            entries = {}
            continue
        if current_race is None:
            continue
        deadline_match = re.search(r"締切予定\s*(\d{1,2}):(\d{2})", line)
        if deadline_match:
            deadline = time(int(deadline_match.group(1)), int(deadline_match.group(2)))
        if len(entries) >= 6:
            # A B archive can contain additional non-entry sections after the
            # six official starters. They must not be mistaken for duplicate
            # lanes belonging to the same race.
            continue
        entry = _entry_from_line(line)
        if entry is not None:
            if entry.lane in entries:
                raise ValueError(f"duplicate program lane {entry.lane} in {current_race}R")
            entries[entry.lane] = entry

    finish_current()
    return races


def parse_result_text(text: str, venue_code: str) -> dict[int, ResultRecord]:
    blocks = _venue_blocks(text, "K")
    if venue_code not in blocks:
        return {}
    results: dict[int, ResultRecord] = {}
    for line in blocks[venue_code]:
        normalized = _normal(line).replace("[払戻金]", "")
        race_match = re.match(r"^\s*(\d{1,2})R\b", normalized)
        if not race_match:
            continue
        race_number = int(race_match.group(1))
        triple_match = re.search(r"([1-6])\s*-\s*([1-6])\s*-\s*([1-6])\s+([0-9,]+)", normalized)
        pair_matches = list(re.finditer(r"([1-6])\s*-\s*([1-6])\s+([0-9,]+)", normalized))
        if triple_match is None or not pair_matches:
            continue
        pair_match = pair_matches[-1]
        results[race_number] = ResultRecord(
            f"{triple_match.group(1)}-{triple_match.group(2)}-{triple_match.group(3)}",
            Decimal(triple_match.group(4).replace(",", "")),
            f"{pair_match.group(1)}-{pair_match.group(2)}",
            Decimal(pair_match.group(3).replace(",", "")),
            "UNKNOWN",
        )
    return results


def archive_documents(program: ArchiveText, result: ArchiveText) -> tuple[RawDocument, RawDocument]:
    return tuple(
        RawDocument(
            archive.source_url,
            archive.fetched_at,
            archive.text_sha256,
            "text/plain; charset=shift_jis",
            archive.text,
        )
        for archive in (program, result)
    )
