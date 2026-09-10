from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from html import unescape
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

OFFICIAL_BASE = "https://www.boatrace.jp/owpc/pc/race"
JST = timezone(timedelta(hours=9))
DECISIONS = {"逃げ", "差し", "まくり", "まくり差し", "抜き"}


@dataclass(frozen=True)
class RawDocument:
    source_url: str
    fetched_at: datetime
    content_sha256: str
    content_type: str
    payload: str


@dataclass(frozen=True)
class EntryRecord:
    lane: int
    racer_id: str
    racer_name: str


@dataclass(frozen=True)
class OddsRecord:
    combination: str
    odds: Decimal


@dataclass(frozen=True)
class ResultRecord:
    combination_3t: str
    payout_3t: Decimal
    combination_2t: str
    payout_2t: Decimal
    decision: str


@dataclass(frozen=True)
class RaceSnapshot:
    race_id: str
    race_date: str
    venue_code: str
    race_number: int
    scheduled_deadline_at: datetime
    entries: tuple[EntryRecord, ...]
    odds: tuple[OddsRecord, ...]
    result: ResultRecord
    raw_documents: tuple[RawDocument, ...]


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _fetch(url: str) -> RawDocument:
    request = Request(url, headers={"User-Agent": "BOAT-RACE-EDGE/0.1"})
    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8", errors="strict")
        content_type = response.headers.get_content_type()
    return RawDocument(
        source_url=url,
        fetched_at=datetime.now(timezone.utc),
        content_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        content_type=content_type,
        payload=payload,
    )


def racelist_url(race_date: str, venue_code: str, race_number: int) -> str:
    return f"{OFFICIAL_BASE}/racelist?hd={race_date}&jcd={venue_code}&rno={race_number}"


def odds_url(race_date: str, venue_code: str, race_number: int) -> str:
    return f"{OFFICIAL_BASE}/odds3t?hd={race_date}&jcd={venue_code}&rno={race_number}"


def resultlist_url(race_date: str, venue_code: str) -> str:
    return f"{OFFICIAL_BASE}/resultlist?hd={race_date}&jcd={venue_code}"


def parse_racelist(
    payload: str, race_date: str, race_number: int
) -> tuple[datetime, tuple[EntryRecord, ...]]:
    soup = BeautifulSoup(payload, "html.parser")
    page_text = _clean(soup.get_text(" "))
    match = re.search(r"締切予定時刻\s+((?:\d{2}:\d{2}\s+){11}\d{2}:\d{2})", page_text)
    if not match:
        raise ValueError("official racelist did not contain 12 scheduled deadlines")
    deadlines = match.group(1).split()
    deadline = datetime.combine(
        datetime.strptime(race_date, "%Y%m%d").date(),
        time.fromisoformat(deadlines[race_number - 1]),
        JST,
    )

    identity_matches = re.findall(
        r"\b(\d{4})\s*/\s*[A-Z]\d\s+(.{1,20}?)\s+[^ /]+/[^ /]+\s+\d+歳/",
        page_text,
    )
    if len(identity_matches) >= 6:
        entries = tuple(
            EntryRecord(lane, racer_id, _clean(name))
            for lane, (racer_id, name) in enumerate(identity_matches[:6], start=1)
        )
        return deadline, entries

    target = next((t for t in soup.find_all("table") if "登録番号/級別" in t.get_text(" ")), None)
    if target is None:
        raise ValueError("official racelist entry table not found")

    entries: list[EntryRecord] = []
    for row in target.find_all("tr"):
        cells = [_clean(c.get_text(" ")) for c in row.find_all(["th", "td"])]
        if not cells or cells[0] not in {str(i) for i in range(1, 7)}:
            continue
        lane = int(cells[0])
        racer_match = re.search(r"\b(\d{4})\b", " ".join(cells))
        if not racer_match:
            raise ValueError(f"racer registration number missing for lane {lane}")
        names = [
            _clean(a.get_text(" "))
            for a in row.find_all("a")
            if _clean(a.get_text(" ")) and not re.fullmatch(r"\d+R?", _clean(a.get_text(" ")))
        ]
        if not names:
            raise ValueError(f"racer name missing for lane {lane}")
        entries.append(EntryRecord(lane, racer_match.group(1), names[0]))

    if len(entries) != 6:
        raise ValueError(f"expected 6 entries, got {len(entries)}")
    return deadline, tuple(entries)


