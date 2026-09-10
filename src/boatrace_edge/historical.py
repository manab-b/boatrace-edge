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


def result_url(race_date: str, venue_code: str, race_number: int) -> str:
    return f"{OFFICIAL_BASE}/raceresult?hd={race_date}&jcd={venue_code}&rno={race_number}"


def parse_racelist(payload: str, race_date: str, race_number: int) -> tuple[datetime, tuple[EntryRecord, ...]]:
    soup = BeautifulSoup(payload, "html.parser")
    page_text = _clean(soup.get_text(" "))
    match = re.search(r"締切予定時刻\s+((?:\d{2}:\d{2}\s+){11}\d{2}:\d{2})", page_text)
    if not match:
        raise ValueError("official racelist did not contain 12 scheduled deadlines")
    deadline = datetime.combine(datetime.strptime(race_date, "%Y%m%d").date(), time.fromisoformat(match.group(1).split()[race_number - 1]), JST)
    identity_matches = re.findall(r"\b(\d{4})\s*/\s*[A-Z]\d\s+(.{1,20}?)\s+[^ /]+/[^ /]+\s+\d+歳/", page_text)
    if len(identity_matches) >= 6:
        return deadline, tuple(EntryRecord(lane, rid, _clean(name)) for lane, (rid, name) in enumerate(identity_matches[:6], start=1))
    raise ValueError("official racelist did not expose six racer identities in a stable form")


def parse_odds3t(payload: str) -> tuple[OddsRecord, ...]:
    soup = BeautifulSoup(payload, "html.parser")
    page_text = _clean(soup.get_text(" "))
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


def parse_result(payload: str) -> ResultRecord:
    soup = BeautifulSoup(payload, "html.parser")
    three = two = None
    for row in soup.find_all("tr"):
        cells = [_clean(c.get_text(" ")) for c in row.find_all(["th", "td"])]
        if not cells:
            continue
        if cells[0] == "3連単":
            three = cells
        elif cells[0] == "2連単":
            two = cells
    if not three or not two:
        raise ValueError("official result payout rows not found")
    combo3 = re.search(r"[1-6]-[1-6]-[1-6]", " ".join(three))
    combo2 = re.search(r"[1-6]-[1-6]", " ".join(two))
    payout3 = next((c for c in three if "¥" in c), None)
    payout2 = next((c for c in two if "¥" in c), None)
    if not combo3 or not combo2 or not payout3 or not payout2:
        raise ValueError("official result combination or payout missing")
    page_text = _clean(soup.get_text(" "))
    decision = next((d for d in DECISIONS if f"決まり手 {d}" in page_text), "UNKNOWN")
    return ResultRecord(combo3.group(0), Decimal(re.sub(r"[^0-9.]", "", payout3)), combo2.group(0), Decimal(re.sub(r"[^0-9.]", "", payout2)), decision)


def collect_race(race_date: str, venue_code: str, race_number: int) -> RaceSnapshot:
    if not re.fullmatch(r"\d{8}", race_date):
        raise ValueError("race_date must be YYYYMMDD")
    if not re.fullmatch(r"\d{2}", venue_code):
        raise ValueError("venue_code must be a two-digit official venue code")
    if not 1 <= race_number <= 12:
        raise ValueError("race_number must be between 1 and 12")
    racelist = _fetch(racelist_url(race_date, venue_code, race_number))
    odds = _fetch(odds_url(race_date, venue_code, race_number))
    results = _fetch(result_url(race_date, venue_code, race_number))
    deadline, entries = parse_racelist(racelist.payload, race_date, race_number)
    try:
        parsed_odds = parse_odds3t(odds.payload)
        odds_status = "COMPLETE"
    except ValueError:
        parsed_odds = ()
        odds_status = "INCOMPLETE_SOURCE_RESPONSE"
    result = parse_result(results.payload)
    return RaceSnapshot(f"{race_date}-{venue_code}-{race_number:02d}", race_date, venue_code, race_number, deadline, entries, parsed_odds, odds_status, result, (racelist, odds, results))
