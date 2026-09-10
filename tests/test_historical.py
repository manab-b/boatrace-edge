from decimal import Decimal

import pytest

from boatrace_edge.historical import parse_odds3t, parse_racelist, parse_resultlist


RACELIST_HTML = """
<html><body>
締切予定時刻 10:57 11:26 11:55 12:24 12:54 13:24 13:55 14:26 14:58 15:31 16:05 16:40
<table><tr><th>登録番号/級別</th><th>氏名</th></tr>
<tr><td>1</td><td>4200 / B1</td><td><a>早川 尚人</a></td></tr>
<tr><td>2</td><td>4339 / B1</td><td><a>平瀬 城啓</a></td></tr>
<tr><td>3</td><td>4197 / B1</td><td><a>渥美 卓郎</a></td></tr>
<tr><td>4</td><td>4641 / B1</td><td><a>磯村 匠</a></td></tr>
<tr><td>5</td><td>4060 / B1</td><td><a>島田 一生</a></td></tr>
<tr><td>6</td><td>4298 / A1</td><td><a>宮下 元胤</a></td></tr>
</table></body></html>
"""


ODDS_HTML = """
<html><body><table>
<tr>""" + "".join(f"<th>{i}</th>" for i in range(18)) + """</tr>
<tr>""" + "".join(f"<td>{x}</td>" for x in (
    2,3,"19.7", 1,3,"56.6", 1,2,"76.6", 1,2,"137.5", 1,2,"112.6", 1,2,"60.0"
)) + """</tr>
""" + "".join(
    "<tr>" + "".join(f"<td>{x}</td>" for x in values) + "</tr>"
    for values in [
        (4,"40.6",4,"69.8",4,"104.4",3,"167.4",3,"121.7",3,"126.1", 0,0,0,0,0,0),
    ]
) + "</table></body></html>"


RESULT_HTML = """
<html><body><table>
<tr><td>1R</td><td>1 -3 -6</td><td>¥2,880</td><td>1 -3</td><td>¥1,230</td><td>一般</td><td>逃げ</td><td></td></tr>
</table></body></html>
"""


def test_racelist_parses_six_entries_and_jst_deadline() -> None:
    deadline, entries = parse_racelist(RACELIST_HTML, "20260226", 1)
    assert deadline.isoformat() == "2026-02-26T10:57:00+09:00"
    assert len(entries) == 6
    assert entries[0].racer_id == "4200"
    assert entries[5].racer_name == "宮下 元胤"


def test_resultlist_never_infers_profit_from_result_only() -> None:
    result = parse_resultlist(RESULT_HTML, 1)
    assert result.combination_3t == "1-3-6"
    assert result.payout_3t == Decimal("2880")
    assert result.combination_2t == "1-3"
    assert result.payout_2t == Decimal("1230")


def test_odds_parser_rejects_incomplete_real_shape() -> None:
    with pytest.raises(ValueError, match="expected 120"):
        parse_odds3t(ODDS_HTML)
