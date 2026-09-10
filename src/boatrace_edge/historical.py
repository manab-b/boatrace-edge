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
DECISIONS = ("逃げ", "差し", "まくり差し", "まくり", "抜き")


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
    odds_status: str
    result: ResultRecord
    raw_documents: tuple[RawDocument, ...]


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _fetch(url: str) -> RawDocument:
    request = Request(url, headers={"User-Agent": "BOAT-RACE-EDGE/0.1"})
    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8", errors="strict")
        content_type = response.headers.get_content_type()
    return RawDocument(url, datetime.now(timezone.utc), hashlib.sha256(payload.encode("utf-8")).hexdigest(), content_type, payload)


def racelist_url(race_date: str, venue_code: str, race_number: int) -> str:
    return f"{OFFICIAL_BASE}/racelist?hd={race_date}&jcd={venue_code}&rno={race_number}"


def odds_url(race_date: str, venue_code: str, race_number: int) -> str:
    return f"{OFFICIAL_BASE}/odds3t?hd={race_date}&jcd={venue_code}&rno={race_number}"


def resultlist_url(race_date: str, venue_code: str) -> str:
    return f"{OFFICIAL_BASE}/resultlist?hd={race_date}&jcd={venue_code}"


def parse_racelist(payload: str, race_date: str, race_number: int) -> tuple[datetime, tuple[EntryRecord, ...]]:
    page_text = _clean(BeautifulSoup(payload, "html.parser").get_text(" "))
    match = re.search(r"締切予定時刻\s+((?:\d{2}:\d{2}\s+){11}\d{2}:\d{2})", page_text)
    if not match:
        raise ValueError("official racelist did not contain 12 scheduled deadlines")
    deadline = datetime.combine(datetime.strptime(race_date, "%Y%m%d").date(), time.fromisoformat(match.group(1).split()[race_number - 1]), JST)
    identity_matches = re.findall(r"\b(\d{4})\s*/\s*[A-Z]\d\s+(.{1,20}?)\s+[^ /]+/[^ /]+\s+\d+歳/", page_text)
    if len(identity_matches) < 6:
        raise ValueError("official racelist did not expose six racer identities in a stable form")
    return deadline, tuple(EntryRecord(lane, rid, _clean(name)) for lane, (rid, name) in enumerate(identity_matches[:6], start=1))


def parse_odds3t(payload: str) -> tuple[OddsRecord, ...]:
    page_text = _clean(BeautifulSoup(payload, "html.parser").get_text(" "))
    if "3連単オッズ" not in page_text:
        raise ValueError("official 3T odds section not found")
    section = page_text.split("3連単オッズ", 1)[1].split("締切時オッズは", 1)[0]
    tokens = re.findall(r"\d+(?:\.\d+)?", section)
    if len(tokens) != 360:
        raise ValueError(f"expected 360 numeric 3T odds tokens, got {len(tokens)}")
    records: list[OddsRecord] = []
    for row_index in range(20):
        row = tokens[row_index * 18 : (row_index + 1) * 18]
        for first in range(1, 7):
            second, third = int(row[(first - 1) * 3]), int(row[(first - 1) * 3 + 1])
            odds = Decimal(row[(first - 1) * 3 + 2])
            if len({first, second, third}) != 3:
                raise ValueError("invalid 3T combination in official odds")
            records.append(OddsRecord(f"{first}-{second}-{third}", odds))
    return tuple(records)


def parse_resultlist(payload: str, race_number: int) -> ResultRecord:
    page_text = _clean(BeautifulSoup(payload, "html.parser").get_text(" "))
    match = re.search(rf"{race_number}R\s+([1-6])\s*-\s*([1-6])\s*-\s*([1-6])\s+¥([0-9,]+)\s+([1-6])\s*-\s*([1-6])\s+¥([0-9,]+)", page_text)
    if not match:
        raise ValueError(f"official result payout row not found for {race_number}R")
    tail = page_text[match.end():]
    decision_match = re.search(r"(?:\d+R|着順 結果).*?(逃げ|差し|まくり差し|まくり|抜き)", tail)
    decision = decision_match.group(1) if decision_match else "UNKNOWN"
    return ResultRecord(
        f"{match.group(1)}-{match.group(2)}-{match.group(3)}",
        Decimal(match.group(4).replace(",", "")),
        f"{match.group(5)}-{match.group(6)}",
        Decimal(match.group(7).replace(",", "")),
        decision,
    )


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
    try:
        parsed_odds = parse_odds3t(odds.payload)
        odds_status = "COMPLETE"
    except ValueError:
        parsed_odds = ()
        odds_status = "INCOMPLETE_SOURCE_RESPONSE"
    result = parse_resultlist(results.payload, race_number)
    return RaceSnapshot(f"{race_date}-{venue_code}-{race_number:02d}", race_date, venue_code, race_number, deadline, entries, parsed_odds, odds_status, result, (racelist, odds, results))