def parse_odds3t(payload: str) -> tuple[OddsRecord, ...]:
    soup = BeautifulSoup(payload, "html.parser")
    records: list[OddsRecord] = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            tokens = [_clean(x) for x in row.stripped_strings]
            if len(tokens) < 18:
                continue
            groups = tokens[:18]
            if not all(re.fullmatch(r"\d+(?:\.\d+)?", x) for x in groups):
                continue
            for first in range(1, 7):
                second = int(groups[(first - 1) * 3])
                third = int(groups[(first - 1) * 3 + 1])
                odds = Decimal(groups[(first - 1) * 3 + 2])
                if len({first, second, third}) != 3:
                    raise ValueError("invalid 3T combination in official odds")
                records.append(OddsRecord(f"{first}-{second}-{third}", odds))
        if len(records) == 120:
            break

    if len(records) != 120:
        raise ValueError(f"expected 120 3T odds, got {len(records)}")
    return tuple(records)


def parse_resultlist(payload: str, race_number: int) -> ResultRecord:
    soup = BeautifulSoup(payload, "html.parser")
    for row in soup.find_all("tr"):
        cells = [_clean(c.get_text(" ")) for c in row.find_all(["th", "td"])]
        if not cells or cells[0] != f"{race_number}R":
            continue
        joined = " ".join(cells)
        combos = re.findall(r"([1-6])\s*-\s*([1-6])(?:\s*-\s*([1-6]))?", joined)
        payout_cells = [c for c in cells if "¥" in c]
        if len(combos) < 2 or len(payout_cells) < 2:
            continue
        combination_3t = "-".join(x for x in combos[0] if x)
        combination_2t = "-".join(x for x in combos[1][:2] if x)
        payout_3t = Decimal(re.sub(r"[^0-9.]", "", payout_cells[0]))
        payout_2t = Decimal(re.sub(r"[^0-9.]", "", payout_cells[1]))
        decision = next((c for c in reversed(cells) if c in DECISIONS), "UNKNOWN")
        return ResultRecord(combination_3t, payout_3t, combination_2t, payout_2t, decision)
    raise ValueError(f"3T/2T payout row not found for {race_number}R")


def collect_race(race_date: str, venue_code: str, race_number: int) -> RaceSnapshot:
    if not re.fullmatch(r"\d{8}", race_date):
        raise ValueError("race_date must be YYYYMMDD")
    if not re.fullmatch(r"\d{2}", venue_code):
        raise ValueError("venue_code must be a two-digit official venue code")
    if not 1 <= race_number <= 12:
        raise ValueError("race_number must be between 1 and 12")

    racelist = _fetch(racelist_url(race_date, venue_code, race_number))
    odds = _fetch(odds_url(race_date, venue_code, race_number))
    results = _fetch(resultlist_url(race_date, venue_code))
    deadline, entries = parse_racelist(racelist.payload, race_date, race_number)
    parsed_odds = parse_odds3t(odds.payload)
    result = parse_resultlist(results.payload, race_number)
    race_id = f"{race_date}-{venue_code}-{race_number:02d}"
    return RaceSnapshot(
        race_id=race_id,
        race_date=race_date,
        venue_code=venue_code,
        race_number=race_number,
        scheduled_deadline_at=deadline,
        entries=entries,
        odds=parsed_odds,
        result=result,
        raw_documents=(racelist, odds, results),
    )
