from decimal import Decimal
from itertools import permutations

import pytest

from boatrace_edge.historical import parse_odds3t, parse_racelist, parse_resultlist


RACELIST_HTML = """
<html><body>
締切予定時刻 10:57 11:26 11:55 12:24 12:54 13:24 13:55 14:26 14:58 15:31 16:05 16:40
<table><tr><th>登録番号/級別</th><th>氏名</th></tr>
<tr><td>1</td><td>4200 / B1</td><td><a>早川 尚人</a></td><td>大阪/大阪 43歳/</td></tr>
<tr><td>2</td><td>4339 / B1</td><td><a>平瀬 城啓</a></td><td>大阪/大阪 44歳/</td></tr>
<tr><td>3</td><td>4197 / B1</td><td><a>渥美 卓郎</a></td><td>大阪/大阪 45歳/</td></tr>
<tr><td>4</td><td>4641 / B1</td><td><a>磯村 匠</a></td><td>大阪/大阪 38歳/</td></tr>
<tr><td>5</td><td>4060 / B1</td><td><a>島田 一生</a></td><td>大阪/大阪 42歳/</td></tr>
<tr><td>6</td><td>4298 / A1</td><td><a>宮下 元胤</a></td><td>大阪/大阪 43歳/</td></tr>
</table></body></html>
"""


RESULT_HTML = """
<html><body>
レース 3連勝単式 2連勝単式
1R 1 -3 -6 ¥2,880 1 -3 ¥1,230
2R 4 -3 -2 ¥4,740 4 -3 ¥1,210
着順 結果 1R 一般 １着 ２着 ３着 ４着 ５着 ６着 逃げ
</body></html>
"""


def _valid_odds_html() -> str:
    rows = []
    by_first = {first: list(permutations([lane for lane in range(1, 7) if lane != first], 2)) for first in range(1, 7)}
    for row_index in range(20):
        cells = []
        for first in range(1, 7):
            second, third = by_first[first][row_index]
            cells.extend((str(second), str(third), "10.0"))
        rows.append("<tr>" + "".join(f"<td>{x}</td>" for x in cells) + "</tr>")
    return "<html><body>3連単オッズ<table>" + "".join(rows) + "</table>締切時オッズは source page text</body></html>"


def test_racelist_parses_six_entries_and_jst_deadline() -> None:
    deadline, entries = parse_racelist(RACELIST_HTML, "20260226", 1)
    assert deadline.isoformat() == "2026-02-26T10:57:00+09:00"
    assert len(entries) == 6
    assert entries[0].racer_id == "4200"
    assert entries[5].racer_name == "宮下 元胤"


def test_result_list_parser_reads_official_payout_rows() -> None:
    result = parse_resultlist(RESULT_HTML, 1)
    assert result.combination_3t == "1-3-6"
    assert result.payout_3t == Decimal("2880")
    assert result.combination_2t == "1-3"
    assert result.payout_2t == Decimal("1230")
    assert result.decision == "逃げ"


def test_odds_parser_accepts_complete_120_combination_matrix() -> None:
    records = parse_odds3t(_valid_odds_html())
    assert len(records) == 120
    assert len({record.combination for record in records}) == 120
    assert records[0].odds == Decimal("10.0")


def test_odds_parser_rejects_incomplete_matrix() -> None:
    with pytest.raises(ValueError, match="expected 360"):
        parse_odds3t("<html><body>3連単オッズ<table><tr><td>1</td></tr></table></body></html>")
