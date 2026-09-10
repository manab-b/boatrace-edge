from decimal import Decimal

import pytest

from boatrace_edge.domain import Settlement, SettlementStatus


def settlement(status: SettlementStatus, payout: str) -> Settlement:
    return Settlement(
        race_id="202601010101",
        combination="1-2-3",
        stake=Decimal("100"),
        payout=Decimal(payout),
        status=status,
    )


def test_win_pnl_is_payout_minus_stake() -> None:
    assert settlement(SettlementStatus.WIN, "650").net_pnl == Decimal("550")


def test_loss_pnl_is_negative_stake() -> None:
    assert settlement(SettlementStatus.LOSS, "0").net_pnl == Decimal("-100")


def test_refund_is_not_profit() -> None:
    assert settlement(SettlementStatus.REFUND, "100").net_pnl == Decimal("0")


def test_void_is_not_profit() -> None:
    assert settlement(SettlementStatus.VOID, "100").net_pnl == Decimal("0")


def test_unknown_cannot_enter_finalized_pnl() -> None:
    with pytest.raises(ValueError, match="UNKNOWN"):
        settlement(SettlementStatus.UNKNOWN, "0").net_pnl
