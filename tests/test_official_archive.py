from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from boatrace_edge.official_archive import parse_program_text, parse_result_text, program_archive_url, result_archive_url


PROGRAM_FIXTURE = """STARTB
24BBGN
  1R 一般 H1800m 電話投票締切予定15:15
1 4966田川大貴24長崎53B1 4.76
2 4705吉川勇作33長崎54B1 4.22
3 5055眞鳥章太25長崎53B1 2.88
4 5011高木圭大24長崎52B1 3.65
5 4969町田洸希30長崎54B1 4.07
6 4299中島浩哉39長崎56B1 4.98
24BEND
FINB
"""

RESULT_FIXTURE = """STARTK
24KBGN
[払戻金] 3連単 3連複 2連単 2連複
  1R 1-5-3 5460 1-3-5 1130 1-5 920 1-5 720
24KEND
FINALK
"""


JST = timezone(timedelta(hours=9))


def test_archive_urls_use_official_daily_pattern() -> None:
    assert program_archive_url("20260101") == "http://www1.mbrace.or.jp/od2/B/202601/b260101.lzh"
    assert result_archive_url("20260101") == "http://www1.mbrace.or.jp/od2/K/202601/k260101.lzh"


def test_program_parser_extracts_point_in_time_deadline_and_six_lanes() -> None:
    races = parse_program_text(PROGRAM_FIXTURE, "20220101", "24")
    deadline, entries = races[1]
    assert deadline == datetime(2022, 1, 1, 15, 15, tzinfo=JST)
    assert [entry.lane for entry in entries] == [1, 2, 3, 4, 5, 6]
    assert [entry.racer_id for entry in entries] == ["4966", "4705", "5055", "5011", "4969", "4299"]


def test_result_parser_extracts_official_payouts_without_inference() -> None:
    results = parse_result_text(RESULT_FIXTURE, "24")
    result = results[1]
    assert result.combination_3t == "1-5-3"
    assert result.payout_3t == Decimal("5460")
    assert result.combination_2t == "1-5"
    assert result.payout_2t == Decimal("920")
    assert result.decision == "UNKNOWN"


def test_program_parser_rejects_incomplete_race() -> None:
    incomplete = PROGRAM_FIXTURE.replace("6 4299中島浩哉39長崎56B1 4.98\n", "")
    with pytest.raises(ValueError, match="incomplete program data"):
        parse_program_text(incomplete, "20220101", "24")
