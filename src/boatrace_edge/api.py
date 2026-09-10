from fastapi import FastAPI

from .domain import SettlementStatus
from .integrity import validate_observation_cutoff

app = FastAPI(title="BOAT RACE EDGE", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/integrity/example")
def integrity_example() -> dict[str, str]:
    return {"refund_status": SettlementStatus.REFUND.value}
