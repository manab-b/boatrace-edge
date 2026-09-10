from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class SettlementStatus(StrEnum):
    WIN = "WIN"
    LOSS = "LOSS"
    REFUND = "REFUND"
    VOID = "VOID"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class OddsSnapshot:
    race_id: str
    combination: str
    odds: Decimal
    observed_at: datetime
    ingestion_at: datetime
    source: str


@dataclass(frozen=True)
class PredictionAudit:
    race_id: str
    generated_at: datetime
    feature_cutoff_at: datetime
    odds_cutoff_at: datetime
    model_version: str
    feature_version: str
    data_version: str


@dataclass(frozen=True)
class Settlement:
    race_id: str
    combination: str
    stake: Decimal
    payout: Decimal
    status: SettlementStatus

    @property
    def net_pnl(self) -> Decimal:
        if self.status in {SettlementStatus.REFUND, SettlementStatus.VOID}:
            return Decimal("0")
        if self.status is SettlementStatus.UNKNOWN:
            raise ValueError("UNKNOWN settlement cannot be included in finalized P/L")
        return self.payout - self.stake
